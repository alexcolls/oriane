#!/bin/bash

# Audit script for boto3 profile-based initialization patterns
# This script searches for problematic patterns that need to be patched

echo "=== BOTO3 PROFILE AUDIT REPORT ==="
echo "Generated on: $(date)"
echo "Repository: $(pwd)"
echo

echo "Searching for boto3 profile-based initialization patterns..."
echo

# Pattern 1: boto3.Session( calls (especially with profile_name=)
echo "1. Searching for boto3.Session( calls:"
grep -rn "boto3\.Session(" . --include="*.py" || echo "   No boto3.Session( calls found"
echo

# Pattern 2: profile_name keyword in any boto3 call
echo "2. Searching for profile_name keyword:"
grep -rn "profile_name" . --include="*.py" || echo "   No profile_name usage found"
echo

# Pattern 3: Direct reads of AWS_PROFILE env-var
echo "3. Searching for AWS_PROFILE environment variable usage:"
grep -rn "AWS_PROFILE" . --include="*.py" || echo "   No AWS_PROFILE usage found"
echo

# Additional patterns that might be relevant
echo "4. Additional boto3 profile-related patterns:"
echo "   a. Searching for 'aws_profile':"
grep -rn "aws_profile" . --include="*.py" || echo "      No aws_profile usage found"
echo
echo "   b. Searching for Session initialization with profile:"
grep -rn "Session.*profile" . --include="*.py" || echo "      No Session with profile found"
echo

echo "=== AUDIT COMPLETE ==="
echo "Review the results above to identify files and lines that need patching."
