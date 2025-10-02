aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources" \
  --output json > cr.json

aws batch update-compute-environment \
  --compute-environment ExtractionGPUComputeEnv \
  --compute-resources file://cr.json

aws batch submit-job \
  --job-name nv-check \
  --job-queue ExtractionGPU_Queue \
  --job-definition ExtractionGPU_JobDef \
  --container-overrides '{"command":["nvidia-smi"]}'
