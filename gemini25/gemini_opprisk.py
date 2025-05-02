#!/usr/bin/env python3
"""
Classifica manchetes com Gemini 2 em lotes (batches) e concorrência.
Gera CSVs por prompt × run e calcula métricas (accuracy, precision,
recall, F1 – micro/macro/weighted).

Exemplo de execução:
  python gemini_opprisk.py \
         --input_csv  ML-ESG-2_English_Testset_formatted.csv \
         --out_dir    results \
         --prompts    prompts_opprisk.json \
         --model      gemini-2.0-pro-001 \
         --runs       10 \
         --batch_size 20 \
         --max_workers 10 \
         --sleep      2
"""
import os, json, time, argparse, datetime, concurrent.futures
from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -------------------- 1 · CONSTANTES --------------------
LABEL_A = "Risk"
LABEL_B = "Opportunity"

# -------------------- 2 · CLIENTE GEMINI ----------------
load_dotenv()
client = genai.Client(
    vertexai=True,
    project="aida-risk",
    location="global",
)

# -------------------- 3 · PARÂMS FIXOS DA API ----------
MAX_OUTPUT_TOKENS = 20
TEMPERATURE       = 0

SYSTEM_INSTRUCTION = (
    "Respond exclusively with one of the specified labels, strictly based on "
    "the given context. Do not include any explanations or additional text—"
    "only the label."
)

def build_config():
    """Retorna um objeto GenerateContentConfig pronto para uso."""
    return types.GenerateContentConfig(
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        top_p=0.95,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",       threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",        threshold="OFF"),
        ],
        system_instruction=[types.Part.from_text(text=SYSTEM_INSTRUCTION)],
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

# --------------------------------------------------------
# 4 · FUNÇÕES AUXILIARES
# --------------------------------------------------------
def _fetch_prediction(args_tuple):
    """
    Função executada em thread.
    Recebe tupla (prompt_full, model, sleep_time).
    Retorna rótulo detectado ou 'undetermined'.
    """
    prompt_full, model, sleep_time = args_tuple
    time.sleep(sleep_time)               

    try:
        contents = [types.Content(role="user",
                                  parts=[types.Part.from_text(text=prompt_full)])]
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=build_config(),
        )
        raw_text = response.text.strip()
    except Exception as e:
        raw_text = f"Error: {e}"

    return detect_label(raw_text), raw_text  # (label_detectada, texto_bruto)

def detect_label(text: str) -> str:
    low = text.lower()
    if LABEL_A.lower() in low:
        return LABEL_A
    if LABEL_B.lower() in low:
        return LABEL_B
    return "undetermined"

def compute_metrics(y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    prec_micro, rec_micro, f1_micro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="micro", zero_division=0
    )
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    prec_w, rec_w, f1_w, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return dict(
        accuracy=acc,
        precision_micro=prec_micro, recall_micro=rec_micro, f1_micro=f1_micro,
        precision_macro=prec_macro, recall_macro=rec_macro, f1_macro=f1_macro,
        precision_weighted=prec_w, recall_weighted=rec_w, f1_weighted=f1_w
    )

def fmt4(x): return f"{x:.4f}"

# --------------------------------------------------------
# 5 · PROCESSAMENTO EM BATCHES
# --------------------------------------------------------
def batched_predictions(text_series, prefix, model,
                        batch_size, sleep_time, max_workers):
    """
    Recebe uma Series de textos e devolve duas listas:
        labels_pred, raw_responses
    Processa em lotes + concorrência.
    """
    labels_pred, raw_responses = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for start in range(0, len(text_series), batch_size):
            end = min(start + batch_size, len(text_series))
            batch_texts = text_series.iloc[start:end]
            # Empacotar args p/ cada item
            args_iter = [
                (prefix + txt, model, sleep_time)
                for txt in batch_texts
            ]
            for label, raw in executor.map(_fetch_prediction, args_iter):
                labels_pred.append(label)
                raw_responses.append(raw)
    return labels_pred, raw_responses

# --------------------------------------------------------
# 6 · MAIN
# --------------------------------------------------------
def main(args):
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    df   = pd.read_csv(args.input_csv)
    gold = df["label"].tolist()

    prompt_dict = json.loads(Path(args.prompts).read_text(encoding="utf-8"))["prompts"]
    run_metrics = []

    for run_id in range(1, args.runs + 1):
        print(f"\n=== RUN {run_id}/{args.runs} ===")
        for key, prefix in prompt_dict.items():
            print(f"--> {key}")
            preds, responses = batched_predictions(
                df["text"], prefix, args.model,
                batch_size=args.batch_size,
                sleep_time=args.sleep,
                max_workers=args.max_workers,
            )

            # -------- salvar CSV ----------
            csv_name = f"{Path(args.input_csv).stem}_{key}_run{run_id}.csv"
            pd.DataFrame(
                {
                    "text":          df["text"],
                    "label":         gold,
                    "response":      responses,
                    "responseLabel": preds,
                }
            ).to_csv(out_dir / csv_name, index=False)

            # -------- métricas ------------
            m = compute_metrics(gold, preds)
            m["prompt"] = key
            m["run"]    = run_id
            run_metrics.append(m)

    # ---------------- salvar TXT de métricas -------------------------
    txt_lines = []
    for prompt in prompt_dict.keys():
        sub = [x for x in run_metrics if x["prompt"] == prompt]
        for r in sub:
            ln = ", ".join(f"{k}={fmt4(v)}" for k, v in r.items() if k not in ("prompt"))
            txt_lines.append(f"{prompt}, {ln}")
        mean = {k: sum(r[k] for r in sub)/len(sub) for k in sub[0] if k not in ("prompt","run")}
        ln_m = ", ".join(f"{k}_mean={fmt4(v)}" for k, v in mean.items())
        txt_lines.append(f"{prompt}, {ln_m}\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    (out_dir / f"metrics_{args.model}_{ts}.txt").write_text("\n".join(txt_lines))

    print("\n✔  CSVs e métricas salvos em", out_dir)

# --------------------------------------------------------
# 7 · ARGUMENTOS CLI
# --------------------------------------------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input_csv",  required=True)
    p.add_argument("--out_dir",   default="results")
    p.add_argument("--prompts",   required=True)
    p.add_argument("--model",     default="gemini-2.0-pro-001")
    p.add_argument("--runs",      type=int, default=10)
    
    p.add_argument("--batch_size", type=int, default=10,
                   help="tamanho de cada lote enviado ao Gemini")
    p.add_argument("--sleep",      type=float, default=2,
                   help="segundos de espera ANTES de cada chamada (por thread)")
    p.add_argument("--max_workers", type=int, default=10,
                   help="threads simultâneas para chamadas Gemini")
    main(p.parse_args())
