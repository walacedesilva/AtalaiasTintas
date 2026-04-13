# ================================================================
# Terraform Outputs Configuration for Atalaia Tintas Paint Store System
# ================================================================
#
# This file defines outputs from the Terraform infrastructure that can be
# used by other systems, CI/CD pipelines, or for operational reference.
#
# Output categories:
# - Network information (VPC, subnets, security groups)
# - Compute resources (instances, load balancers)  
# - Database connection details
# - Storage resources (S3 buckets)
# - Monitoring and logging endpoints
# - Security credentials and keys
#
# Usage:
#   terraform output                    # Show all outputs
#   terraform output vpc_id            # Show specific output
#   terraform output -json            # JSON format for automation
#
# Author: Atalaia Tintas DevOps Team
# Version: 1.0.0

# ================================
# Network Information
# ================================

output "vpc_id" {
  description = "ID of the VPC created for the infrastructure"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  description = "List of IDs of the private application subnets"
  value       = aws_subnet.private_app[*].id
}

output "private_db_subnet_ids" {
  description = "List of IDs of the private database subnets"
  value       = aws_subnet.private_db[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "List of IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = local.azs
}

# ================================
# Security Groups
# ================================

output "alb_security_group_id" {
  description = "ID of the Application Load Balancer security group"
  value       = aws_security_group.alb.id
}

output "web_app_security_group_id" {
  description = "ID of the web application security group"
  value       = aws_security_group.web_app.id
}

output "database_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.database.id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

output "bastion_security_group_id" {
  description = "ID of the bastion host security group"
  value       = aws_security_group.bastion.id
}

# ================================
# Load Balancer and Compute
# ================================

output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "load_balancer_dns" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_zone_id" {
  description = "Canonical hosted zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "blue_target_group_arn" {
  description = "ARN of the blue target group for blue-green deployments"
  value       = aws_lb_target_group.blue.arn
}

output "green_target_group_arn" {
  description = "ARN of the green target group for blue-green deployments"
  value       = aws_lb_target_group.green.arn
}

output "auto_scaling_group_name" {
  description = "Name of the Auto Scaling Group"
  value       = aws_autoscaling_group.web_app.name
}

output "auto_scaling_group_arn" {
  description = "ARN of the Auto Scaling Group"
  value       = aws_autoscaling_group.web_app.arn
}

output "launch_template_id" {
  description = "ID of the launch template"
  value       = aws_launch_template.web_app.id
}

output "launch_template_version" {
  description = "Latest version of the launch template"
  value       = aws_launch_template.web_app.latest_version
}

# ================================
# Bastion Host
# ================================

output "bastion_instance_id" {
  description = "ID of the bastion host instance"
  value       = aws_instance.bastion.id
}

output "bastion_public_ip" {
  description = "Public IP address of the bastion host"
  value       = aws_eip.bastion.public_ip
}

output "bastion_private_ip" {
  description = "Private IP address of the bastion host"
  value       = aws_instance.bastion.private_ip
}

# ================================
# Database Information
# ================================

output "database_instance_id" {
  description = "ID of the RDS database instance"
  value       = aws_db_instance.main.id
}

output "database_endpoint" {
  description = "RDS instance endpoint for database connections"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "Name of the database"
  value       = aws_db_instance.main.db_name
}

output "database_username" {
  description = "Username for the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "database_arn" {
  description = "ARN of the RDS database instance"
  value       = aws_db_instance.main.arn
}

output "database_availability_zone" {
  description = "Availability zone of the RDS instance"
  value       = aws_db_instance.main.availability_zone
}

output "database_backup_retention_period" {
  description = "Backup retention period of the RDS instance"
  value       = aws_db_instance.main.backup_retention_period
}

output "database_backup_window" {
  description = "Backup window of the RDS instance"
  value       = aws_db_instance.main.backup_window
}

output "database_maintenance_window" {
  description = "Maintenance window of the RDS instance"
  value       = aws_db_instance.main.maintenance_window
}

# ================================
# Cache Information (Redis)
# ================================

output "redis_cluster_id" {
  description = "ID of the Redis cluster"
  value       = aws_elasticache_replication_group.main.replication_group_id
}

output "redis_endpoint" {
  description = "Redis cluster endpoint for connections"
  value       = aws_elasticache_replication_group.main.configuration_endpoint_address != "" ? aws_elasticache_replication_group.main.configuration_endpoint_address : aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_arn" {
  description = "ARN of the Redis cluster"
  value       = aws_elasticache_replication_group.main.arn
}

# ================================
# Storage Resources (S3)
# ================================

output "media_bucket_name" {
  description = "Name of the S3 bucket for media storage"
  value       = aws_s3_bucket.media.id
}

output "media_bucket_arn" {
  description = "ARN of the S3 bucket for media storage"
  value       = aws_s3_bucket.media.arn
}

output "media_bucket_domain_name" {
  description = "Domain name of the S3 bucket for media storage"
  value       = aws_s3_bucket.media.bucket_domain_name
}

output "backup_bucket_name" {
  description = "Name of the S3 bucket for backups"
  value       = aws_s3_bucket.backups.id
}

output "backup_bucket_arn" {
  description = "ARN of the S3 bucket for backups"
  value       = aws_s3_bucket.backups.arn
}

output "alb_logs_bucket_name" {
  description = "Name of the S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.id
}

output "alb_logs_bucket_arn" {
  description = "ARN of the S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.arn
}

# ================================
# IAM Resources
# ================================

output "ec2_instance_role_arn" {
  description = "ARN of the EC2 instance IAM role"
  value       = aws_iam_role.ec2_instance.arn
}

output "ec2_instance_role_name" {
  description = "Name of the EC2 instance IAM role"
  value       = aws_iam_role.ec2_instance.name
}

output "ec2_instance_profile_arn" {
  description = "ARN of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_instance.arn
}

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_instance.name
}

# ================================
# Security and Secrets
# ================================

output "key_pair_name" {
  description = "Name of the EC2 Key Pair"
  value       = aws_key_pair.main.key_name
}

output "ssh_private_key_secret_arn" {
  description = "ARN of the secret containing SSH private key"
  value       = aws_secretsmanager_secret.ssh_private_key.arn
  sensitive   = true
}

output "database_credentials_secret_arn" {
  description = "ARN of the secret containing database credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
  sensitive   = true
}

output "app_secrets_secret_arn" {
  description = "ARN of the secret containing application secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
  sensitive   = true
}

# ================================
# Monitoring and Logging
# ================================

output "cloudwatch_log_group_app" {
  description = "Name of the CloudWatch log group for application logs"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "cloudwatch_log_group_nginx" {
  description = "Name of the CloudWatch log group for Nginx logs"
  value       = aws_cloudwatch_log_group.nginx_logs.name
}

output "sns_alerts_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "cloudwatch_alarms" {
  description = "List of CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.high_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.database_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.scale_up_alarm.alarm_name,
    aws_cloudwatch_metric_alarm.scale_down_alarm.alarm_name
  ]
}

# ================================
# Environment Information
# ================================

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# ================================
# Resource Tags
# ================================

output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# ================================
# Connection Information for Applications
# ================================

output "application_connection_info" {
  description = "Connection information for applications and CI/CD pipelines"
  value = {
    vpc_id                    = aws_vpc.main.id
    private_app_subnet_ids    = aws_subnet.private_app[*].id
    web_app_security_group_id = aws_security_group.web_app.id
    database_endpoint         = aws_db_instance.main.endpoint
    database_port            = aws_db_instance.main.port
    database_name            = aws_db_instance.main.db_name
    redis_endpoint           = aws_elasticache_replication_group.main.configuration_endpoint_address != "" ? aws_elasticache_replication_group.main.configuration_endpoint_address : aws_elasticache_replication_group.main.primary_endpoint_address
    redis_port               = aws_elasticache_replication_group.main.port
    media_bucket_name        = aws_s3_bucket.media.id
    backup_bucket_name       = aws_s3_bucket.backups.id
    load_balancer_dns        = aws_lb.main.dns_name
    bastion_public_ip        = aws_eip.bastion.public_ip
  }
  sensitive = true
}

# ================================
# Deployment Information
# ================================

output "deployment_info" {
  description = "Information needed for deployment processes"
  value = {
    auto_scaling_group_name   = aws_autoscaling_group.web_app.name
    blue_target_group_arn     = aws_lb_target_group.blue.arn
    green_target_group_arn    = aws_lb_target_group.green.arn
    launch_template_id        = aws_launch_template.web_app.id
    alb_listener_arn          = aws_lb_listener.main.arn
    instance_profile_name     = aws_iam_instance_profile.ec2_instance.name
    key_pair_name            = aws_key_pair.main.key_name
  }
}

# ================================
# Cost Optimization Information
# ================================

output "cost_optimization_info" {
  description = "Information for cost analysis and optimization"
  value = {
    instance_type             = var.instance_type
    min_instances            = var.min_instances
    max_instances            = var.max_instances
    desired_instances        = var.desired_instances
    db_instance_class        = local.db_instance_class
    redis_node_type          = local.redis_node_type
    backup_retention_days    = var.backup_retention_days
    log_retention_days       = var.log_retention_days
  }
}