#!/usr/bin/env python3
"""
Classifica manchetes com Gemini (Vertex AI) em lotes e
salva apenas os CSVs

Exemplo:
  python gemini_posneg.py \
         --input_csv  ML-ESG-2_English_Testset_formatted.csv \
         --out_dir    results \
         --prompts    prompts_risk_opportunity.json \
         --model      gemini-2.0-pro-001 \
         --runs       10 \
         --batch_size 20 \
         --sleep      2 \
         --max_workers 8
"""
import os, json, time, argparse, concurrent.futures
from pathlib import Path
import pandas as pd
from google import genai
from google.genai import types

# -------------------- 1 · CONSTS --------------------
LABEL_A = "Positive"
LABEL_B = "Negative"

SLEEP_DEFAULT   = 2
MAX_TOKENS      = 20
TEMPERATURE     = 0

SYSTEM_INSTRUCTION = (
    "Respond exclusively with one of the specified labels, strictly based on "
    "the given context. Do not include any explanations or additional text—"
    "only the label."
)

# -------------------- 2 · CLIENTE GEMINI ------------
client = genai.Client(
    vertexai=True,
    project="aida-risk",
    location="global",
)

def build_cfg():
    return types.GenerateContentConfig(
        temperature=TEMPERATURE,
        max_output_tokens=MAX_TOKENS,
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

# -------------------- 3 · FUNÇÕES --------------------
def _fetch(args_tuple):
    """Função que roda em thread: (prompt_full, model, sleep)."""
    prompt_full, model, sleep_time = args_tuple
    time.sleep(sleep_time)
    try:
        contents = [types.Content(role="user",
                                  parts=[types.Part.from_text(text=prompt_full)])]
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=build_cfg(),
        )
        return resp.text.strip()
    except Exception as e:
        return f"Error: {e}"

def detect_label(text: str) -> str:
    low = text.lower()
    if LABEL_A.lower() in low:
        return LABEL_A
    if LABEL_B.lower() in low:
        return LABEL_B
    return "undetermined"

def get_predictions(series_texts, prefix, model,
                    batch_size, sleep_time, max_workers):
    """Retorna duas listas: raw_responses, predicted_labels."""
    raw_responses, labels = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for start in range(0, len(series_texts), batch_size):
            end = min(start + batch_size, len(series_texts))
            args_iter = [
                (prefix + txt, model, sleep_time)
                for txt in series_texts.iloc[start:end]
            ]
            for raw in ex.map(_fetch, args_iter):
                raw_responses.append(raw)
                labels.append(detect_label(raw))
    return raw_responses, labels

# -------------------- 4 · MAIN -----------------------
def main(args):
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    df   = pd.read_csv(args.input_csv)
    gold = df["label"].tolist()

    prompt_dict = json.loads(Path(args.prompts).read_text(encoding="utf-8"))["prompts"]

    for run in range(1, args.runs + 1):
        print(f"\n=== RUN {run}/{args.runs} ===")
        for key, prefix in prompt_dict.items():
            print(f"--> {key}")
            responses, preds = get_predictions(
                df["text"],
                prefix,
                args.model,
                batch_size=args.batch_size,
                sleep_time=args.sleep,
                max_workers=args.max_workers,
            )

            csv_name = f"{Path(args.input_csv).stem}_{key}_run{run}.csv"
            pd.DataFrame(
                {"text": df["text"], "label": gold,
                 "response": responses, "responseLabel": preds}
            ).to_csv(out_dir / csv_name, index=False)

    print("\n✔  CSVs salvos em", out_dir)

# -------------------- 5 · CLI ------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_csv", required=True, help="CSV com colunas text e label")
    ap.add_argument("--out_dir",   default="results")
    ap.add_argument("--prompts",   required=True)
    ap.add_argument("--model",     default="gemini-2.0-pro-001")
    ap.add_argument("--runs",      type=int, default=10)

    ap.add_argument("--batch_size",  type=int, default=10)
    ap.add_argument("--sleep",       type=float, default=SLEEP_DEFAULT)
    ap.add_argument("--max_workers", type=int, default=8)
    main(ap.parse_args())
