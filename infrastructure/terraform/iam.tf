###############################################################
# EKS Cluster Service Role
###############################################################

data "aws_iam_policy_document" "cluster_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

# Use existing cluster role if it exists
data "aws_iam_role" "cluster_role" {
  name = "${local.name}-cluster-role"
}

###############################################################
# EKS Node Group Role
###############################################################

data "aws_iam_policy_document" "node_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# Use existing node role if it exists
data "aws_iam_role" "node_role" {
  name = "${local.name}-node-role"
}

# Note: EBS CSI Driver role is handled by IRSA module in addons.tf