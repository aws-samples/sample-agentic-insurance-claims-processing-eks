###############################################################
# KMS Key for EKS Encryption
###############################################################

resource "aws_kms_key" "eks" {
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.tags, {
    Name = "${local.name}-eks-secrets"
  })
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${local.name}-eks-secrets"
  target_key_id = aws_kms_key.eks.key_id
}

###############################################################
# EKS Cluster
###############################################################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = local.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access       = var.cluster_endpoint_public_access
  cluster_endpoint_private_access      = var.cluster_endpoint_private_access
  cluster_endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs

  # Cluster logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Cluster encryption
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  # Cluster access entry
  enable_cluster_creator_admin_permissions = true

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    instance_types = ["m6i.large", "m5.large", "m5n.large", "m5zn.large"]

    attach_cluster_primary_security_group = true
    vpc_security_group_ids                = [aws_security_group.additional.id]

    # Production security settings
    iam_role_additional_policies = {
      AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    }

    # EBS encryption
    block_device_mappings = {
      xvda = {
        device_name = "/dev/xvda"
        ebs = {
          volume_size           = 100
          volume_type           = "gp3"
          iops                  = 3000
          throughput            = 150
          encrypted             = true
          delete_on_termination = true
        }
      }
    }

    metadata_options = {
      http_endpoint               = "enabled"
      http_tokens                 = "required"
      http_put_response_hop_limit = 2
      instance_metadata_tags      = "disabled"
    }
  }

  # One managed node group for core components, Karpenter for workloads
  eks_managed_node_groups = {
    general = {
      instance_types = ["m5.large"]
      min_size       = 1
      max_size       = 2
      desired_size   = 2
      capacity_type  = "ON_DEMAND"

      # Taint so only core components run here
      taints = [
        {
          key    = "CriticalAddonsOnly"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]

      # Labels for identification  
      labels = {
        role = "core-components"
      }

      subnet_ids             = module.vpc.private_subnets
      create_launch_template = true
      launch_template_name   = "${local.cluster_name}-general"
    }
  }

  # Cluster add-ons are managed by EKS Blueprints in addons.tf
  cluster_addons = {}

  # Node Security Group - Add Karpenter discovery tag
  node_security_group_tags = {
    "karpenter.sh/discovery" = local.cluster_name
  }

  tags = merge(local.tags, {
    "karpenter.sh/discovery" = local.cluster_name
  })
}

###############################################################
# Security Groups
###############################################################

resource "aws_security_group" "additional" {
  name_prefix = "${local.cluster_name}-additional-"
  vpc_id      = module.vpc.vpc_id
  description = "Additional security group for EKS worker nodes"

  # SSH access from private networks only
  ingress {
    description = "SSH from private networks"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [
      "10.0.0.0/8",
      "172.16.0.0/12",
      "192.168.0.0/16",
    ]
  }

  # HTTPS from ALB
  ingress {
    description = "HTTPS from ALB"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # HTTP from ALB
  ingress {
    description = "HTTP from ALB"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.cluster_name}-additional-sg"
  })
}