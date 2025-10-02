#!/bin/bash

# WARNING: Make sure to have the ./keys/OrianeSearchAPIv1_dev.pem file.
# Email alex@oriane.xyz for authorization if missing.
ssh -i keys/OrianeSearchAPIv1_dev.pem ubuntu@ec2-3-239-35-32.compute-1.amazonaws.com
