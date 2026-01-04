# Webis Multi-Region Deployment
# This is a conceptual Terraform configuration for deploying Webis across multiple regions.

variable "regions" {
  type    = list(string)
  default = ["us-east-1", "eu-central-1", "ap-northeast-1"]
}

module "webis_cluster" {
  source = "./modules/k8s_cluster"
  count  = length(var.regions)
  region = var.regions[count.index]
}

# Global Load Balancer (e.g., AWS Global Accelerator)
resource "aws_globalaccelerator_accelerator" "webis_global" {
  name            = "webis-global-api"
  ip_address_type = "IPV4"
  enabled         = true
}

resource "aws_globalaccelerator_listener" "webis_listener" {
  accelerator_arn = aws_globalaccelerator_accelerator.webis_global.id
  protocol        = "TCP"
  port_range {
    from_port = 80
    to_port   = 80
  }
}

# Endpoint groups for each region
resource "aws_globalaccelerator_endpoint_group" "webis_endpoints" {
  count = length(var.regions)
  listener_arn = aws_globalaccelerator_listener.webis_listener.id
  endpoint_region = var.regions[count.index]
  
  endpoint_configuration {
    endpoint_id = module.webis_cluster[count.index].load_balancer_arn
    weight      = 100
  }
}
