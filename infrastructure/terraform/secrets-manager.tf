###############################################################
# AWS Secrets Manager for MongoDB Credentials
###############################################################

# Random password for MongoDB
resource "random_password" "mongodb_password" {
  length  = 32
  special = true
  # MongoDB has some restrictions on special characters
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Secrets Manager Secret for MongoDB
resource "aws_secretsmanager_secret" "mongodb_credentials" {
  name                    = "${local.name}-mongodb-credentials"
  description             = "MongoDB credentials for insurance claims processing"
  recovery_window_in_days = 7 # 7 days recovery window for production safety

  tags = merge(local.tags, {
    Purpose = "MongoDB Credentials"
  })
}

# Secret Version with MongoDB credentials
resource "aws_secretsmanager_secret_version" "mongodb_credentials_version" {
  secret_id = aws_secretsmanager_secret.mongodb_credentials.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.mongodb_password.result
    database = "claims_db"
    port     = "27017"
  })
}

# Enable encryption at rest for the secret
resource "aws_kms_key" "secrets_encryption" {
  description             = "KMS key for encrypting secrets in ${local.name}"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(local.tags, {
    Purpose = "Secrets Encryption"
  })
}

resource "aws_kms_alias" "secrets_encryption_alias" {
  name          = "alias/${local.name}-secrets"
  target_key_id = aws_kms_key.secrets_encryption.key_id
}

# Update MongoDB secret to use KMS encryption
resource "aws_secretsmanager_secret" "mongodb_credentials_encrypted" {
  name                    = "${local.name}-mongodb-credentials-encrypted"
  description             = "Encrypted MongoDB credentials for insurance claims processing"
  kms_key_id              = aws_kms_key.secrets_encryption.arn
  recovery_window_in_days = 7

  tags = merge(local.tags, {
    Purpose   = "MongoDB Credentials (Encrypted)"
    ManagedBy = "terraform"
  })
}

resource "aws_secretsmanager_secret_version" "mongodb_credentials_encrypted_version" {
  secret_id = aws_secretsmanager_secret.mongodb_credentials_encrypted.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.mongodb_password.result
    database = "claims_db"
    port     = "27017"
  })
}

###############################################################
# IAM Policy for External Secrets Operator
###############################################################

# Create IAM policy for External Secrets Operator to access Secrets Manager
# Following least privilege principle - only read access to specific secrets
resource "aws_iam_policy" "external_secrets_policy" {
  name        = "${local.name}-external-secrets-policy"
  description = "Least-privilege policy for External Secrets Operator to access AWS Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadSpecificSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.mongodb_credentials_encrypted.arn,
          aws_secretsmanager_secret.langgraph_secrets.arn
        ]
        Condition = {
          StringEquals = {
            "secretsmanager:ResourceTag/ManagedBy" = "terraform"
          }
        }
      },
      {
        Sid    = "DecryptSecrets"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.secrets_encryption.arn
        ]
        Condition = {
          StringEquals = {
            "kms:ViaService" = "secretsmanager.${var.region}.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = local.tags
}

# IRSA for External Secrets Operator
module "external_secrets_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.49"

  role_name_prefix = "${local.name}-external-secrets-"

  role_policy_arns = {
    external_secrets = aws_iam_policy.external_secrets_policy.arn
  }

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["external-secrets:external-secrets"]
    }
  }

  tags = local.tags
}

###############################################################
# Secret Rotation Configuration
###############################################################

# IAM Role for Lambda Rotation Function
resource "aws_iam_role" "mongodb_rotation_lambda" {
  name = "${local.name}-mongodb-rotation-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.tags
}

# IAM Policy for Lambda Rotation Function
resource "aws_iam_role_policy" "mongodb_rotation_lambda" {
  name = "${local.name}-mongodb-rotation-lambda-policy"
  role = aws_iam_role.mongodb_rotation_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = aws_secretsmanager_secret.mongodb_credentials_encrypted.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetRandomPassword"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.secrets_encryption.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Security group for Lambda rotation function
resource "aws_security_group" "mongodb_rotation_lambda" {
  name_prefix = "${local.name}-mongodb-rotation-lambda-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for MongoDB rotation Lambda function"

  egress {
    description = "MongoDB access"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    description = "HTTPS to AWS APIs"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name}-mongodb-rotation-lambda"
  })
}

###############################################################
# Lambda Rotation Function (Placeholder)
###############################################################

# Note: For full secret rotation, create a Lambda function in
# infrastructure/terraform/lambda/mongodb-rotation/
# See docs/SECRETS_MANAGEMENT.md for implementation details

# Secret rotation schedule (30-day automatic rotation)
# Uncomment when Lambda rotation function is ready
#
# resource "aws_secretsmanager_secret_rotation" "mongodb_credentials" {
#   secret_id           = aws_secretsmanager_secret.mongodb_credentials_encrypted.id
#   rotation_lambda_arn = aws_lambda_function.mongodb_rotation.arn
#
#   rotation_rules {
#     automatically_after_days = 30
#   }
# }

###############################################################
# Outputs
###############################################################

output "mongodb_rotation_lambda_role_arn" {
  description = "ARN of the MongoDB password rotation Lambda IAM role"
  value       = aws_iam_role.mongodb_rotation_lambda.arn
}

output "mongodb_rotation_enabled" {
  description = "MongoDB secret rotation configuration status"
  value       = "IAM role and security group created - Lambda function ready to be deployed"
}
