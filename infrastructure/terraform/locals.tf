###############################################################
# Local Values
###############################################################

locals {
  # Shortened naming convention: {project}-{environment}
  name = "${var.project_name}-${var.environment}"

  # EKS cluster name - use existing cluster name to prevent recreation
  cluster_name = "agentic-eks-cluster"


  # Availability zones
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  # Common tags for all resources
  tags = {
    Project     = var.project_name
    Environment = var.environment
    Region      = var.region
    ManagedBy   = "terraform"
    Purpose     = "insurance-agentic-ai"
    Owner       = "platform-team"
    CostCenter  = "ai-ml"
    UniqueId    = random_string.cluster_suffix.result

    # EKS and Karpenter discovery tags
    "kubernetes.io/cluster/${local.cluster_name}" = "owned"
    "karpenter.sh/discovery"                      = local.cluster_name
  }


}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}


# Random suffix for unique naming
resource "random_string" "cluster_suffix" {
  length  = 4
  special = false
  upper   = false
  numeric = true
  lower   = true
}
