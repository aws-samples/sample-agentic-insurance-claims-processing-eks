# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Insurance Claims Processing system to production with all security best practices enabled.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Configuration](#pre-deployment-configuration)
3. [Terraform Deployment](#terraform-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Production Checklist](#production-checklist)

---

## Prerequisites

### Required Tools
```bash
# Verify installations
terraform --version  # >= 1.0
kubectl version --client  # >= 1.28
aws --version  # >= 2.0
helm version  # >= 3.0
```

### AWS Prerequisites
- AWS Account with appropriate permissions
- Route53 hosted zone (for custom domain)
- ACM certificate or ability to create one
- Configured AWS CLI with credentials

### Environment Setup
```bash
# Set AWS credentials (PLACEHOLDER VALUES - replace with actual credentials)
# IMPORTANT: Use AWS IAM roles or AWS SSO instead of hardcoded credentials when possible
export AWS_ACCESS_KEY_ID="<AWS_ACCESS_KEY_ID>"
export AWS_SECRET_ACCESS_KEY="<AWS_SECRET_ACCESS_KEY>"
export AWS_REGION="us-west-2"

# Set AWS profile (RECOMMENDED - more secure than hardcoded credentials)
export AWS_PROFILE="<AWS_PROFILE_NAME>"
```

---

## Pre-Deployment Configuration

### Step 1: Clone and Configure Repository

```bash
cd insurance/agentic-on-eks
```

### Step 2: Configure Terraform Variables

Create `infrastructure/terraform/terraform.tfvars`:

```hcl
###############################################################
# General Configuration
###############################################################
region       = "us-west-2"
environment  = "production"
project_name = "insurance-claims"

###############################################################
# VPC Configuration
###############################################################
vpc_cidr             = "10.0.0.0/16"
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# Cost optimization - use single NAT gateway for non-production
single_nat_gateway = true  # Set to false for production HA

###############################################################
# EKS Configuration
###############################################################
cluster_name    = "production-eks-cluster"
cluster_version = "1.31"

# Restrict access to your IP or VPN
cluster_endpoint_public_access_cidrs = ["YOUR_IP_ADDRESS/32"]

###############################################################
# ACM Certificate Configuration
###############################################################
create_acm_certificate = true
domain_name           = "claims.yourcompany.com"
route53_zone_id       = "Z1234567890ABC"  # Your Route53 zone ID

###############################################################
# Addons Configuration
###############################################################
enable_cloudwatch_metrics = true
enable_fluentbit_logging  = true
enable_prometheus_grafana = true
enable_nvidia_device_plugin = true
enable_s3_bucket = true
```

### Step 3: Initialize Terraform Backend

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create S3 backend for state (recommended for production)
# Update backend.tf with your S3 bucket name
```

---

## Terraform Deployment

### Step 1: Plan Infrastructure

```bash
# Review what will be created
terraform plan -out=tfplan

# Review the plan carefully
```

### Step 2: Deploy Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# This will create:
# - VPC with public/private subnets
# - EKS cluster with Karpenter
# - AWS Secrets Manager with KMS encryption
# - External Secrets Operator
# - ACM Certificate (if enabled)
# - IAM roles with least-privilege policies
# - S3 buckets for storage
# - CloudWatch log groups
```

### Step 3: Capture Outputs

```bash
# Save important outputs
terraform output > ../deployment-outputs.txt

# Key outputs:
terraform output acm_certificate_arn
terraform output mongodb_secret_arn
terraform output external_secrets_role_arn
```

### Step 4: Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-west-2 \
  --name production-eks-cluster

# Verify connection
kubectl get nodes
```

---

## Kubernetes Deployment

### Step 1: Verify External Secrets Operator

```bash
# Check External Secrets Operator is running
kubectl get pods -n external-secrets

# Should show: external-secrets-* Running
```

### Step 2: Update Ingress with Certificate ARN

```bash
# Get certificate ARN
CERT_ARN=$(terraform output -raw acm_certificate_arn)

# Update ingress configuration
sed -i.bak "s|<ACM_CERTIFICATE_ARN>|$CERT_ARN|g" \
  ../../infrastructure/kubernetes/insurance-claims-ingress.yaml

# Verify the replacement
grep certificate-arn ../../infrastructure/kubernetes/insurance-claims-ingress.yaml
```

### Step 3: Deploy External Secrets

```bash
# Deploy ExternalSecret resources
kubectl apply -f ../../infrastructure/kubernetes/external-secrets.yaml

# Verify secrets are syncing
kubectl get externalsecrets -n insurance-claims
kubectl get secretstores -n insurance-claims

# Check created secrets
kubectl get secrets -n insurance-claims | grep external
```

### Step 4: Deploy Application Components

```bash
# Deploy in order
kubectl apply -f ../../infrastructure/kubernetes/mongodb-deployment.yaml
kubectl apply -f ../../infrastructure/kubernetes/redis-deployment.yaml
kubectl apply -f ../../infrastructure/kubernetes/ollama-deployment.yaml

# Deploy application services
kubectl apply -f ../../infrastructure/kubernetes/shared-memory.yaml
kubectl apply -f ../../infrastructure/kubernetes/coordinator.yaml
kubectl apply -f ../../infrastructure/kubernetes/policy-agent.yaml
kubectl apply -f ../../infrastructure/kubernetes/external-integrations.yaml

# Deploy web interface and simulator
kubectl apply -f ../../infrastructure/kubernetes/claims-web-interface.yaml
kubectl apply -f ../../infrastructure/kubernetes/claims-simulator.yaml

# Deploy ingress
kubectl apply -f ../../infrastructure/kubernetes/insurance-claims-ingress.yaml
```

### Step 5: Deploy Observability (Optional)

```bash
# Deploy CloudWatch observability
kubectl apply -f ../../infrastructure/kubernetes/cloudwatch-observability.yaml
```

---

## Post-Deployment Verification

### Step 1: Verify All Pods are Running

```bash
# Check all pods
kubectl get pods -n insurance-claims

# All pods should be in Running state
# Expected pods:
# - mongodb-*
# - redis-service-*
# - ollama-service-*
# - coordinator-*
# - shared-memory-*
# - policy-agent-*
# - external-integrations-*
# - claims-web-interface-*
# - claims-simulator-*
```

### Step 2: Verify Secrets

```bash
# Check secret synchronization
kubectl describe externalsecret mongodb-credentials -n insurance-claims

# Should show: Status: SecretSynced

# Verify pods can access secrets
kubectl exec -it -n insurance-claims \
  $(kubectl get pod -n insurance-claims -l app=coordinator -o jsonpath='{.items[0].metadata.name}') \
  -- env | grep MONGODB_URL
```

### Step 3: Verify Ingress and ALB

```bash
# Get ALB DNS name
kubectl get ingress insurance-claims-ingress -n insurance-claims

# Test HTTP to HTTPS redirect
ALB_DNS=$(kubectl get ingress insurance-claims-ingress -n insurance-claims \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

curl -I http://$ALB_DNS
# Should return: HTTP/1.1 301 Moved Permanently

# Test HTTPS (after DNS propagation)
curl -I https://claims.yourcompany.com
# Should return: HTTP/2 200
```

### Step 4: Test Application

```bash
# Forward port for testing
kubectl port-forward -n insurance-claims svc/claims-web-interface 8080:8080

# Open browser to http://localhost:8080
```

### Step 5: Configure DNS (if using custom domain)

```bash
# Get ALB DNS name
ALB_DNS=$(kubectl get ingress insurance-claims-ingress -n insurance-claims \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Create Route53 alias record
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "claims.yourcompany.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z1H1FL5HABSF5",
          "DNSName": "'$ALB_DNS'",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

---

## Production Checklist

### Security

- [ ] **Secrets Management**
  - [ ] Verified all secrets are in AWS Secrets Manager
  - [ ] No hardcoded credentials in code/config
  - [ ] KMS encryption enabled for secrets
  - [ ] Secret rotation IAM role created
  - [ ] External Secrets Operator syncing correctly

- [ ] **Network Security**
  - [ ] HTTPS enforced (HTTP redirects to HTTPS)
  - [ ] TLS 1.2+ enforced
  - [ ] ACM certificate installed and validated
  - [ ] Security groups restrict access to VPC
  - [ ] NAT gateways deployed for private subnets

- [ ] **Container Security**
  - [ ] All containers running as non-root
  - [ ] Security contexts configured
  - [ ] Read-only filesystems where possible
  - [ ] No privilege escalation allowed

- [ ] **IAM & Access**
  - [ ] IRSA configured for all service accounts
  - [ ] Least-privilege IAM policies
  - [ ] Condition-based policies enforced
  - [ ] EKS cluster endpoint access restricted

### High Availability

- [ ] **Infrastructure**
  - [ ] Multi-AZ deployment
  - [ ] Multiple NAT gateways (if HA required)
  - [ ] EBS volumes with gp3 storage class
  - [ ] Pod disruption budgets configured

- [ ] **Application**
  - [ ] Multiple replicas for critical services
  - [ ] Liveness and readiness probes configured
  - [ ] Resource requests and limits set
  - [ ] HPA configured for auto-scaling

### Monitoring & Observability

- [ ] **Logging**
  - [ ] CloudWatch logs enabled
  - [ ] Fluent Bit configured for log shipping
  - [ ] Log retention policies set (30 days)
  - [ ] Application logs structured (JSON)

- [ ] **Metrics**
  - [ ] CloudWatch metrics enabled
  - [ ] Prometheus/Grafana deployed (optional)
  - [ ] Custom application metrics exported
  - [ ] ServiceMonitors configured

- [ ] **Tracing**
  - [ ] X-Ray daemon deployed
  - [ ] Applications instrumented for tracing
  - [ ] Distributed tracing enabled

- [ ] **Alerting**
  - [ ] CloudWatch alarms configured
  - [ ] SNS topics for notifications
  - [ ] PagerDuty/Slack integration (if needed)

### Backup & DR

- [ ] **Data Backup**
  - [ ] MongoDB backup strategy defined
  - [ ] EBS snapshots scheduled
  - [ ] S3 bucket versioning enabled
  - [ ] Cross-region replication (if required)

- [ ] **Disaster Recovery**
  - [ ] DR runbook created
  - [ ] RTO/RPO defined
  - [ ] Backup restoration tested
  - [ ] Terraform state backed up to S3

### Cost Optimization

- [ ] **Resource Right-Sizing**
  - [ ] Pod resource requests/limits optimized
  - [ ] Karpenter configured for spot instances
  - [ ] Single NAT gateway for dev (multiple for prod)
  - [ ] EBS volumes using gp3 (cost-effective)

- [ ] **Auto-Scaling**
  - [ ] Karpenter node auto-scaling enabled
  - [ ] HPA configured for application pods
  - [ ] Scale-down policies set appropriately

### Compliance & Audit

- [ ] **Audit Logging**
  - [ ] CloudTrail enabled
  - [ ] EKS audit logs enabled
  - [ ] Secret access logged

- [ ] **Compliance**
  - [ ] Data encryption at rest
  - [ ] Data encryption in transit
  - [ ] Network segmentation implemented
  - [ ] Regular vulnerability scanning

---

## Troubleshooting

### Common Issues

**Issue: Pods stuck in Pending state**
```bash
# Check pod events
kubectl describe pod <pod-name> -n insurance-claims

# Common causes:
# 1. Insufficient cluster capacity - Karpenter will provision nodes
# 2. ImagePullBackOff - check ECR permissions
# 3. PVC not bound - check storage class
```

**Issue: External Secrets not syncing**
```bash
# Check External Secrets Operator logs
kubectl logs -n external-secrets deployment/external-secrets

# Check IRSA annotation
kubectl get sa external-secrets -n external-secrets -o yaml | grep eks.amazonaws.com/role-arn

# Verify secret exists in AWS
aws secretsmanager get-secret-value \
  --secret-id agentic-eks-cluster-mongodb-credentials-encrypted \
  --region us-west-2
```

**Issue: ALB not created**
```bash
# Check AWS Load Balancer Controller
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check ingress events
kubectl describe ingress insurance-claims-ingress -n insurance-claims
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor CloudWatch alarms
- Check pod health and resource usage
- Review application logs for errors

**Weekly:**
- Review security group rules
- Check for pending Kubernetes/EKS updates
- Review cost reports

**Monthly:**
- Rotate MongoDB credentials
- Update container images
- Review and update IAM policies
- Test disaster recovery procedures

**Quarterly:**
- Full security audit
- Performance testing
- Capacity planning review
- Update Kubernetes version

---

## Rollback Procedures

### Terraform Rollback
```bash
# Revert to previous Terraform state
terraform state pull > current-state.json
terraform state push previous-state.json
```

### Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/coordinator -n insurance-claims

# Rollback to specific revision
kubectl rollout history deployment/coordinator -n insurance-claims
kubectl rollout undo deployment/coordinator --to-revision=2 -n insurance-claims
```

---

## Support & Resources

- **Documentation**: `/docs` directory
- **Security Guide**: `docs/SECURITY_FIXES_SUMMARY.md`
- **Secrets Management**: `docs/SECRETS_MANAGEMENT.md`
- **Terraform Docs**: `infrastructure/terraform/README.md`

---

**Last Updated**: 2025-10-29
**Version**: 1.0 Production-Ready
