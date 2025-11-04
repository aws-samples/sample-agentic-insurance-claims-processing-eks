###############################################################
# Storage Classes and Persistent Volume Configuration
###############################################################

# GP3 Storage Class for high-performance workloads
resource "kubectl_manifest" "gp3_storage_class" {
  yaml_body = <<-YAML
    apiVersion: storage.k8s.io/v1
    kind: StorageClass
    metadata:
      name: gp3
      annotations:
        storageclass.kubernetes.io/is-default-class: "true"
    provisioner: ebs.csi.aws.com
    parameters:
      type: gp3
      iops: "3000"
      throughput: "125"
      encrypted: "true"
    volumeBindingMode: WaitForFirstConsumer
    allowVolumeExpansion: true
    reclaimPolicy: Delete
  YAML

  depends_on = [
    module.eks_blueprints_addons
  ]
}

# GP3 High Performance Storage Class for databases and high-IOPS workloads
resource "kubectl_manifest" "gp3_high_performance_storage_class" {
  yaml_body = <<-YAML
    apiVersion: storage.k8s.io/v1
    kind: StorageClass
    metadata:
      name: gp3-high-performance
    provisioner: ebs.csi.aws.com
    parameters:
      type: gp3
      iops: "16000"
      throughput: "1000"
      encrypted: "true"
    volumeBindingMode: WaitForFirstConsumer
    allowVolumeExpansion: true
    reclaimPolicy: Delete
  YAML

  depends_on = [
    module.eks_blueprints_addons
  ]
}

# GP3 Retain Storage Class for critical data
resource "kubectl_manifest" "gp3_retain_storage_class" {
  yaml_body = <<-YAML
    apiVersion: storage.k8s.io/v1
    kind: StorageClass
    metadata:
      name: gp3-retain
    provisioner: ebs.csi.aws.com
    parameters:
      type: gp3
      iops: "3000"
      throughput: "125"
      encrypted: "true"
    volumeBindingMode: WaitForFirstConsumer
    allowVolumeExpansion: true
    reclaimPolicy: Retain
  YAML

  depends_on = [
    module.eks_blueprints_addons
  ]
}

# Remove default GP2 storage class
resource "kubectl_manifest" "remove_default_gp2" {
  yaml_body = <<-YAML
    apiVersion: storage.k8s.io/v1
    kind: StorageClass
    metadata:
      name: gp2
      annotations:
        storageclass.kubernetes.io/is-default-class: "false"
    provisioner: kubernetes.io/aws-ebs
    parameters:
      type: gp2
      fsType: ext4
    volumeBindingMode: WaitForFirstConsumer
    allowVolumeExpansion: true
    reclaimPolicy: Delete
  YAML

  depends_on = [
    kubectl_manifest.gp3_storage_class
  ]
}
