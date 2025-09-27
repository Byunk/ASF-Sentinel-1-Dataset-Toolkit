#!/bin/bash

# Process Seoul InSAR data for entire duration

# Reference ID
reference_id="S1A_IW_SLC__1SSV_20141213T093112_20141213T093140_003699_004641_E1DC-SLC"
project_name="seoul-insar"

uv run --env-file .env main.py "${reference_id}" --project-name "${project_name}" --no-download
