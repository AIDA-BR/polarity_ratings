#!/usr/bin/env bash
#chmod +x run.sh
# Ajuste os três parâmetros abaixo e rode:  ./run_classification.sh

# 1) Qwen – Positive/Negative
OUT_DIR="train_results_qwen_posneg"
MODEL_NAME="qwen3:32b"
INPUT_CSV="ML-ESG-2_English_Train_formatted.csv"

python classify_posneg.py \
       --input_csv "$INPUT_CSV" \
       --out_dir   "$OUT_DIR" \
       --model     "$MODEL_NAME" \
       --runs      10


ollama stop "$MODEL_NAME"

# 2) Gemma – Positive/Negative
OUT_DIR="train_results_gemma_posneg"
MODEL_NAME="gemma3:27b"

python classify_posneg.py \
       --input_csv "$INPUT_CSV" \
       --out_dir   "$OUT_DIR" \
       --model     "$MODEL_NAME" \
       --runs      10

ollama stop "$MODEL_NAME"

# 3) Qwen – Opportunity/Risk
OUT_DIR="train_results_qwen_opprisk"
MODEL_NAME="qwen3:32b"

python classify_opprisk.py \
       --input_csv "$INPUT_CSV" \
       --out_dir   "$OUT_DIR" \
       --model     "$MODEL_NAME" \
       --runs      10

ollama stop "$MODEL_NAME"

# 4) Gemma – Opportunity/Risk
OUT_DIR="train_results_gemma_opprisk"
MODEL_NAME="gemma3:27b"

python classify_opprisk.py \
       --input_csv "$INPUT_CSV" \
       --out_dir   "$OUT_DIR" \
       --model     "$MODEL_NAME" \
       --runs      10

ollama stop "$MODEL_NAME"