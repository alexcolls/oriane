aws ec2 modify-subnet-attribute \
  --subnet-id subnet-049b5277041e9bc5d \
  --map-public-ip-on-launch

aws ec2 modify-subnet-attribute \
  --subnet-id subnet-0a7566c72481f41fa \
  --map-public-ip-on-launch

aws ec2 allocate-address --domain vpc \
  --query "AllocationId" --output text

aws ec2 create-nat-gateway \
  --subnet-id subnet-049b5277041e9bc5d \
  --allocation-id eipalloc-0a40a9115eb0da3fd \
  --query "NatGateway.NatGatewayId" --output text

aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-08dd0fdfaac847269 \
  --query "NatGateways[0].State" \
  --output text

for rtb in rtb-0c49ffc57bc5b3f48 rtb-050b4aac4be84f72d; do
  aws ec2 create-route \
    --route-table-id $rtb \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id nat-08dd0fdfaac847269
done

aws ec2 describe-route-tables \
  --route-table-ids rtb-0c49ffc57bc5b3f48 rtb-050b4aac4be84f72d \
  --query "RouteTables[].Routes[?DestinationCidrBlock=='0.0.0.0/0']"

aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].computeResources.instanceRole" \
  --output text

aws batch describe-compute-environments \
  --compute-environments ExtractionGPUComputeEnv \
  --query "computeEnvironments[0].status"
