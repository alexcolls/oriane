# Top-level statusReason
aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].statusReason" \
  --output text

# Compute resources statusReason
aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources.statusReason" \
  --output text

# Subnets
aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources.subnets[]" \
  --output text

# Route tables
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0e22e824327172265,subnet-049b5277041e9bc5d,subnet-0a7566c72481f41fa,subnet-0df646eacc0b79218 \
  --query "RouteTables[].Routes[]" \
  --output table
# or
for id in \
  subnet-0e22e824327172265 \
  subnet-049b5277041e9bc5d \
  subnet-0a7566c72481f41fa \
  subnet-0df646eacc0b79218; do
  echo "Routes for $id:"
  aws ec2 describe-route-tables \
    --filters Name=association.subnet-id,Values=$id \
    --query "RouteTables[].Routes[]" \
    --output table
done

# Identify subnets that are not public
for id in \
  subnet-0e22e824327172265 \
  subnet-049b5277041e9bc5d \
  subnet-0a7566c72481f41fa \
  subnet-0df646eacc0b79218; do
  echo
  echo "Subnet $id:"
  aws ec2 describe-route-tables \
    --filters Name=association.subnet-id,Values=$id \
    --query "RouteTables[0].{RT:RouteTableId,Routes:Routes}" \
    --output json

  aws ec2 describe-subnets \
    --subnet-ids $id \
    --query "Subnets[0].{MapPublicIpOnLaunch:MapPublicIpOnLaunch}" \
    --output table
done

# Describe route tables for subnets
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-0e22e824327172265,subnet-0df646eacc0b79218 \
  --query "RouteTables[].RouteTableId" \
  --output text

# Describe route tables for subnets 2
aws ec2 describe-route-tables \
  --route-table-ids rtb-0c49ffc57bc5b3f48 rtb-050b4aac4be84f72d \
  --query "RouteTables[].Routes[?DestinationCidrBlock=='0.0.0.0/0']"

# Describe compute environment
aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources.instanceRole" \
  --output text

# Describe compute environment status
aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].status"

# List container instances
aws ecs list-container-instances \
  --cluster ExtractionGPUComputeEnv

# List job queues
aws batch describe-job-queues \
  --query "jobQueues[?state=='ENABLED'].jobQueueName" \
  --output table

# List job definitions
aws batch describe-job-definitions \
  --status ACTIVE \
  --query "jobDefinitions[].{Name:jobDefinitionName,Revision:revision}" \
  --output table
