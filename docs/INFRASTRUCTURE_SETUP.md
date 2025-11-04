# Infrastructure Setup Guide

Complete guide to provisioning and managing the AWS infrastructure for the Insurance Claims Processing System.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Infrastructure Components](#infrastructure-components)
5. [Deployment Options](#deployment-options)
6. [ALB Configuration](#alb-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Cost Optimization](#cost-optimization)

---

## Overview

This project uses **Terraform** to provision a complete AWS infrastructure including:

- **VPC**: Multi-AZ setup with public and private subnets
- **EKS Cluster**: Kubernetes 1.33 with managed node groups
- **Karpenter**: Advanced autoscaling for workload nodes
- **AWS Load Balancer Controller**: Automatic ALB provisioning for ingress
- **Storage**: EBS CSI driver for persistent volumes, S3 for application data
- **Monitoring**: CloudWatch Container Insights
- **Networking**: NAT gateways, security groups, network policies

All infrastructure is defined as code in `infrastructure/terraform/`.

---

## Prerequisites

### Required Tools

```bash
# Install required CLI tools
brew install awscli terraform kubectl jq  # macOS
# or
apt-get install awscli terraform kubectl jq  # Linux
```

**Version Requirements:**
- AWS CLI: >= 2.0
- Terraform: >= 1.5
- kubectl: >= 1.28
- jq: latest

### AWS Account Setup

```bash
# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity

# Output should show:
# {
#     "UserId": "...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/yourname"
# }
```

**Required AWS Permissions:**
- EKS (full access)
- EC2 (VPC, subnets, security groups, NAT gateways)
- IAM (roles, policies for EKS and services)
- S3 (bucket creation)
- CloudWatch (logs, metrics)

### Configure Terraform Variables

```bash
cd infrastructure/terraform

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

**Key Configuration Options:**

```hcl
# infrastructure/terraform/terraform.tfvars

# Project settings
project_name = "insurance"
environment  = "production"
region       = "us-west-2"

# EKS cluster
cluster_name    = "agentic"
cluster_version = "1.33"

# VPC settings
vpc_cidr = "10.0.0.0/16"
single_nat_gateway = false  # Set to true for cost savings

# Addons
enable_karpenter          = true   # Required for autoscaling
enable_cloudwatch_metrics = true   # Recommended for production
enable_fluentbit_logging  = true   # Recommended for production
enable_s3_bucket          = true   # Required for data storage
```

---

## Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# Deploy everything with one command
./scripts/deploy-infrastructure.sh deploy
```

This will:
1. Validate prerequisites
2. Initialize Terraform
3. Show plan and ask for confirmation
4. Deploy all infrastructure
5. Configure kubectl
6. Wait for critical components (ALB Controller, Karpenter)
7. Display summary

**Time:** ~20-25 minutes

### Option 2: Manual Step-by-Step

```bash
# 1. Preview changes
./scripts/deploy-infrastructure.sh plan

# 2. Apply changes
./scripts/deploy-infrastructure.sh deploy

# 3. Validate deployment
./scripts/validate-infrastructure.sh
```

### Post-Deployment Validation

```bash
# Run comprehensive validation
./scripts/validate-infrastructure.sh

# Should show:
# ✓ AWS connectivity
# ✓ EKS cluster is ACTIVE
# ✓ kubectl access working
# ✓ Nodes ready
# ✓ Core addons running
# ✓ AWS Load Balancer Controller running  ← Required for ALB!
# ✓ Karpenter running
# ✓ VPC configured
```

---

## Infrastructure Components

### 1. Networking (VPC)

**Created Resources:**
- 1 VPC with configurable CIDR (default: 10.0.0.0/16)
- 3 public subnets across 3 availability zones
- 3 private subnets across 3 availability zones
- Internet Gateway for public subnet internet access
- NAT Gateways for private subnet internet access
- Route tables and associations

**Terraform Files:**
- `infrastructure/terraform/vpc.tf`

### 2. EKS Cluster

**Created Resources:**
- EKS control plane (managed by AWS)
- Managed node group: 2x m5.large for core components
  - Tainted with `CriticalAddonsOnly=true:NoSchedule`
  - Runs: Karpenter, ALB Controller, CoreDNS, etc.
- Cluster encryption with AWS KMS
- CloudWatch logging (API, audit, authenticator, controller, scheduler)

**Terraform Files:**
- `infrastructure/terraform/eks.tf`
- `infrastructure/terraform/iam.tf`

### 3. Karpenter (Autoscaling)

**Purpose:** Automatically provisions worker nodes based on pod requirements

**Node Pools Created:**
- `general-purpose`: CPU workloads (m5, m6i, t3)
- `gpu-workloads`: LLM inference (g5, g4dn with NVIDIA GPUs)

**Terraform Files:**
- `infrastructure/terraform/addons.tf` (lines 94-119)
- `infrastructure/terraform/karpenter-nodepools.tf`

**How it works:**
1. Pod is created with resource requests
2. Karpenter finds cheapest instance type that fits
3. Node is provisioned in ~30-60 seconds
4. Pod schedules on new node
5. Unused nodes are automatically terminated after 30s

### 4. AWS Load Balancer Controller

**Purpose:** Automatically creates Application Load Balancers (ALBs) for Kubernetes Ingress resources

**Why it's critical:**
- **Without it:** Your ingress resources won't create ALBs
- **With it:** ALBs are automatically created, configured, and cleaned up

**Terraform Configuration:**
```hcl
# infrastructure/terraform/addons.tf (lines 122-178)
enable_aws_load_balancer_controller = true
```

**How to verify it's running:**
```bash
kubectl get deployment -n kube-system aws-load-balancer-controller

# Should show:
# NAME                           READY   UP-TO-DATE   AVAILABLE
# aws-load-balancer-controller   1/1     1            1
```

### 5. Storage

**EBS CSI Driver:**
- Enables dynamic provisioning of EBS volumes
- Used for MongoDB, Redis persistent storage

**S3 Bucket:**
- Application logs
- Data exports
- Model artifacts

**Terraform Files:**
- `infrastructure/terraform/addons.tf` (lines 13-25)
- `infrastructure/terraform/storage.tf`

### 6. Monitoring & Logging

**CloudWatch Container Insights:**
- Cluster, node, and pod metrics
- Enabled by default

**AWS for Fluent Bit (optional):**
- Centralized logging to CloudWatch and S3
- Set `enable_fluentbit_logging = true`

**Terraform Files:**
- `infrastructure/terraform/addons.tf` (lines 182-200)

---

## Deployment Options

### Development / Testing

**Goal:** Minimize cost while maintaining functionality

```hcl
# terraform.tfvars
single_nat_gateway = true         # Use 1 NAT gateway instead of 3
enable_fluentbit_logging = false  # Disable centralized logging
enable_prometheus_grafana = false # Disable monitoring stack
```

**Estimated cost:** ~$100-120/month

### Production

**Goal:** High availability, monitoring, logging

```hcl
# terraform.tfvars
single_nat_gateway = false        # Multi-AZ NAT gateways
enable_fluentbit_logging = true   # Centralized logging
enable_cloudwatch_metrics = true  # Container Insights
enable_prometheus_grafana = true  # Optional: Prometheus/Grafana stack
```

**Estimated cost:** ~$150-200/month (base) + workload nodes

---

## ALB Configuration

### How ALB is Created

**Step 1:** Terraform installs AWS Load Balancer Controller
```hcl
# infrastructure/terraform/addons.tf
enable_aws_load_balancer_controller = true
```

**Step 2:** Deploy your application ingress
```bash
kubectl apply -f infrastructure/kubernetes/insurance-claims-ingress.yaml
```

**Step 3:** AWS Load Balancer Controller sees the ingress and:
1. Creates an Application Load Balancer
2. Configures target groups
3. Creates listener rules
4. Registers pods as targets
5. Configures health checks

**Step 4:** Get ALB URL
```bash
kubectl get ingress -n insurance-claims

# Output:
# NAME                        CLASS   HOSTS   ADDRESS                                                                  PORTS
# insurance-claims-ingress    alb     *       insurance-claims-alb-xxxxxxxx.us-west-2.elb.amazonaws.com              80
```

### ALB Configuration Details

The ingress manifest (`infrastructure/kubernetes/insurance-claims-ingress.yaml`) includes:

```yaml
metadata:
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/load-balancer-name: insurance-claims-alb
    alb.ingress.kubernetes.io/healthcheck-path: /
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
spec:
  ingressClassName: alb  # Uses AWS Load Balancer Controller
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: claims-web-interface
            port:
              number: 8080
```

### Troubleshooting ALB Issues

**Problem:** Ingress created but no ALB

```bash
# Check if AWS Load Balancer Controller is running
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Should show 1 running pod
```

If not running:
```bash
# Reinstall via Terraform
cd infrastructure/terraform
terraform apply -target=module.eks_blueprints_addons.helm_release.aws_load_balancer_controller
```

**Problem:** ALB created but returns 502 errors

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Check pod status
kubectl get pods -n insurance-claims

# Check service endpoints
kubectl get endpoints -n insurance-claims
```

**Problem:** ALB not accessible from internet

```bash
# Verify ALB scheme is internet-facing
aws elbv2 describe-load-balancers \
  --names insurance-claims-alb \
  --query 'LoadBalancers[0].Scheme'

# Should return: "internet-facing"

# Check security groups allow port 80
aws ec2 describe-security-groups \
  --group-ids <alb-security-group-id> \
  --query 'SecurityGroups[0].IpPermissions'
```

---

## Troubleshooting

### Common Issues

#### 1. Terraform fails with "InvalidParameter: Neither subnets nor security groups are tagged"

**Cause:** VPC subnets need tags for AWS Load Balancer Controller

**Solution:** Already handled in `vpc.tf` - check tags are applied:
```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id>" --query 'Subnets[*].[SubnetId,Tags]'
```

#### 2. Nodes not joining cluster

**Cause:** IAM role not configured correctly

**Solution:**
```bash
# Check node IAM role
kubectl get nodes
kubectl describe node <node-name>

# Verify access entry
aws eks list-access-entries --cluster-name <cluster-name>
```

#### 3. Karpenter not provisioning nodes

**Cause:** NodePools not created or misconfigured

**Solution:**
```bash
# Check NodePools
kubectl get nodepools

# Check Karpenter logs
kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter

# Manually create NodePools
cd infrastructure/terraform
terraform apply -target=kubectl_manifest.karpenter_nodepool_general
```

#### 4. ALB Controller webhook errors

**Cause:** Certificate not ready

**Solution:**
```bash
# Delete webhook and let it recreate
kubectl delete validatingwebhookconfigurations aws-load-balancer-webhook
kubectl delete mutatingwebhookconfigurations aws-load-balancer-webhook

# Restart controller
kubectl rollout restart deployment/aws-load-balancer-controller -n kube-system
```

### Validation Commands

```bash
# Full validation suite
./scripts/validate-infrastructure.sh

# Quick checks
kubectl get nodes
kubectl get pods -A
kubectl get ingress -A

# Check specific components
kubectl get deployment -n kube-system | grep -E "aws-load-balancer|karpenter|coredns"

# Terraform outputs
cd infrastructure/terraform
terraform output
```

---

## Cost Optimization

### Monthly Cost Breakdown

**Base Infrastructure:**
- EKS control plane: $73/month
- 2x m5.large (core nodes): ~$70/month
- 3x NAT gateways: ~$45/month (or $15 with single NAT)
- Data transfer: ~$10/month

**Total base: ~$198/month (or $153 with single NAT gateway)**

**Workload Nodes (created by Karpenter):**
- Depends on your workload
- Example: 3x m5.large = ~$105/month
- Karpenter automatically removes unused nodes

### Cost Saving Tips

1. **Use single NAT gateway for dev/test:**
```hcl
single_nat_gateway = true  # Saves ~$30/month
```

2. **Use Spot instances for workloads:**
```yaml
# Karpenter NodePool already configured for Spot
spec:
  disruption:
    consolidationPolicy: WhenEmpty
  requirements:
    - key: karpenter.sh/capacity-type
      operator: In
      values: ["spot", "on-demand"]
```

3. **Reduce core node count:**
```hcl
# eks.tf - for non-prod environments
min_size     = 1
max_size     = 1
desired_size = 1
```

4. **Disable optional addons:**
```hcl
enable_fluentbit_logging  = false
enable_prometheus_grafana = false
```

5. **Schedule cluster downtime:**
```bash
# Stop all Karpenter nodes at night
kubectl scale deployment --all --replicas=0 -n insurance-claims

# Resume in morning
kubectl scale deployment --all --replicas=2 -n insurance-claims
```

---

## Cleanup

### Destroy All Infrastructure

```bash
# Option 1: Use helper script
./scripts/deploy-infrastructure.sh destroy

# Option 2: Manual
cd infrastructure/terraform
terraform destroy
```

**Important:** This will delete:
- All Kubernetes workloads
- EKS cluster
- VPC and networking
- S3 buckets and data (if `force_destroy = true`)
- All associated resources

**Before destroying:**
```bash
# 1. Export any important data
kubectl get all -A -o yaml > cluster-backup.yaml

# 2. Backup S3 bucket
aws s3 sync s3://<bucket-name> ./backup/

# 3. Delete all Kubernetes resources first (optional but cleaner)
kubectl delete namespace insurance-claims

# 4. Now destroy infrastructure
./scripts/deploy-infrastructure.sh destroy
```

---

## Next Steps

After infrastructure is deployed:

1. **Validate everything is working:**
```bash
./scripts/validate-infrastructure.sh
```

2. **Build and push Docker images:**
```bash
export ECR_REGISTRY=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-west-2.amazonaws.com
./scripts/build-docker-images.sh build
./scripts/build-docker-images.sh push
```

3. **Deploy application:**
```bash
./scripts/deploy-kubernetes.sh deploy
```

4. **Get ALB URL and access application:**
```bash
kubectl get ingress -n insurance-claims
```

---

## Additional Resources

- [Terraform Documentation](infrastructure/terraform/README.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Architecture Overview](ARCHITECTURE.md)
- [AWS Load Balancer Controller Docs](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Karpenter Documentation](https://karpenter.sh/)

---

## Support

For infrastructure issues:

1. Run validation: `./scripts/validate-infrastructure.sh`
2. Check Terraform state: `cd infrastructure/terraform && terraform show`
3. Review AWS console for resource status
4. Check component logs: `kubectl logs -n kube-system <pod-name>`
5. Open GitHub issue with validation output
