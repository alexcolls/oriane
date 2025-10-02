#!/bin/bash

aws batch submit-job \
  --job-name extraction-run \
  --job-queue ExtractionGPU_Queue \
  --job-definition ExtractionGPU_JobDef \
  --container-overrides 'command=["python","-u","entrypoint.py"]'
