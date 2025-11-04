###############################################################
# General Variables
###############################################################

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "agentic-eks"
}

###############################################################
# VPC Variables
###############################################################

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "enable_nat_gateway" {
  description = "Should be true to provision NAT Gateways for each of your private networks"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Should be true to provision a single shared NAT Gateway across all of your private networks"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Should be true to enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Should be true to enable DNS support in the VPC"
  type        = bool
  default     = true
}

###############################################################
# EKS Variables
###############################################################

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "agentic-eks-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.31"
}

variable "cluster_endpoint_public_access" {
  description = "Indicates whether or not the Amazon EKS public API server endpoint is enabled"
  type        = bool
  default     = true
}

variable "cluster_endpoint_private_access" {
  description = "Indicates whether or not the Amazon EKS private API server endpoint is enabled"
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "List of CIDR blocks which can access the Amazon EKS public API server endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

###############################################################
# ACM Certificate Variables
###############################################################

variable "create_acm_certificate" {
  description = "Whether to create an ACM certificate for the ALB"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for ACM certificate (e.g., claims.example.com)"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for ACM certificate validation"
  type        = string
  default     = ""
}

###############################################################
# Node Group Variables
###############################################################

###############################################################
# Addon Variables
###############################################################

variable "cluster_addons" {
  description = "Map of cluster addon configurations to enable for the cluster. Addon name can be the map keys or set with `name`"
  type        = any
  default     = {}
}

variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler for automatic node scaling"
  type        = bool
  default     = false
}

variable "enable_karpenter" {
  description = "Enable Karpenter for advanced autoscaling"
  type        = bool
  default     = false
}

variable "enable_nvidia_device_plugin" {
  description = "Enable NVIDIA device plugin for GPU support"
  type        = bool
  default     = true
}


variable "enable_cloudwatch_metrics" {
  description = "Enable CloudWatch Container Insights metrics"
  type        = bool
  default     = true
}

variable "enable_fluentbit_logging" {
  description = "Enable AWS for Fluent Bit logging"
  type        = bool
  default     = false
}

variable "enable_prometheus_grafana" {
  description = "Enable Prometheus and Grafana monitoring stack"
  type        = bool
  default     = false
}

variable "enable_s3_bucket" {
  description = "Enable S3 bucket for application data and logs"
  type        = bool
  default     = true
}

###############################################################
# Tags
###############################################################