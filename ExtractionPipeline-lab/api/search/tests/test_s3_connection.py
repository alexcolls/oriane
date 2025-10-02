#!/usr/bin/env python3
"""
Quick test script to verify S3 connection and credentials
"""

import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")


def test_s3_connection():
    """Test S3 connection and bucket access"""

    # Get credentials from environment
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")
    bucket_name = os.getenv("S3_APP_BUCKET", "oriane-app")

    print(f"Testing S3 connection...")
    print(f"Region: {region}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key: {access_key[:10]}..." if access_key else "Access Key: Not set")
    print(f"Secret Key: {'*' * 20}" if secret_key else "Secret Key: Not set")

    if not access_key or not secret_key:
        print("❌ ERROR: AWS credentials not set in .env file")
        return False

    try:
        # Create S3 client
        s3_client = boto3.client(
            "s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region
        )

        # Test bucket access
        print(f"\n🔍 Testing bucket access...")
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Successfully connected to bucket: {bucket_name}")

        # Test upload permissions with a tiny test file
        print(f"\n🔍 Testing upload permissions...")
        test_key = "test/connection_test.txt"
        test_content = b"S3 connection test"

        s3_client.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)
        print(f"✅ Successfully uploaded test file: {test_key}")

        # Clean up test file
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ Successfully deleted test file")

        print(f"\n🎉 S3 configuration is working correctly!")
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        print(f"\n❌ AWS Error ({error_code}): {error_message}")

        if error_code == "NoSuchBucket":
            print(f"💡 Bucket '{bucket_name}' does not exist. Please create it or check the name.")
        elif error_code == "AccessDenied":
            print(f"💡 Access denied. Check your AWS credentials and bucket permissions.")
        elif error_code == "InvalidAccessKeyId":
            print(f"💡 Invalid access key ID. Check your AWS_ACCESS_KEY_ID in .env")
        elif error_code == "SignatureDoesNotMatch":
            print(f"💡 Invalid secret key. Check your AWS_SECRET_ACCESS_KEY in .env")

        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    test_s3_connection()
