#!/usr/bin/env bash

INPUT_CSV="ML-ESG-2_English_Testset_formatted.csv"

# # -------- Positive / Negative ----------
# python3 gemini_posneg.py \
#     --input_csv "$INPUT_CSV" \
#     --out_dir   "test_results_gemini_posneg" \
#     --prompts   "prompts_posneg.json" \
#     --model     "gemini-2.5-flash-preview-04-17" \
#     --runs      10

# # -------- Risk / Opportunity -----------
# python3 gemini_opprisk.py \
#     --input_csv "$INPUT_CSV" \
#     --out_dir   "test_results_gemini_opprisk" \
#     --prompts   "prompts_opprisk.json" \
#     --model     "gemini-2.5-flash-preview-04-17" \
#     --runs      10

INPUT_CSV="ML-ESG-2_English_Train_formatted.csv"

# # -------- Positive / Negative ----------
python3 gemini_posneg.py \
    --input_csv "$INPUT_CSV" \
    --out_dir   "train_results_gemini_posneg" \
    --prompts   "prompts_posneg.json" \
    --model     "gemini-2.5-flash-preview-04-17" \
    --runs      10

# -------- Risk / Opportunity -----------
# python3 gemini_opprisk.py \
#     --input_csv "$INPUT_CSV" \
#     --out_dir   "train_results_gemini_opprisk" \
#     --prompts   "prompts_opprisk.json" \
#     --model     "gemini-2.5-flash-preview-04-17" \
#     --runs      10
