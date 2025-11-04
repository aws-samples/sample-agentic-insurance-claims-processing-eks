# Automated Deployment Guide

This guide explains the automated deployment system that handles infrastructure, configuration, and validation automatically.

## Overview

The automated deployment system consists of three main scripts:

1. **`scripts/deploy-all.sh`** - Complete one-command deployment
2. **`scripts/deploy-infrastructure.sh`** - Infrastructure only
3. **`scripts/validate-deployment.sh`** - Post-deployment validation

---

## Quick Start

### One-Command Deployment

```bash
# Deploy everything automatically
./scripts/deploy-all.sh

# This script will:
# 1. Check prerequisites (terraform, aws, kubectl, jq)
# 2. Validate AWS credentials
# 3. Deploy Terraform infrastructure
# 4. Capture outputs (cluster name, certificate ARN, etc.)
# 5. Configure kubectl automatically
# 6. Update Kubernetes manifests with outputs
# 7. Deploy all Kubernetes resources
# 8. Validate the deployment
# 9. Display access URLs
```

**Total Time:** 15-20 minutes

---

## What Gets Automated

### 1. Infrastructure Deployment

**Automated Steps:**
- ✅ Terraform initialization
- ✅ Plan generation
- ✅ Infrastructure provisioning (VPC, EKS, Secrets Manager, etc.)
- ✅ Output capture

**Manual Input Required:**
- One-time: Edit `infrastructure/terraform/terraform.tfvars`
- Interactive: Confirm Terraform apply

### 2. Configuration Management

**Automated Steps:**
- ✅ ACM certificate ARN injection into ingress manifest
- ✅ kubectl configuration for EKS cluster
- ✅ Environment variable export
- ✅ Backup of original manifests (.bak files)

**What Gets Updated:**
```yaml
# infrastructure/kubernetes/insurance-claims-ingress.yaml
alb.ingress.kubernetes.io/certificate-arn: <AUTOMATICALLY_INJECTED>
```

### 3. Kubernetes Deployment

**Automated Steps:**
- ✅ ExternalSecrets deployment
- ✅ Secret synchronization wait
- ✅ Application deployment in correct order:
  1. External Secrets
  2. MongoDB
  3. Redis
  4. Ollama
  5. Shared Memory
  6. Coordinator
  7. Policy Agent
  8. External Integrations
  9. Web Interface
  10. Claims Simulator
  11. Ingress

### 4. Validation

**Automated Checks:**
- ✅ Cluster connectivity
- ✅ External Secrets Operator status
- ✅ Secret synchronization
- ✅ Pod health (running/ready)
- ✅ Service availability
- ✅ Ingress/ALB provisioning
- ✅ HTTP to HTTPS redirect test

---

## Configuration

### Terraform Variables

Before running `deploy-all.sh`, configure your deployment:

```hcl
# infrastructure/terraform/terraform.tfvars

# Basic Configuration
region = "us-west-2"
environment = "production"
project_name = "insurance-claims"

# ACM Certificate (Optional - for custom domain)
create_acm_certificate = true  # Set to true for production
domain_name = "claims.yourcompany.com"
route53_zone_id = "Z1234567890ABC"

# Feature Flags
enable_cloudwatch_metrics = true
enable_fluentbit_logging = true
enable_prometheus_grafana = false  # Set true if needed
enable_nvidia_device_plugin = true
enable_s3_bucket = true
```

---

## Script Details

### deploy-all.sh

**What It Does:**
1. **Prerequisites Check**
   - Verifies tools: terraform, aws, kubectl, jq
   - Validates AWS credentials

2. **Terraform Deployment**
   - Creates `terraform.tfvars` if missing
   - Runs `terraform init`, `plan`, and `apply`
   - Prompts for confirmation before applying

3. **Output Capture**
   - Extracts:
     - AWS Region
     - EKS Cluster Name
     - ACM Certificate ARN (if created)
   - Saves to `deployment-outputs.env`

4. **kubectl Configuration**
   - Updates kubeconfig automatically
   - Waits for cluster to be ready
   - Verifies node connectivity

5. **Manifest Updates**
   - Injects ACM certificate ARN into ingress
   - Creates `.bak` backup of original files
   - Removes certificate annotation if no cert exists

6. **Kubernetes Deployment**
   - Applies manifests in correct order
   - Waits for External Secrets Operator
   - Verifies secret synchronization

7. **Validation**
   - Displays pod status
   - Shows ingress/ALB information
   - Provides access URLs

### validate-deployment.sh

**What It Checks:**
- Cluster connection
- External Secrets Operator health
- Secret synchronization status
- Pod health (running/ready counts)
- Service availability
- Ingress/ALB provisioning
- HTTP redirect functionality

**Usage:**
```bash
# Run anytime to check status
./scripts/validate-deployment.sh

# Output example:
# ✓ Connected to cluster
# ✓ External Secrets Operator running
# ✓ Secrets synchronized
# ✓ All 12 pods running
# ✓ ALB provisioned
#   DNS: k8s-insuranc-insuranc-abc123.us-west-2.elb.amazonaws.com
# ✓ ALB responding (HTTP 301)
```

---

## Outputs

### deployment-outputs.env

After successful deployment, this file contains:

```bash
export AWS_REGION='us-west-2'
export EKS_CLUSTER_NAME='agentic-eks-cluster'
export ACM_CERTIFICATE_ARN='arn:aws:acm:us-west-2:123456789:certificate/abc-123'
```

**Usage:**
```bash
# Source in other scripts
source deployment-outputs.env

# Use in commands
aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION
```

---

## Manual Steps Required

Despite automation, some steps require manual action:

### Before Deployment
1. **Edit terraform.tfvars** with your settings
2. **Confirm Terraform plan** (interactive prompt)

### After Deployment (Optional)
1. **Configure DNS** - Point your domain to ALB
   ```bash
   # Get ALB DNS
   kubectl get ingress insurance-claims-ingress -n insurance-claims
   
   # Create Route53 A record (alias) pointing to ALB
   ```

2. **Load Sample Data** (if needed)
   ```bash
   python3 -m applications.insurance-claims-processing.src.data_loader \
       newdata/syntheticdatageneral/dist/SyntheticInsuranceData-byPolicy-2022-08-11.zip
   ```

---

## Troubleshooting

### Issue: Terraform tfvars not found

**Solution:**
```bash
# Script creates template automatically
# Edit the created terraform.tfvars and run again
cd infrastructure/terraform
vim terraform.tfvars
cd ../..
./scripts/deploy-all.sh
```

### Issue: ACM Certificate not injected

**Check:**
```bash
# View captured outputs
cat deployment-outputs.env

# If ACM_CERTIFICATE_ARN is empty:
# Set create_acm_certificate=true in terraform.tfvars
```

### Issue: Pods not starting

**Check:**
```bash
# Run validation
./scripts/validate-deployment.sh

# Check specific pod
kubectl describe pod <pod-name> -n insurance-claims

# Common issues:
# - External secrets not synced (wait a few minutes)
# - Image pull errors (check ECR permissions)
# - Resource limits (check node capacity)
```

### Issue: ALB not provisioned

**Check:**
```bash
# Check AWS Load Balancer Controller
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check ingress events
kubectl describe ingress insurance-claims-ingress -n insurance-claims

# Wait 5-10 minutes for ALB provisioning
```

---

## Advanced Usage

### Deploy Infrastructure Only

```bash
# If you want to deploy infrastructure separately
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Then deploy Kubernetes manually
kubectl apply -f ../kubernetes/
```

### Update Only Kubernetes

```bash
# If infrastructure already exists
kubectl apply -f infrastructure/kubernetes/

# Or use the deploy-kubernetes.sh script
./scripts/deploy-kubernetes.sh deploy
```

### Re-inject Certificate ARN

```bash
# If you need to update the certificate
source deployment-outputs.env
sed -i "s|<ACM_CERTIFICATE_ARN>|$ACM_CERTIFICATE_ARN|g" \
    infrastructure/kubernetes/insurance-claims-ingress.yaml

kubectl apply -f infrastructure/kubernetes/insurance-claims-ingress.yaml
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to EKS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Deploy Infrastructure & Applications
        run: |
          # Non-interactive deployment
          cd infrastructure/terraform
          terraform init
          terraform apply -auto-approve
          cd ../..
          
          # Configure kubectl
          aws eks update-kubeconfig --name agentic-eks-cluster --region us-west-2
          
          # Deploy applications
          kubectl apply -f infrastructure/kubernetes/
```

---

## Best Practices

1. **Always validate** after deployment
   ```bash
   ./scripts/validate-deployment.sh
   ```

2. **Keep backups** of modified manifests
   - Script creates `.bak` files automatically
   - Commit originals to git

3. **Test in non-production first**
   - Use `environment = "development"` in tfvars
   - Set `create_acm_certificate = false` for testing

4. **Monitor during deployment**
   ```bash
   # In another terminal
   watch kubectl get pods -n insurance-claims
   ```

5. **Save outputs**
   ```bash
   # Keep deployment-outputs.env for reference
   cp deployment-outputs.env deployment-outputs-$(date +%Y%m%d).env
   ```

---

## Summary

The automated deployment system eliminates manual configuration steps:

| Task | Before | After |
|------|--------|-------|
| **Terraform outputs** | Manual copy/paste | Automatic capture |
| **Certificate ARN** | Manual injection | Automatic injection |
| **kubectl config** | Manual setup | Automatic configuration |
| **Deployment order** | Manual sequence | Automatic ordering |
| **Validation** | Manual checks | Automated validation |

**Result:** One command deploys everything correctly configured! 🚀

---

For detailed production deployment guidance, see `docs/DEPLOYMENT.md`.
