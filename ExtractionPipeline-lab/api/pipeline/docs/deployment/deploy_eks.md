# EKS Deployment Guide

This guide provides comprehensive instructions for deploying the Oriane Extraction Pipeline API on Amazon Elastic Kubernetes Service (EKS) with GPU support.

## Table of Contents

- [Prerequisites](#prerequisites)
- [EKS Cluster Setup](#eks-cluster-setup)
- [GPU Node Groups](#gpu-node-groups)
- [IAM Roles and Policies](#iam-roles-and-policies)
- [Load Balancer Configuration](#load-balancer-configuration)
- [Deployment Steps](#deployment-steps)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

### Required Tools

Install the following tools on your deployment machine:

```bash
# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### AWS Account Requirements

- AWS CLI configured with appropriate permissions
- VPC with public and private subnets
- Sufficient EC2 instance limits for GPU instances
- Route 53 hosted zone (optional, for custom domains)

### AWS Permissions

Your AWS user/role needs the following permissions:
- `AmazonEKSClusterPolicy`
- `AmazonEKSWorkerNodePolicy`
- `AmazonEKS_CNI_Policy`
- `AmazonEC2ContainerRegistryReadOnly`
- `AmazonS3FullAccess` (for pipeline storage)
- `AmazonRoute53FullAccess` (for DNS)

## EKS Cluster Setup

### 1. Create EKS Cluster

Create a cluster configuration file:

```yaml
# cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: oriane-pipeline-cluster
  region: us-east-1
  version: "1.28"

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: Single
  clusterEndpoints:
    publicAccess: true
    privateAccess: true

cloudWatch:
  clusterLogging:
    enableTypes: ["*"]

addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest
  - name: aws-ebs-csi-driver
    version: latest

managedNodeGroups:
  - name: system-nodes
    instanceType: t3.medium
    minSize: 2
    maxSize: 4
    desiredCapacity: 2
    volumeSize: 50
    ssh:
      enableSsm: true
    labels:
      node-type: system
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/oriane-pipeline-cluster: "owned"

iam:
  withOIDC: true
  serviceAccounts:
    - metadata:
        name: aws-load-balancer-controller
        namespace: kube-system
      wellKnownPolicies:
        awsLoadBalancerController: true
    - metadata:
        name: cluster-autoscaler
        namespace: kube-system
      wellKnownPolicies:
        autoScaling: true
```

Deploy the cluster:

```bash
eksctl create cluster -f cluster-config.yaml
```

### 2. Update kubeconfig

```bash
aws eks update-kubeconfig --region us-east-1 --name oriane-pipeline-cluster
```

### 3. Verify Cluster

```bash
kubectl get nodes
kubectl get pods -n kube-system
```

## GPU Node Groups

### 1. Create GPU Node Group Configuration

```yaml
# gpu-nodegroup.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: oriane-pipeline-cluster
  region: us-east-1

managedNodeGroups:
  - name: gpu-nodes-p3
    instanceTypes: ["p3.2xlarge", "p3.8xlarge"]
    minSize: 0
    maxSize: 10
    desiredCapacity: 2
    volumeSize: 100
    volumeType: gp3
    ssh:
      enableSsm: true
    labels:
      node-type: gpu
      gpu-type: tesla-v100
      accelerator: nvidia-tesla-v100
    taints:
      - key: nvidia.com/gpu
        value: "true"
        effect: NoSchedule
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/oriane-pipeline-cluster: "owned"
      k8s.io/cluster-autoscaler/node-template/taint/nvidia.com/gpu: "true:NoSchedule"

  - name: gpu-nodes-g4dn
    instanceTypes: ["g4dn.xlarge", "g4dn.2xlarge", "g4dn.4xlarge"]
    minSize: 0
    maxSize: 5
    desiredCapacity: 1
    volumeSize: 100
    volumeType: gp3
    ssh:
      enableSsm: true
    labels:
      node-type: gpu
      gpu-type: tesla-t4
      accelerator: nvidia-tesla-t4
    taints:
      - key: nvidia.com/gpu
        value: "true"
        effect: NoSchedule
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/oriane-pipeline-cluster: "owned"
      k8s.io/cluster-autoscaler/node-template/taint/nvidia.com/gpu: "true:NoSchedule"
```

Create the GPU node groups:

```bash
eksctl create nodegroup -f gpu-nodegroup.yaml
```

### 2. Install NVIDIA Device Plugin

```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

### 3. Verify GPU Nodes

```bash
kubectl get nodes --show-labels | grep gpu
kubectl describe nodes -l accelerator=nvidia-tesla-v100
```

## IAM Roles and Policies

### 1. Create Service Account IAM Role

```yaml
# service-account-policy.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pipeline-api-sa
  namespace: pipeline
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/PipelineApiRole
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pipeline-api-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["pods", "nodes"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: pipeline-api-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: pipeline-api-role
subjects:
- kind: ServiceAccount
  name: pipeline-api-sa
  namespace: pipeline
```

### 2. Create IAM Policy for Pipeline

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::oriane-frames/*",
        "arn:aws:s3:::oriane-frames",
        "arn:aws:s3:::oriane-contents/*",
        "arn:aws:s3:::oriane-contents"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:oriane/pipeline/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 3. Create IAM Role with Trust Policy

```bash
# Create IAM role
aws iam create-role --role-name PipelineApiRole --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/OIDC_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/OIDC_ID:sub": "system:serviceaccount:pipeline:pipeline-api-sa",
          "oidc.eks.us-east-1.amazonaws.com/id/OIDC_ID:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}'

# Attach policy
aws iam attach-role-policy --role-name PipelineApiRole --policy-arn arn:aws:iam::ACCOUNT_ID:policy/PipelineApiPolicy
```

## Load Balancer Configuration

### 1. Install AWS Load Balancer Controller

```bash
# Install cert-manager
kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v1.5.4/cert-manager.yaml

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=oriane-pipeline-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 2. Create Application Load Balancer

```yaml
# alb-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pipeline-api-ingress
  namespace: pipeline
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERT_ID
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '5'
spec:
  rules:
  - host: pipeline-api.oriane.xyz
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pipeline-api-service
            port:
              number: 80
```

### 3. Network Load Balancer (Alternative)

```yaml
# nlb-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: pipeline-api-nlb
  namespace: pipeline
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
spec:
  type: LoadBalancer
  selector:
    app: pipeline-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  - name: https
    port: 443
    targetPort: 8000
    protocol: TCP
```

## Deployment Steps

### 1. Create Namespace

```bash
kubectl create namespace pipeline
```

### 2. Create Secrets

```bash
# API credentials
kubectl create secret generic pipeline-api-secrets \
  --namespace=pipeline \
  --from-literal=API_KEY=your-api-key-here \
  --from-literal=API_USERNAME=admin \
  --from-literal=API_PASSWORD=your-password-here \
  --from-literal=AWS_ACCESS_KEY_ID=your-aws-access-key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your-aws-secret-key \
  --from-literal=QDRANT_KEY=your-qdrant-key \
  --from-literal=QDRANT_URL=https://your-qdrant-endpoint:6333

# Docker registry credentials (if using private registry)
kubectl create secret docker-registry registry-secret \
  --namespace=pipeline \
  --docker-server=your-registry-url \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email
```

### 3. Apply ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Create Persistent Volume

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-shared-pvc
  namespace: pipeline
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi
```

```bash
kubectl apply -f pvc.yaml
```

### 5. Deploy Application

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f alb-ingress.yaml
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods -n pipeline

# Check services
kubectl get svc -n pipeline

# Check ingress
kubectl get ingress -n pipeline

# Check logs
kubectl logs -n pipeline deployment/pipeline-api
```

## Monitoring and Logging

### 1. Install Prometheus and Grafana

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=your-grafana-password

# Install Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

### 2. Configure CloudWatch Logging

```yaml
# cloudwatch-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-info
  namespace: amazon-cloudwatch
data:
  cluster.name: oriane-pipeline-cluster
  logs.region: us-east-1
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: cwagentconfig
  namespace: amazon-cloudwatch
data:
  cwagentconfig.json: |
    {
      "logs": {
        "metrics_collected": {
          "kubernetes": {
            "cluster_name": "oriane-pipeline-cluster",
            "metrics_collection_interval": 60
          }
        },
        "force_flush_interval": 15
      }
    }
```

### 3. Install Fluent Bit

```bash
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit \
  --namespace amazon-cloudwatch \
  --create-namespace \
  --set cloudWatch.enabled=true \
  --set cloudWatch.region=us-east-1
```

## Troubleshooting

### Common Issues

#### 1. GPU Nodes Not Ready
```bash
# Check node status
kubectl describe nodes -l accelerator=nvidia-tesla-v100

# Check NVIDIA device plugin
kubectl get daemonset -n kube-system nvidia-device-plugin-daemonset

# Restart device plugin
kubectl delete pods -n kube-system -l name=nvidia-device-plugin-ds
```

#### 2. Pod Stuck in Pending
```bash
# Check pod events
kubectl describe pod -n pipeline pod-name

# Check node taints and tolerations
kubectl get nodes -o json | jq '.items[].spec.taints'

# Check resource requests
kubectl top nodes
```

#### 3. Load Balancer Issues
```bash
# Check ingress status
kubectl describe ingress -n pipeline pipeline-api-ingress

# Check AWS Load Balancer Controller
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check target group health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...
```

#### 4. GPU Memory Issues
```bash
# Check GPU usage
kubectl exec -n pipeline deployment/pipeline-api -- nvidia-smi

# Check pod resource limits
kubectl describe pod -n pipeline pod-name | grep -A5 -B5 resources

# Scale down parallel jobs
kubectl patch configmap -n pipeline pipeline-api-config -p '{"data":{"PIPELINE_MAX_PARALLEL_JOBS":"1"}}'
```

### Debug Commands

```bash
# Check cluster status
kubectl cluster-info

# Check all resources in namespace
kubectl get all -n pipeline

# Check events
kubectl get events -n pipeline --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top nodes
kubectl top pods -n pipeline

# Check logs
kubectl logs -n pipeline deployment/pipeline-api --tail=100 -f
```

## Maintenance

### 1. Update Cluster

```bash
# Update cluster version
eksctl upgrade cluster --name oriane-pipeline-cluster --version 1.29

# Update node groups
eksctl upgrade nodegroup --cluster=oriane-pipeline-cluster --name=gpu-nodes-p3
```

### 2. Scaling

```bash
# Scale deployment
kubectl scale deployment pipeline-api --replicas=5 -n pipeline

# Scale node group
eksctl scale nodegroup --cluster=oriane-pipeline-cluster --name=gpu-nodes-p3 --nodes=3
```

### 3. Backup and Restore

```bash
# Backup cluster configuration
kubectl get all -n pipeline -o yaml > pipeline-backup.yaml

# Backup secrets
kubectl get secrets -n pipeline -o yaml > secrets-backup.yaml

# Restore from backup
kubectl apply -f pipeline-backup.yaml
```

### 4. Cost Optimization

```bash
# Enable cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Set node group to scale to zero
eksctl scale nodegroup --cluster=oriane-pipeline-cluster --name=gpu-nodes-p3 --nodes-min=0
```

This deployment guide provides a comprehensive setup for running the Oriane Extraction Pipeline API on EKS with GPU support, proper load balancing, monitoring, and maintenance procedures.
