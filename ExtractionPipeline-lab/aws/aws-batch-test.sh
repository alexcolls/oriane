# Submit batch
aws batch submit-job \
  --job-name test-gpu \
  --job-queue ExtractionGPU_Queue \
  --job-definition ExtractionGPU_JobDef \
  --container-overrides 'command=["nvidia-smi"]'
