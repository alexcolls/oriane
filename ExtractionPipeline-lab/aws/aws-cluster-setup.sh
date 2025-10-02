aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources.ecsClusterArn" \
  --output text

aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].ecsClusterArn" \
  --output text

aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].ecsClusterArn" \
  --output text

aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources.launchTemplate" \
  --output json

aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --output json

CLUSTER_ARN=$(aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].ecsClusterArn" \
  --output text)

# Extract the name after the last slash
CLUSTER_NAME=${CLUSTER_ARN##*/}
echo "Cluster: $CLUSTER_NAME"
