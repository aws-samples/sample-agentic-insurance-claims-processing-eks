###############################################################
# ECR Public Authorization Token
###############################################################

data "aws_ecrpublic_authorization_token" "token" {
  provider = aws.virginia
}

###############################################################
# IRSA for EBS CSI Driver
###############################################################

module "ebs_csi_driver_irsa" {
  source                = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version               = "~> 5.49"
  role_name_prefix      = format("%s-%s-", local.name, "ebs-csi-driver")
  attach_ebs_csi_policy = true
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
  tags = local.tags
}

###############################################################
# EKS Blueprints Addons
###############################################################

module "eks_blueprints_addons" {
  source  = "aws-ia/eks-blueprints-addons/aws"
  version = "~> 1.20"

  cluster_name      = module.eks.cluster_name
  cluster_endpoint  = module.eks.cluster_endpoint
  cluster_version   = module.eks.cluster_version
  oidc_provider_arn = module.eks.oidc_provider_arn

  #---------------------------------------
  # Amazon EKS Managed Add-ons
  #---------------------------------------
  eks_addons = {
    aws-ebs-csi-driver = {
      service_account_role_arn = module.ebs_csi_driver_irsa.iam_role_arn
    }
    coredns = {
      preserve = true
    }
    vpc-cni = {
      preserve = true
    }
    kube-proxy = {
      preserve = true
    }
  }

  #---------------------------------------
  # Metrics Server
  #---------------------------------------
  enable_metrics_server = true
  metrics_server = {
    values = [
      <<-EOT
      resources:
        limits:
          cpu: 200m
          memory: 256Mi
        requests:
          cpu: 100m
          memory: 128Mi
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
        capabilities:
          drop:
          - ALL
      EOT
    ]
  }

  #---------------------------------------
  # Cluster Autoscaler - Completely disabled when using Karpenter
  #---------------------------------------
  enable_cluster_autoscaler = false

  #---------------------------------------
  # Karpenter Autoscaler
  #---------------------------------------
  enable_karpenter                  = true
  karpenter_enable_spot_termination = true
  karpenter_node = {
    iam_role_additional_policies = {
      AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    }
  }
  karpenter = {
    chart_version       = "1.7.1"
    repository_username = data.aws_ecrpublic_authorization_token.token.user_name
    repository_password = data.aws_ecrpublic_authorization_token.token.password
    source_policy_documents = [
      data.aws_iam_policy_document.karpenter_controller_policy.json
    ]
    values = [
      <<-EOT
      # Remove CriticalAddonsOnly taint and nodeSelector to allow application pods
      settings:
        # Only manage nodes that Karpenter created
        clusterName: ${module.eks.cluster_name}
        # Disable disruption of nodes not created by Karpenter
        featureGates:
          spotToSpotConsolidation: false
      EOT
    ]
  }

  #---------------------------------------
  # AWS Load Balancer Controller
  #---------------------------------------
  enable_aws_load_balancer_controller = true
  aws_load_balancer_controller = {
    chart_version   = "1.8.1"
    wait            = false # Disable wait to prevent timeout
    timeout         = 600   # Reduced timeout to 10 minutes
    atomic          = false # Disable atomic to allow partial installation
    cleanup_on_fail = false # Keep resources for debugging
    max_history     = 3
    set = [
      {
        name  = "enableServiceMutatorWebhook"
        value = "false"
      },
      {
        name  = "resources.limits.cpu"
        value = "200m" # Reduced CPU limits
      },
      {
        name  = "resources.limits.memory"
        value = "512Mi" # Reduced memory limits
      },
      {
        name  = "resources.requests.cpu"
        value = "100m" # Reduced CPU requests
      },
      {
        name  = "resources.requests.memory"
        value = "256Mi" # Reduced memory requests
      },
      {
        name  = "replicaCount"
        value = "1"
      },
      {
        name  = "podDisruptionBudget.enabled"
        value = "false"
      },
      {
        name  = "nodeSelector.kubernetes\\.io/os"
        value = "linux"
      },
      {
        name  = "serviceAccount.create"
        value = "true"
      },
      {
        name  = "region"
        value = "us-west-2" # Explicitly set region
      },
      {
        name  = "vpcId"
        value = module.vpc.vpc_id # Explicitly set VPC ID
      }
    ]
  }

  #---------------------------------------
  # External Secrets Operator
  #---------------------------------------
  enable_external_secrets = true
  external_secrets = {
    chart_version = "0.11.0"
    set = [
      {
        name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
        value = module.external_secrets_irsa.iam_role_arn
      }
    ]
  }

  #---------------------------------------
  # CloudWatch metrics for EKS
  #---------------------------------------
  enable_aws_cloudwatch_metrics = var.enable_cloudwatch_metrics

  #---------------------------------------
  # AWS for FluentBit - Logging
  #---------------------------------------
  enable_aws_for_fluentbit = var.enable_fluentbit_logging
  aws_for_fluentbit_cw_log_group = {
    create            = false # Use existing log group
    use_name_prefix   = false
    name              = "/${local.name}/aws-fluentbit-logs"
    retention_in_days = 30
  }
  aws_for_fluentbit = {
    s3_bucket_arns = var.enable_fluentbit_logging ? [
      module.s3_bucket[0].s3_bucket_arn,
      "${module.s3_bucket[0].s3_bucket_arn}/*"
    ] : []
  }

  #---------------------------------------
  # Prometheus and Grafana Stack
  #---------------------------------------
  enable_kube_prometheus_stack = var.enable_prometheus_grafana
  kube_prometheus_stack = {
    chart_version = "77.11.1"
    set_sensitive = var.enable_prometheus_grafana ? [
      {
        name  = "grafana.adminPassword"
        value = data.aws_secretsmanager_secret_version.admin_password_version[0].secret_string
      }
    ] : []
  }

  tags = local.tags
}

# Removed data_addons module - NodePools are now created directly in karpenter-nodepools.tf

#---------------------------------------------------------------
# Karpenter Node instance role Access Entry
#---------------------------------------------------------------
resource "aws_eks_access_entry" "karpenter_nodes" {
  cluster_name  = module.eks.cluster_name
  principal_arn = module.eks_blueprints_addons.karpenter.node_iam_role_arn
  type          = "EC2_LINUX"

  depends_on = [
    module.eks_blueprints_addons
  ]
}

#---------------------------------------------------------------
# Karpenter Controller Additional IAM Policy
#---------------------------------------------------------------
data "aws_iam_policy_document" "karpenter_controller_policy" {
  statement {
    actions = [
      "ec2:RunInstances",
      "ec2:CreateLaunchTemplate",
    ]
    resources = ["*"]
    effect    = "Allow"
    sid       = "KarpenterControllerAdditionalPolicy"
  }
}

###############################################################
# NVIDIA Device Plugin for GPU Support
###############################################################

resource "kubectl_manifest" "nvidia_device_plugin" {
  count = var.enable_nvidia_device_plugin ? 1 : 0

  yaml_body = <<-YAML
    apiVersion: apps/v1
    kind: DaemonSet
    metadata:
      name: nvidia-device-plugin-daemonset
      namespace: kube-system
      labels:
        k8s-app: nvidia-device-plugin
    spec:
      selector:
        matchLabels:
          name: nvidia-device-plugin-ds
      updateStrategy:
        type: RollingUpdate
      template:
        metadata:
          labels:
            name: nvidia-device-plugin-ds
        spec:
          tolerations:
          - key: nvidia.com/gpu
            operator: Exists
            effect: NoSchedule
          - key: "CriticalAddonsOnly"
            operator: "Exists"
          - key: "kubernetes.io/arch"
            operator: "Equal"
            value: "amd64"
            effect: "NoSchedule"
          nodeSelector:
            kubernetes.io/arch: amd64
          priorityClassName: "system-node-critical"
          containers:
          - image: nvcr.io/nvidia/k8s-device-plugin:v0.17.4
            name: nvidia-device-plugin-ctr
            args: ["--fail-on-init-error=false"]
            securityContext:
              allowPrivilegeEscalation: false
              capabilities:
                drop: ["ALL"]
            volumeMounts:
              - name: device-plugin
                mountPath: /var/lib/kubelet/device-plugins
          volumes:
            - name: device-plugin
              hostPath:
                path: /var/lib/kubelet/device-plugins
  YAML

  depends_on = [module.eks]
}

###############################################################
# S3 bucket for Application Logs and Data Storage
###############################################################

module "s3_bucket" {
  count = var.enable_s3_bucket ? 1 : 0

  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 4.2"

  bucket_prefix = "${local.name}-app-data-"

  # For demo only - please evaluate for your environment
  force_destroy = true

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = local.tags
}

# Creating S3 bucket folders for different purposes
resource "aws_s3_object" "app_logs" {
  count = var.enable_s3_bucket ? 1 : 0

  bucket       = module.s3_bucket[0].s3_bucket_id
  key          = "application-logs/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "data_storage" {
  count = var.enable_s3_bucket ? 1 : 0

  bucket       = module.s3_bucket[0].s3_bucket_id
  key          = "data-storage/"
  content_type = "application/x-directory"
}

###############################################################
# Grafana Admin Credentials (only if Prometheus/Grafana enabled)
###############################################################

resource "random_password" "grafana" {
  count = var.enable_prometheus_grafana ? 1 : 0

  length  = 16
  special = true
}

resource "aws_secretsmanager_secret" "grafana" {
  count = var.enable_prometheus_grafana ? 1 : 0

  name                    = "${local.name}-grafana-${formatdate("YYYYMMDD-hhmmss", timestamp())}"
  recovery_window_in_days = 0 # Set to zero for demo to force delete during Terraform destroy
}

resource "aws_secretsmanager_secret_version" "grafana" {
  count = var.enable_prometheus_grafana ? 1 : 0

  secret_id     = aws_secretsmanager_secret.grafana[0].id
  secret_string = random_password.grafana[0].result
}

data "aws_secretsmanager_secret_version" "admin_password_version" {
  count = var.enable_prometheus_grafana ? 1 : 0

  secret_id  = aws_secretsmanager_secret.grafana[0].id
  depends_on = [aws_secretsmanager_secret_version.grafana]
}