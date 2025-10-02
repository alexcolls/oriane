# Fix: Support Amazon Linux 2023 GPU AMIs for EKS 1.33

## Summary
This pull request adds support for Amazon Linux 2023 GPU AMIs for EKS version 1.33, addressing compatibility issues with GPU node groups and ensuring proper AMI selection for modern workloads.

## Changes Made
- Updated AMI family configuration to support `AmazonLinux2023` in `.env.sample`
- Enhanced `create_node_groups.sh` to handle Amazon Linux 2023 GPU AMIs
- Added fallback logic to gracefully handle AMI selection when AL2023 is not available
- Updated deployment scripts to properly configure GPU node groups with AL2023 AMIs
- Added AMI update script (`scripts/update_eks_ami.sh`) for automated AMI management

## Fallback Path
The implementation includes a robust fallback mechanism:
1. **Primary**: Attempts to use Amazon Linux 2023 GPU AMIs for optimal performance
2. **Fallback**: If AL2023 GPU AMIs are not available in the region, automatically falls back to Amazon Linux 2 GPU AMIs
3. **Error Handling**: Provides clear error messages and logs when AMI selection fails

## Technical Details
- **EKS Version**: 1.33 (default)
- **AMI Family**: AmazonLinux2023 (with AL2 fallback)
- **GPU Instance Types**: g5.xlarge, g5.2xlarge, g4dn.xlarge, g4dn.2xlarge
- **Node Group Configuration**: Enhanced with proper AMI selection logic

## AWS Documentation Reference
According to AWS documentation, Amazon Linux 2023 is now supported for EKS GPU workloads:
- [Amazon EKS optimized Amazon Linux AMIs](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html)
- [Amazon Linux 2023 support for EKS](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-linux.html)

## Testing
- ✅ Verified AMI selection logic with both AL2023 and AL2 fallback scenarios
- ✅ Tested GPU node group creation with new AMI configuration
- ✅ Validated deployment scripts with updated AMI family settings
- ✅ Confirmed backward compatibility with existing AL2 setups

## Benefits
1. **Performance**: Amazon Linux 2023 provides better performance and security features
2. **Future-proofing**: Aligns with AWS's recommended AMI family for new deployments
3. **Compatibility**: Maintains backward compatibility with existing AL2 deployments
4. **Reliability**: Robust fallback mechanism ensures deployments don't fail due to AMI availability

## Files Modified
- `.env.sample` - Updated AMI family configuration
- `deploy/create_node_groups.sh` - Enhanced AMI selection logic
- `deploy/deploy_solution.sh` - Updated deployment configuration
- `deploy/deploy_to_eks.sh` - Enhanced EKS deployment process
- `scripts/update_eks_ami.sh` - New AMI management script
- Various deployment and configuration files

## Breaking Changes
None. This change is backward compatible and includes appropriate fallback mechanisms.

## Rollback Plan
If issues arise, the fallback to Amazon Linux 2 AMIs is automatic. Additionally, the previous AMI family can be restored by updating the `AMI_FAMILY` variable in the environment configuration.
