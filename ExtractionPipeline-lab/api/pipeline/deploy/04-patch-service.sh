#!/bin/bash


# Script to patch FastAPI service from LoadBalancer to ClusterIP
# This allows the Ingress to own the external traffic instead of the service

echo "Patching fastapi-service from LoadBalancer to ClusterIP..."

kubectl patch svc fastapi-service -n default -p '{"spec":{"type":"ClusterIP"}}'

if [ $? -eq 0 ]; then
    echo "Successfully patched fastapi-service to ClusterIP type"
else
    echo "Failed to patch fastapi-service"
    exit 1
fi
