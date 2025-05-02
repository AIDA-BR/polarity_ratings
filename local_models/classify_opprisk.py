#!/usr/bin/env python3
"""
Classifica manchetes como Risk / Opportunity usando LlamaIndex,
gera CSVs por prompt × run e calcula métricas (Accuracy, Precision,
Recall, F1 em micro/macro/weighted) – individualmente e em média.

Exemplo de execução (ver .sh):
python classify_headlines_llamaindex_runs.py \
       --input_csv ML-ESG-2_English_Train_formatted.csv \
       --out_dir  results \
       --model    mistral-small3.1:24b \
       --prompts  prompts_risk_opportunity.json \
       --runs     10
"""

import argparse, json, gc, datetime
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from llama_index.core import Settings

# ------------------------------------------------------------------ #
# utilidades
# ------------------------------------------------------------------ #
def detect_label(text: str) -> str:
    low = text.lower()
    if "risk" in low:
        return "Risk"
    if "opportunity" in low:
        return "Opportunity"
    return "undetermined"

def classify(headline: str, prefix: str, llm) -> str:
    prompt = prefix + headline
    try:
        
        messages = [
                ChatMessage(
                    role="system",
                    content="/no_think Respond exclusively with one of the specified labels, strictly based on the given context. Do not include any explanations or additional text—only the label.",
                ),
                ChatMessage(role="user", content=prompt),
        ]
        resp = llm.chat(messages)
        return resp.message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"

def compute_metrics(y_true, y_pred):
    """Retorna dicionário de métricas com 4 casas decimais."""
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=["Risk", "Opportunity"], average=None
    )  # não usado diretamente, mas garante label order
    prec_micro, rec_micro, f1_micro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="micro", zero_division=0
    )
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    prec_w, rec_w, f1_w, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return {
        "accuracy": acc,
        "precision_micro": prec_micro,
        "recall_micro": rec_micro,
        "f1_micro": f1_micro,
        "precision_macro": prec_macro,
        "recall_macro": rec_macro,
        "f1_macro": f1_macro,
        "precision_weighted": prec_w,
        "recall_weighted": rec_w,
        "f1_weighted": f1_w,
    }

def fmt(val):  # 4 dígitos
    return f"{val:.4f}"

# ------------------------------------------------------------------ #
# main
# ------------------------------------------------------------------ #
def main(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv)
    gold = df["label"].tolist()  # espera etiquetas Risk / Opportunity

    # configurar LLM
    llm = Ollama(
        model=args.model,
        request_timeout=120.0,
        temperature=0,
        additional_kwargs={"top_p": 0.95, "num_predict": 20},
    )
    Settings.llm = llm

    # carregar prompts
    with open(args.prompts, encoding="utf-8") as f:
        prompt_dict = json.load(f)["prompts"]

    # armazenar métricas de cada run para média
    run_metrics_all = []

    for run_id in range(1, args.runs + 1):
        print(f"\n===== RUN {run_id}/{args.runs} =====")
        for key, prefix in prompt_dict.items():
            print(f"--> Prompt: {key}")

            responses = [classify(h, prefix, llm) for h in df["text"]]
            preds     = [detect_label(r)             for r in responses]

            # salvar CSV
            csv_name = f"{Path(args.input_csv).stem}_{key}_run{run_id}.csv"
            out_df = pd.DataFrame(
                {
                    "text": df["text"],
                    "label": gold,
                    "response": responses,
                    "responseLabel": preds,
                }
            )
            out_df.to_csv(out_dir / csv_name, index=False)

            # métricas
            metrics = compute_metrics(gold, preds)
            metrics["run"]    = run_id
            metrics["prompt"] = key
            run_metrics_all.append(metrics)
            gc.collect()

    # ----------------------- salvar métricas ------------------------
    # média por prompt (sobre as runs)
    summary = {}
    for m in run_metrics_all:
        p = m["prompt"]
        summary.setdefault(p, []).append(m)

    lines = []
    for prompt_key, results in summary.items():
        # média
        mean_vals = {
            k: sum(r[k] for r in results) / len(results)
            for k in results[0] if k not in ("run", "prompt")
        }
        # registro por run
        for r in results:
            run_line = ", ".join(f"{k}={fmt(v)}" for k, v in r.items() if k not in ("prompt"))
            lines.append(f"{prompt_key}, {run_line}")
        # registro média
        mean_line = ", ".join(f"{k}_mean={fmt(v)}" for k, v in mean_vals.items())
        lines.append(f"{prompt_key}, {mean_line}\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    metrics_path = out_dir / f"metrics_{args.model.replace(':','-')}_{ts}.txt"
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✔ Métricas salvas em {metrics_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Risk/Opportunity classification via LlamaIndex")
    p.add_argument("--input_csv", required=True, help="CSV de entrada")
    p.add_argument("--out_dir", default="results", help="diretório para CSVs e métricas")
    p.add_argument("--model", default="mistral-small3.1:24b", help="modelo Ollama")
    p.add_argument("--prompts", default="prompts_opprisk.json", help="JSON de prompts")
    p.add_argument("--runs", type=int, default=10, help="quantas repetições")
    main(p.parse_args())
