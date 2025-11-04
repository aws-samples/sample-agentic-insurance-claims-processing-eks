terraform {
  backend "s3" {
    bucket = "agentic-eks-terraform-state"
    key    = "insurance-demo/terraform.tfstate"
    region = "us-west-2"
  }
}
