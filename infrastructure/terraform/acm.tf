###############################################################
# ACM Certificate for ALB HTTPS
###############################################################

# ACM Certificate for custom domain (optional)
resource "aws_acm_certificate" "alb_certificate" {
  count = var.create_acm_certificate ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}" # Support subdomains like www.claims.example.com
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.tags, {
    Name = "${local.name}-alb-certificate"
  })
}

# Route53 DNS validation records
resource "aws_route53_record" "cert_validation" {
  for_each = var.create_acm_certificate ? {
    for dvo in aws_acm_certificate.alb_certificate[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "alb_certificate" {
  count = var.create_acm_certificate ? 1 : 0

  certificate_arn         = aws_acm_certificate.alb_certificate[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  timeouts {
    create = "10m"
  }
}

###############################################################
# Self-Signed Certificate for Demo/Testing (when no custom domain)
###############################################################

# Note: For demo purposes without a custom domain, use AWS ALB's default certificate
# or create a self-signed cert via kubectl/openssl for testing
# Production deployments should always use ACM with a valid domain

###############################################################
# Outputs
###############################################################

output "acm_certificate_arn" {
  description = "ARN of the ACM certificate for ALB"
  value       = var.create_acm_certificate ? aws_acm_certificate.alb_certificate[0].arn : "No certificate created - set create_acm_certificate=true"
}

output "acm_certificate_status" {
  description = "Status of ACM certificate validation"
  value       = var.create_acm_certificate ? aws_acm_certificate.alb_certificate[0].status : "N/A"
}

output "domain_name" {
  description = "Domain name for the ACM certificate"
  value       = var.create_acm_certificate ? var.domain_name : "No custom domain configured"
}
