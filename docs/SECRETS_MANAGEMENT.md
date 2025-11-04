# AWS Secrets Manager Integration Guide

This document explains how secrets are managed in the Insurance Claims Processing system using AWS Secrets Manager and External Secrets Operator.

## Overview

The system uses **AWS Secrets Manager** for secure credential storage and **External Secrets Operator** to synchronize secrets into Kubernetes. This approach provides:

- **Centralized Secret Management**: All secrets stored in AWS Secrets Manager
- **Automatic Rotation**: Secrets can be rotated without redeploying applications
- **Encryption at Rest**: KMS encryption for all secrets
- **Audit Trail**: CloudTrail logs for secret access
- **No Hardcoded Credentials**: Eliminates credentials in code/config files

## Architecture

```
┌─────────────────────┐
│  AWS Secrets        │
│  Manager            │
│  (KMS Encrypted)    │
└──────────┬──────────┘
           │
           │ IRSA
           │ (IAM Roles for Service Accounts)
           ▼
┌─────────────────────┐
│  External Secrets   │
│  Operator           │
│  (Kubernetes)       │
└──────────┬──────────┘
           │
           │ Creates/Updates
           ▼
┌─────────────────────┐
│  Kubernetes         │
│  Secrets            │
│  (insurance-claims) │
└──────────┬──────────┘
           │
           │ Mounted as env vars
           ▼
┌─────────────────────┐
│  Application        │
│  Pods               │
└─────────────────────┘
```

## Components

### 1. AWS Secrets Manager

**Location**: `infrastructure/terraform/secrets-manager.tf`

The Terraform configuration creates:

- **MongoDB Credentials Secret**: Stores MongoDB username, password, database, and port
- **KMS Key**: Custom KMS key for secret encryption with automatic rotation
- **IAM Policy**: Grants External Secrets Operator access to secrets
- **IRSA Role**: IAM Role for Service Accounts for pod-level authentication

### 2. External Secrets Operator

**Location**: `infrastructure/terraform/addons.tf`

Deployed via EKS Blueprints Addons:
- Helm chart version: 0.11.0
- Namespace: `external-secrets`
- Service Account: `external-secrets` (with IRSA annotations)

### 3. Kubernetes Resources

**Location**: `infrastructure/kubernetes/external-secrets.yaml`

Contains:
- **SecretStore**: Connects to AWS Secrets Manager in `us-west-2`
- **ExternalSecret (MongoDB)**: Syncs MongoDB credentials
- **ExternalSecret (LangGraph)**: Syncs LangGraph secrets
- **ClusterSecretStore**: Optional cluster-wide secret access

## Deployment Steps

### Step 1: Deploy Terraform Infrastructure

```bash
cd infrastructure/terraform

# Initialize Terraform (if not already done)
terraform init

# Review the secrets manager configuration
terraform plan -target=aws_secretsmanager_secret.mongodb_credentials_encrypted
terraform plan -target=aws_kms_key.secrets_encryption
terraform plan -target=module.external_secrets_irsa

# Apply the secrets manager configuration
terraform apply

# Note the outputs
terraform output mongodb_secret_arn
terraform output external_secrets_role_arn
```

### Step 2: Deploy External Secrets Operator

The External Secrets Operator is deployed automatically via the EKS Blueprints Addons module when you apply the full Terraform configuration:

```bash
# Apply full Terraform (includes External Secrets Operator)
terraform apply
```

Verify deployment:

```bash
# Check External Secrets Operator is running
kubectl get pods -n external-secrets

# Check the service account has IRSA annotation
kubectl get sa external-secrets -n external-secrets -o yaml | grep eks.amazonaws.com/role-arn
```

### Step 3: Deploy Kubernetes External Secrets

```bash
# Deploy the ExternalSecret resources
kubectl apply -f infrastructure/kubernetes/external-secrets.yaml

# Verify SecretStore is ready
kubectl get secretstores -n insurance-claims

# Verify ExternalSecrets are syncing
kubectl get externalsecrets -n insurance-claims

# Check the created Kubernetes secrets
kubectl get secrets -n insurance-claims | grep external
```

### Step 4: Deploy Applications

```bash
# Deploy all application components
kubectl apply -f infrastructure/kubernetes/mongodb-deployment.yaml
kubectl apply -f infrastructure/kubernetes/coordinator.yaml
kubectl apply -f infrastructure/kubernetes/shared-memory.yaml
kubectl apply -f infrastructure/kubernetes/claims-web-interface.yaml
kubectl apply -f infrastructure/kubernetes/policy-agent.yaml
kubectl apply -f infrastructure/kubernetes/external-integrations.yaml
kubectl apply -f infrastructure/kubernetes/claims-simulator.yaml
```

## Secret Management

### Viewing Secrets

**View secret in AWS Secrets Manager:**

```bash
# Get secret value
aws secretsmanager get-secret-value \
  --secret-id agentic-eks-cluster-mongodb-credentials-encrypted \
  --region us-west-2 \
  --query SecretString \
  --output text | jq .
```

**View synchronized Kubernetes secret:**

```bash
# View the secret (base64 encoded)
kubectl get secret mongodb-secret-external -n insurance-claims -o yaml

# Decode a specific value
kubectl get secret mongodb-secret-external -n insurance-claims \
  -o jsonpath='{.data.MONGO_INITDB_ROOT_USERNAME}' | base64 -d

# View all decoded values
kubectl get secret mongodb-secret-external -n insurance-claims -o json | \
  jq -r '.data | map_values(@base64d)'
```

### Updating Secrets

**Method 1: Update via AWS Console**

1. Go to AWS Secrets Manager Console
2. Find secret: `agentic-eks-cluster-mongodb-credentials-encrypted`
3. Click "Retrieve secret value" → "Edit"
4. Update the secret value (JSON format)
5. Click "Save"

The External Secrets Operator will automatically sync the updated secret within 1 hour (or based on `refreshInterval`).

**Method 2: Update via AWS CLI**

```bash
# Update the secret
aws secretsmanager update-secret \
  --secret-id agentic-eks-cluster-mongodb-credentials-encrypted \
  --region us-west-2 \
  --secret-string '{
    "username": "admin",
    "password": "<NEW_MONGODB_PASSWORD>",
    "database": "claims_db",
    "port": "27017"
  }'
```

**Method 3: Force Immediate Sync**

```bash
# Delete the Kubernetes secret to force immediate resync
kubectl delete secret mongodb-secret-external -n insurance-claims

# The ExternalSecret controller will recreate it immediately
kubectl get secret mongodb-secret-external -n insurance-claims --watch
```

### Rotating MongoDB Password

To rotate the MongoDB password:

1. **Update the secret in AWS Secrets Manager** (see above)
2. **Update MongoDB with new password**:

```bash
# Connect to MongoDB pod
kubectl exec -it -n insurance-claims mongodb-xxxxxxxx-xxxxx -- mongosh

# In MongoDB shell, update password
use admin
db.updateUser("admin", {pwd: "<NEW_MONGODB_PASSWORD>"})
exit
```

3. **Force secret sync** (optional for immediate update):

```bash
kubectl delete secret mongodb-secret-external -n insurance-claims
```

4. **Restart application pods** to pick up new credentials:

```bash
kubectl rollout restart deployment/coordinator -n insurance-claims
kubectl rollout restart deployment/shared-memory -n insurance-claims
kubectl rollout restart deployment/claims-web-interface -n insurance-claims
```

## Troubleshooting

### ExternalSecret Not Syncing

**Check ExternalSecret status:**

```bash
kubectl describe externalsecret mongodb-credentials -n insurance-claims
```

**Common issues:**

1. **IRSA permissions issue**:
   ```bash
   # Verify service account annotation
   kubectl get sa external-secrets -n external-secrets -o yaml

   # Should show: eks.amazonaws.com/role-arn
   ```

2. **Secret not found in AWS**:
   ```bash
   # Verify secret exists
   aws secretsmanager list-secrets --region us-west-2 | \
     grep agentic-eks-cluster-mongodb-credentials
   ```

3. **Wrong region**:
   - Verify SecretStore is configured for correct region
   - Check AWS_REGION in ExternalSecret logs

**View External Secrets Operator logs:**

```bash
kubectl logs -n external-secrets deployment/external-secrets -f
```

### Application Can't Access Secret

**Verify secret exists:**

```bash
kubectl get secret mongodb-secret-external -n insurance-claims
```

**Check pod environment variables:**

```bash
kubectl exec -it -n insurance-claims <pod-name> -- env | grep MONGODB
```

**Verify secret is mounted correctly:**

```bash
kubectl describe pod <pod-name> -n insurance-claims | grep -A 10 "Environment"
```

### Permission Errors

If External Secrets Operator shows permission errors:

```bash
# Check IAM role policy
aws iam get-role --role-name <external-secrets-role-name>

# Check policy document
aws iam get-policy-version \
  --policy-arn <policy-arn> \
  --version-id v1 \
  --query 'PolicyVersion.Document'
```

## Security Best Practices

1. **KMS Encryption**: All secrets are encrypted at rest with custom KMS key
2. **IAM Least Privilege**: IRSA role has minimum required permissions
3. **Secret Rotation**: Implement automatic secret rotation where possible
4. **Audit Logging**: Enable CloudTrail for secret access auditing
5. **No Hardcoded Secrets**: Never commit secrets to Git
6. **Recovery Window**: Secrets have 7-day recovery window before deletion

## Production Considerations

### High Availability

- External Secrets Operator runs with multiple replicas for HA
- Secrets are cached in Kubernetes for availability during AWS outages

### Monitoring

Monitor these metrics:

```bash
# External Secrets sync status
kubectl get externalsecrets -A --watch

# Secret age (detect stale secrets)
kubectl get secrets -A -o json | \
  jq -r '.items[] | select(.metadata.name | contains("external")) |
  "\(.metadata.namespace)/\(.metadata.name): \(.metadata.creationTimestamp)"'
```

### Backup and Recovery

```bash
# Backup secret from AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id agentic-eks-cluster-mongodb-credentials-encrypted \
  --region us-west-2 > mongodb-secret-backup.json

# Restore (if needed)
aws secretsmanager update-secret \
  --secret-id agentic-eks-cluster-mongodb-credentials-encrypted \
  --region us-west-2 \
  --secret-string "$(cat mongodb-secret-backup.json | jq -r .SecretString)"
```

## References

- [External Secrets Operator Documentation](https://external-secrets.io/)
- [AWS Secrets Manager User Guide](https://docs.aws.amazon.com/secretsmanager/)
- [EKS IRSA Documentation](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [KMS Key Rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)
