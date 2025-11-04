###############################################################
# Karpenter NodePools and EC2NodeClasses
###############################################################

# CPU NodeClass for general workloads
resource "kubectl_manifest" "cpu_nodeclass" {
  yaml_body = <<-YAML
    apiVersion: karpenter.k8s.aws/v1
    kind: EC2NodeClass
    metadata:
      name: cpu-nodeclass
    spec:
      amiSelectorTerms:
        - alias: al2023@latest
      role: ${module.eks_blueprints_addons.karpenter.node_iam_role_name}
      subnetSelectorTerms:
        - tags:
            karpenter.sh/discovery: ${module.eks.cluster_name}
            kubernetes.io/role/internal-elb: "1"
      securityGroupSelectorTerms:
        - id: ${module.eks.cluster_primary_security_group_id}
      instanceStorePolicy: RAID0
      blockDeviceMappings:
        - deviceName: /dev/xvda
          ebs:
            volumeSize: 100Gi
            volumeType: gp3
            encrypted: true
            deleteOnTermination: true
      userData: |
        #!/bin/bash
        /etc/eks/bootstrap.sh ${module.eks.cluster_name}
      tags:
        karpenter.sh/discovery: ${module.eks.cluster_name}
        Name: ${module.eks.cluster_name}-cpu-node
  YAML

  depends_on = [
    module.eks_blueprints_addons
  ]
}

# GPU NodeClass for ML workloads with AL2
resource "kubectl_manifest" "gpu_nodeclass" {
  yaml_body = <<-YAML
    apiVersion: karpenter.k8s.aws/v1
    kind: EC2NodeClass
    metadata:
      name: gpu-nodeclass
    spec:
      # Use Bottlerocket AMI family - optimized for GPU instances
      amiFamily: Bottlerocket
      amiSelectorTerms:
        - alias: bottlerocket@latest
      role: ${module.eks_blueprints_addons.karpenter.node_iam_role_name}
      subnetSelectorTerms:
        - tags:
            karpenter.sh/discovery: ${module.eks.cluster_name}
            kubernetes.io/role/internal-elb: "1"
      securityGroupSelectorTerms:
        - id: ${module.eks.cluster_primary_security_group_id}
      instanceStorePolicy: RAID0
      blockDeviceMappings:
        - deviceName: /dev/xvda
          ebs:
            volumeSize: 100Gi
            volumeType: gp3
            encrypted: true
            deleteOnTermination: true
      userData: |
        #!/bin/bash
        /etc/eks/bootstrap.sh ${module.eks.cluster_name}
      tags:
        karpenter.sh/discovery: ${module.eks.cluster_name}
        Name: ${module.eks.cluster_name}-gpu-node
        NodeType: gpu
  YAML

  depends_on = [
    module.eks_blueprints_addons
  ]
}

# CPU NodePool for general workloads
resource "kubectl_manifest" "cpu_nodepool" {
  yaml_body = <<-YAML
    apiVersion: karpenter.sh/v1
    kind: NodePool
    metadata:
      name: cpu-nodepool
    spec:
      template:
        metadata:
          labels:
            nodepool: cpu
        spec:
          # Remove taints to allow application pods to schedule
          taints: []
          nodeClassRef:
            group: karpenter.k8s.aws
            kind: EC2NodeClass
            name: cpu-nodeclass
          requirements:
            - key: "karpenter.k8s.aws/instance-category"
              operator: In
              values: ["c", "m", "r"]
            - key: "karpenter.k8s.aws/instance-cpu"
              operator: In
              values: ["2", "4", "8", "16", "32"]
            - key: "karpenter.k8s.aws/instance-hypervisor"
              operator: In
              values: ["nitro"]
            - key: "karpenter.k8s.aws/instance-generation"
              operator: Gt
              values: ["2"]
            - key: "kubernetes.io/arch"
              operator: In
              values: ["amd64"]
            - key: "karpenter.sh/capacity-type"
              operator: In
              values: ["spot", "on-demand"]
      limits:
        cpu: 5000
        memory: 5000Gi
      disruption:
        consolidationPolicy: WhenEmpty
        consolidateAfter: 30s
  YAML

  depends_on = [
    kubectl_manifest.cpu_nodeclass
  ]
}

# GPU NodePool for ML workloads
resource "kubectl_manifest" "gpu_nodepool" {
  yaml_body = <<-YAML
    apiVersion: karpenter.sh/v1
    kind: NodePool
    metadata:
      name: gpu-nodepool
    spec:
      template:
        metadata:
          labels:
            nodepool: gpu
        spec:
          # Allow application pods while keeping GPU taints for GPU workloads
          taints:
            - key: "nvidia.com/gpu"
              value: "true"
              effect: "NoSchedule"
          nodeClassRef:
            group: karpenter.k8s.aws
            kind: EC2NodeClass
            name: gpu-nodeclass
          requirements:
            - key: "karpenter.k8s.aws/instance-category"
              operator: In
              values: ["g"]
            - key: "karpenter.k8s.aws/instance-family"
              operator: In
              values: ["g5", "g6"]
            - key: "karpenter.k8s.aws/instance-hypervisor"
              operator: In
              values: ["nitro"]
            - key: "kubernetes.io/arch"
              operator: In
              values: ["amd64"]
            - key: "karpenter.sh/capacity-type"
              operator: In
              values: ["on-demand"]
      limits:
        cpu: 1000
        memory: 1000Gi
      disruption:
        consolidationPolicy: WhenEmpty
        consolidateAfter: 30s
  YAML

  depends_on = [
    kubectl_manifest.gpu_nodeclass
  ]
}
