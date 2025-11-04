###############################################################
# LangGraph Agentic Insurance System Configuration
###############################################################

# Project Configuration
project_name = "insurance"
environment  = "production"
region       = "us-west-2"

# EKS Cluster Configuration
cluster_name    = "agentic"
cluster_version = "1.33"

###############################################################
# VPC Configuration
###############################################################

vpc_cidr = "10.0.0.0/16"

# Private subnets (3 subnets across 3 AZs)
private_subnet_cidrs = [
  "10.0.1.0/24",
  "10.0.2.0/24",
  "10.0.3.0/24"
]

# Public subnets (3 subnets across 3 AZs)
public_subnet_cidrs = [
  "10.0.101.0/24",
  "10.0.102.0/24",
  "10.0.103.0/24"
]

# NAT Gateway configuration
enable_nat_gateway = true
single_nat_gateway = false # Multi-AZ for production reliability

###############################################################
# Security Configuration
###############################################################

# API endpoint access
cluster_endpoint_public_access       = true
cluster_endpoint_private_access      = true
cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"] # Restrict in production

###############################################################
# Addon Configuration
###############################################################

cluster_addons = {
  coredns = {
    most_recent = true
  }
  kube-proxy = {
    most_recent = true
  }
  vpc-cni = {
    most_recent = true
  }
  aws-ebs-csi-driver = {
    most_recent = true
  }
}

# Core addons for LangGraph system
enable_nvidia_device_plugin = true  # GPU support for LLM inference
enable_cluster_autoscaler   = false # Disabled when using Karpenter
enable_cloudwatch_metrics   = true  # Production monitoring
enable_s3_bucket            = true  # Storage for models and data

# Advanced addons
enable_karpenter          = true  # Advanced autoscaling for LangGraph workloads
enable_fluentbit_logging  = true  # Production logging
enable_prometheus_grafana = false # Optional monitoring stack
