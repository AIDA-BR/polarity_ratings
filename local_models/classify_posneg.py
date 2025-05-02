#!/usr/bin/env python3
"""
Classifica manchetes como Positive / Negative usando LlamaIndex.

Uso:
  python classify_headlines_llamaindex_runs.py \
        --input_csv ML-ESG-2_English_Train_formatted.csv \
        --out_dir  results \
        --model    mistral-small3.1:24b \
        --prompts  prompts.json \
        --runs     10
"""

import argparse
import json
import gc
from pathlib import Path

import pandas as pd
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from llama_index.core import Settings

# ------------------------------------------------------------------ #
# utilidades
# ------------------------------------------------------------------ #
def detect_sentiment(text: str) -> str:
    lower = text.lower()
    if "positive" in lower:
        return "positive"
    if "negative" in lower:
        return "negative"
    return "undetermined"

def classify(text: str, prefix: str, llm) -> str:
    prompt = prefix + text
    try:
        messages = [
                ChatMessage(
                    role="system",
                    content="/no_think Respond exclusively with one of the specified labels. Do not include any explanations or additional text, only the label.",
                ),
                ChatMessage(role="user", content=prompt),
        ]
        resp = llm.chat(messages)
        return resp.message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"

# ------------------------------------------------------------------ #
# main
# ------------------------------------------------------------------ #
def main(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv)
    texts = df["text"].tolist()

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

    for run_id in range(1, args.runs + 1):
        print(f"\n===== RUN {run_id}/{args.runs} =====")
        for key, prefix in prompt_dict.items():
            print(f"--> Prompt: {key}")

            responses = [classify(t, prefix, llm) for t in texts]
            labels    = [detect_sentiment(r) for r in responses]

            out_df = pd.DataFrame(
                {
                    "text"          : df["text"],
                    "label"         : df["label"],
                    "response"      : responses,
                    "responseLabel" : labels,
                }
            )

            csv_name = (
                f"{Path(args.input_csv).stem}_{key}_run{run_id}.csv"
            )
            out_path = out_dir / csv_name
            out_df.to_csv(out_path, index=False)
            print(f"    ✔ salvo em {out_path}")

            gc.collect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sentiment classification via LlamaIndex"
    )
    parser.add_argument("--input_csv", required=True, help="caminho do CSV de entradas")
    parser.add_argument("--out_dir",   default="results", help="diretório de saída")
    parser.add_argument("--model",     default="mistral-small3.1:24b", help="nome do modelo Ollama")
    parser.add_argument("--prompts",   default="prompts_posneg.json", help="arquivo JSON com prompts")
    parser.add_argument("--runs",      type=int, default=10, help="quantas repetições")
    args = parser.parse_args()
    main(args)
