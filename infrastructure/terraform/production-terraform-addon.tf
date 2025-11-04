# Production-Grade Terraform Addon for LangGraph Insurance System

# Use existing LangGraph service role if it exists
data "aws_iam_role" "langgraph_service_role" {
  name = "${local.name}-langgraph-service-role"
}

# IAM Policy for LangGraph Services
resource "aws_iam_policy" "langgraph_service_policy" {
  name        = "${local.name}-langgraph-service-policy"
  description = "IAM policy for LangGraph insurance services"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.langgraph_storage.arn,
          "${aws_s3_bucket.langgraph_storage.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.langgraph_secrets.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.tags
}


# S3 Bucket for LangGraph Storage
resource "aws_s3_bucket" "langgraph_storage" {
  bucket = "${local.name}-langgraph-storage-${random_string.bucket_suffix.result}"

  tags = local.tags
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "langgraph_storage_versioning" {
  bucket = aws_s3_bucket.langgraph_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "langgraph_storage_encryption" {
  bucket = aws_s3_bucket.langgraph_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "langgraph_storage_pab" {
  bucket = aws_s3_bucket.langgraph_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Secrets Manager for LangGraph Configuration
resource "aws_secretsmanager_secret" "langgraph_secrets" {
  name        = "${local.name}-langgraph-secrets"
  description = "Secrets for LangGraph insurance system"

  tags = merge(local.tags, {
    ManagedBy = "terraform"
  })
}

resource "aws_secretsmanager_secret_version" "langgraph_secrets_version" {
  secret_id = aws_secretsmanager_secret.langgraph_secrets.id
  secret_string = jsonencode({
    redis_password = random_password.redis_password.result
    api_key        = random_password.api_key.result
    encryption_key = random_password.encryption_key.result
  })
}

resource "random_password" "redis_password" {
  length  = 32
  special = true
}

resource "random_password" "api_key" {
  length  = 64
  special = false
}

resource "random_password" "encryption_key" {
  length  = 32
  special = false
}

# CloudWatch Log Group for LangGraph
resource "aws_cloudwatch_log_group" "langgraph_logs" {
  name              = "/aws/eks/${local.cluster_name}/langgraph"
  retention_in_days = 30

  tags = local.tags
}

# Security Group for LangGraph Services
resource "aws_security_group" "langgraph_services" {
  name_prefix = "${local.name}-langgraph-services"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for LangGraph insurance services"

  ingress {
    description = "HTTP from ALB"
    from_port   = 8000
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  ingress {
    description = "Redis"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  ingress {
    description = "Ollama LLM"
    from_port   = 11434
    to_port     = 11434
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name}-langgraph-services"
  })
}

# Time delay to ensure Karpenter is ready
resource "time_sleep" "wait_for_karpenter" {
  depends_on = [
    module.eks,
    module.eks_blueprints_addons
  ]
  create_duration = "120s"
}

# Enhanced Karpenter Node Pool for GPU Workloads
resource "kubectl_manifest" "karpenter_nodepool_gpu" {
  depends_on = [
    time_sleep.wait_for_karpenter
  ]

  yaml_body = <<-YAML
    apiVersion: karpenter.sh/v1
    kind: NodePool
    metadata:
      name: gpu-nodepool
    spec:
      template:
        metadata:
          labels:
            workload-type: "gpu"
        spec:
          requirements:
            - key: kubernetes.io/arch
              operator: In
              values: ["amd64"]
            - key: karpenter.sh/capacity-type
              operator: In
              values: ["on-demand"]
            - key: node.kubernetes.io/instance-type
              operator: In
              values: ["g5.xlarge", "g5.2xlarge", "g5.4xlarge", "g6.xlarge", "g6.2xlarge"]
          nodeClassRef:
            group: karpenter.k8s.aws
            kind: EC2NodeClass
            name: gpu-nodeclass
          taints:
            - key: nvidia.com/gpu
              value: "true"
              effect: NoSchedule
      limits:
        cpu: 1000
        memory: 1000Gi
      disruption:
        consolidationPolicy: WhenEmpty
        consolidateAfter: 30s
  YAML
}

resource "kubectl_manifest" "karpenter_nodeclass_gpu" {
  depends_on = [
    time_sleep.wait_for_karpenter
  ]

  yaml_body = <<-YAML
    apiVersion: karpenter.k8s.aws/v1
    kind: EC2NodeClass
    metadata:
      name: gpu-nodeclass
    spec:
      amiFamily: Bottlerocket
      amiSelectorTerms:
        - alias: bottlerocket@latest
      role: "${module.eks_blueprints_addons.karpenter.node_iam_role_name}"
      subnetSelectorTerms:
        - tags:
            karpenter.sh/discovery: "${local.cluster_name}"
            kubernetes.io/role/internal-elb: "1"
      securityGroupSelectorTerms:
        - tags:
            karpenter.sh/discovery: "${local.cluster_name}"
      tags:
        Name: "${local.name}-gpu-node"
        NodeType: "gpu"
  YAML
}

# Application Load Balancer for Production
resource "aws_lb" "langgraph_alb" {
  name               = "langgraph-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.langgraph_alb.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = false

  tags = local.tags
}

resource "aws_security_group" "langgraph_alb" {
  name_prefix = "${local.name}-langgraph-alb"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for LangGraph ALB"

  ingress {
    description = "HTTP (will redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS (TLS 1.2+)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name}-langgraph-alb"
  })
}

# Output important values
output "langgraph_service_role_arn" {
  description = "ARN of the LangGraph service IAM role"
  value       = data.aws_iam_role.langgraph_service_role.arn
}

output "langgraph_storage_bucket" {
  description = "Name of the LangGraph S3 storage bucket"
  value       = aws_s3_bucket.langgraph_storage.bucket
}

output "langgraph_secrets_arn" {
  description = "ARN of the LangGraph secrets in Secrets Manager"
  value       = aws_secretsmanager_secret.langgraph_secrets.arn
}

output "langgraph_alb_dns" {
  description = "DNS name of the LangGraph Application Load Balancer"
  value       = aws_lb.langgraph_alb.dns_name
}
