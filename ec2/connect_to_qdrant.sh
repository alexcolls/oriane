#!/bin/bash

# WARNING: Make sure to have the ./keys/OrianeSearchAPIv1_dev.pem file.
# Email alex@oriane.xyz for authorization if missing.
ssh -i keys/qdrant-dev-key.pem ubuntu@ec2-44-222-164-61.compute-1.amazonaws.com
