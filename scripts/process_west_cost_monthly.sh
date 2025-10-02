#!/bin/bash

set -e

PROJECT_NAME=${PROJECT_NAME:-west-coast-monthly}
OUTPUT_DIR=${OUTPUT_DIR:-data/west-coast-monthly}
DRY_RUN=${DRY_RUN:-false}

# 3 months
# if [ "${DRY_RUN}" = "false" ]; then
#   uv run main.py process insar-burst \
#     input.txt \
#     --project-name ${PROJECT_NAME} \
#     --output-dir ${OUTPUT_DIR} \
#     --water-mask \
#     --min-temporal-baseline 80 \
#     --max-temporal-baseline 100
# else
#   uv run main.py process insar-burst \
#     input.txt \
#     --project-name ${PROJECT_NAME} \
#     --output-dir ${OUTPUT_DIR} \
#     --water-mask \
#     --min-temporal-baseline 80 \
#     --max-temporal-baseline 100 \
#     --dry-run
# fi

# 6 months
if [ "${DRY_RUN}" = "false" ]; then
  uv run main.py process insar-burst \
    input.txt \
    --project-name ${PROJECT_NAME} \
    --output-dir ${OUTPUT_DIR} \
    --water-mask \
    --min-temporal-baseline 160 \
    --max-temporal-baseline 200 \
    --no-wait
else
  uv run main.py process insar-burst \
    input.txt \
    --project-name ${PROJECT_NAME} \
    --output-dir ${OUTPUT_DIR} \
    --water-mask \
    --min-temporal-baseline 160 \
    --max-temporal-baseline 200 \
    --dry-run \
    --no-wait
fi

# 12 months
if [ "${DRY_RUN}" = "false" ]; then
  uv run main.py process insar-burst \
    input.txt \
    --project-name ${PROJECT_NAME} \
    --output-dir ${OUTPUT_DIR} \
    --water-mask \
    --min-temporal-baseline 330 \
    --max-temporal-baseline 400 \
    --no-wait
else
  uv run main.py process insar-burst \
    input.txt \
    --project-name ${PROJECT_NAME} \
    --output-dir ${OUTPUT_DIR} \
    --water-mask \
    --min-temporal-baseline 330 \
    --max-temporal-baseline 400 \
    --dry-run \
    --no-wait
fi
