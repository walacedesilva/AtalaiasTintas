# ================================================================
# Terraform Variables Configuration for Atalaia Tintas Paint Store System  
# ================================================================
#
# This file defines all input variables for the Terraform infrastructure.
# Variables are organized by category for easy management and configuration.
#
# Usage:
#   - Set values in environment-specific .tfvars files
#   - Override via command line: terraform apply -var="variable_name=value"
#   - Use environment variables: TF_VAR_variable_name=value
#
# Environment Examples:
#   - development.tfvars
#   - staging.tfvars  
#   - production.tfvars
#
# Author: Atalaia Tintas DevOps Team
# Version: 1.0.0

# ================================
# General Configuration
# ================================

variable "project_name" {
  description = "Name of the project - used for resource naming and tagging"
  type        = string
  default     = "atalaia-tintas"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = "atalaia-tintas.com"
  
  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid fully qualified domain name."
  }
}

# ================================
# Network Configuration
# ================================

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string 
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "admin_ip_ranges" {
  description = "List of IP ranges allowed to access bastion host and admin interfaces"
  type        = list(string)
  default     = ["0.0.0.0/0"]
  
  validation {
    condition     = length(var.admin_ip_ranges) > 0
    error_message = "At least one admin IP range must be specified."
  }
}

# ================================
# Compute Configuration
# ================================

variable "instance_type" {
  description = "EC2 instance type for web application servers"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition = contains([
      "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge",
      "t4g.micro", "t4g.small", "t4g.medium", "t4g.large", "t4g.xlarge",
      "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge",
      "m6g.large", "m6g.xlarge", "m6g.2xlarge", "m6g.4xlarge",
      "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge",
      "c6g.large", "c6g.xlarge", "c6g.2xlarge", "c6g.4xlarge"
    ], var.instance_type)
    error_message = "Instance type must be a valid EC2 instance type suitable for web applications."
  }
}

variable "root_volume_size" {
  description = "Size of the root EBS volume in GB for EC2 instances"
  type        = number
  default     = 30
  
  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 500
    error_message = "Root volume size must be between 20 and 500 GB."
  }
}

variable "min_instances" {
  description = "Minimum number of instances in the Auto Scaling Group"
  type        = number
  default     = 1
  
  validation {
    condition     = var.min_instances >= 1 && var.min_instances <= 10
    error_message = "Minimum instances must be between 1 and 10."
  }
}

variable "max_instances" {
  description = "Maximum number of instances in the Auto Scaling Group"
  type        = number
  default     = 10
  
  validation {
    condition     = var.max_instances >= var.min_instances && var.max_instances <= 20
    error_message = "Maximum instances must be greater than or equal to minimum instances and not exceed 20."
  }
}

variable "desired_instances" {
  description = "Desired number of instances in the Auto Scaling Group"
  type        = number
  default     = 2
  
  validation {
    condition     = var.desired_instances >= var.min_instances && var.desired_instances <= var.max_instances
    error_message = "Desired instances must be between minimum and maximum instances."
  }
}

# ================================
# Database Configuration  
# ================================

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "atalaia_tintas_db"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]{0,62}$", var.db_name))
    error_message = "Database name must start with a letter, contain only letters, numbers, and underscores, and be 1-63 characters long."
  }
}

variable "db_username" {
  description = "Username for the PostgreSQL database master user"
  type        = string
  default     = "postgres_admin"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]{0,62}$", var.db_username))
    error_message = "Database username must start with a letter, contain only letters, numbers, and underscores, and be 1-63 characters long."
  }
}

variable "postgres_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
  
  validation {
    condition = contains([
      "13.13", "13.14", "13.15",
      "14.9", "14.10", "14.11", 
      "15.3", "15.4", "15.5",
      "16.1", "16.2"
    ], var.postgres_version)
    error_message = "PostgreSQL version must be a supported RDS version."
  }
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for the RDS instance in GB"
  type        = number
  default     = 100
  
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 65536
    error_message = "Database allocated storage must be between 20 and 65536 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS auto-scaling in GB"
  type        = number
  default     = 1000
  
  validation {
    condition     = var.db_max_allocated_storage >= var.db_allocated_storage
    error_message = "Maximum allocated storage must be greater than or equal to allocated storage."
  }
}

variable "db_backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
  
  validation {
    condition     = var.db_backup_retention_days >= 0 && var.db_backup_retention_days <= 35
    error_message = "Backup retention period must be between 0 and 35 days."
  }
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for RDS instance"
  type        = bool
  default     = false
}

variable "db_performance_insights_enabled" {
  description = "Enable Performance Insights for RDS instance"
  type        = bool
  default     = false
}

variable "db_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds (0, 1, 5, 10, 15, 30, 60)"
  type        = number
  default     = 0
  
  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.db_monitoring_interval)
    error_message = "Monitoring interval must be 0, 1, 5, 10, 15, 30, or 60 seconds."
  }
}

# ================================
# Cache Configuration (Redis)
# ================================

variable "redis_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
  
  validation {
    condition = contains([
      "6.2", "7.0", "7.1"
    ], var.redis_version)
    error_message = "Redis version must be a supported ElastiCache version."
  }
}

variable "redis_node_type" {
  description = "ElastiCache node type for Redis cluster"
  type        = string
  default     = "cache.t4g.micro"
  
  validation {
    condition = contains([
      "cache.t3.micro", "cache.t3.small", "cache.t3.medium",
      "cache.t4g.micro", "cache.t4g.small", "cache.t4g.medium",
      "cache.m5.large", "cache.m5.xlarge", "cache.m5.2xlarge",
      "cache.m6g.large", "cache.m6g.xlarge", "cache.m6g.2xlarge",
      "cache.r6g.large", "cache.r6g.xlarge", "cache.r6g.2xlarge"
    ], var.redis_node_type)
    error_message = "Redis node type must be a valid ElastiCache node type."
  }
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in the Redis cluster"
  type        = number
  default     = 1
  
  validation {
    condition     = var.redis_num_cache_nodes >= 1 && var.redis_num_cache_nodes <= 6
    error_message = "Number of Redis cache nodes must be between 1 and 6."
  }
}

variable "redis_snapshot_retention_limit" {
  description = "Number of days to retain Redis snapshots"
  type        = number
  default     = 1
  
  validation {
    condition     = var.redis_snapshot_retention_limit >= 0 && var.redis_snapshot_retention_limit <= 35
    error_message = "Redis snapshot retention limit must be between 0 and 35 days."
  }
}

variable "redis_automatic_failover" {
  description = "Enable automatic failover for Redis cluster"
  type        = bool
  default     = false
}

# ================================
# Storage Configuration
# ================================

variable "backup_retention_days" {
  description = "Number of days to retain backups in S3"
  type        = number
  default     = 30
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 2555
    error_message = "Backup retention must be between 1 and 2555 days (7 years)."
  }
}

variable "media_storage_class" {
  description = "S3 storage class for media files"
  type        = string
  default     = "STANDARD"
  
  validation {
    condition = contains([
      "STANDARD", "STANDARD_IA", "ONEZONE_IA", "REDUCED_REDUNDANCY"
    ], var.media_storage_class)
    error_message = "Media storage class must be a valid S3 storage class."
  }
}

variable "enable_s3_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = false
}

# ================================
# Security Configuration  
# ================================

variable "django_secret_key" {
  description = "Django secret key for cryptographic operations"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.django_secret_key) >= 50
    error_message = "Django secret key must be at least 50 characters long."
  }
}

variable "jwt_secret_key" {
  description = "JWT secret key for token signing"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.jwt_secret_key) >= 32
    error_message = "JWT secret key must be at least 32 characters long."
  }
}

variable "enable_waf" {
  description = "Enable AWS WAF for the Application Load Balancer"
  type        = bool
  default     = false
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS termination"
  type        = string
  default     = ""
  
  validation {
    condition     = var.ssl_certificate_arn == "" || can(regex("^arn:aws:acm:", var.ssl_certificate_arn))
    error_message = "SSL certificate ARN must be a valid ACM certificate ARN or empty."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = false
}

# ================================
# Monitoring Configuration
# ================================

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for RDS and other services"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
  
  validation {
    condition     = var.alert_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address or empty."
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for EC2 instances"
  type        = bool
  default     = false
}

# ================================
# Cost Optimization
# ================================

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization (not recommended for production)"
  type        = bool
  default     = false
}

variable "spot_instance_max_price" {
  description = "Maximum price for spot instances as percentage of on-demand price"
  type        = string
  default     = "0.50"
  
  validation {
    condition     = can(tonumber(var.spot_instance_max_price)) && tonumber(var.spot_instance_max_price) > 0 && tonumber(var.spot_instance_max_price) <= 1
    error_message = "Spot instance max price must be between 0.01 and 1.00."
  }
}

# ================================
# Feature Flags
# ================================

variable "enable_blue_green_deployment" {
  description = "Enable blue-green deployment infrastructure"
  type        = bool
  default     = true
}

variable "enable_cloudfront_cdn" {
  description = "Enable CloudFront CDN for static asset distribution"
  type        = bool
  default     = false
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling for the application tier"
  type        = bool
  default     = true
}

variable "enable_backup_automation" {
  description = "Enable automated backup processes"
  type        = bool
  default     = true
}

# ================================
# Performance Configuration
# ================================

variable "auto_scaling_cooldown" {
  description = "Cooldown period (in seconds) for auto scaling actions"
  type        = number
  default     = 300
  
  validation {
    condition     = var.auto_scaling_cooldown >= 0 && var.auto_scaling_cooldown <= 3600
    error_message = "Auto scaling cooldown must be between 0 and 3600 seconds."
  }
}

variable "health_check_grace_period" {
  description = "Grace period (in seconds) for health check after instance launch"
  type        = number
  default     = 300
  
  validation {
    condition     = var.health_check_grace_period >= 0 && var.health_check_grace_period <= 7200
    error_message = "Health check grace period must be between 0 and 7200 seconds."
  }
}

variable "cpu_scale_up_threshold" {
  description = "CPU utilization threshold (percentage) to trigger scale up"
  type        = number
  default     = 70
  
  validation {
    condition     = var.cpu_scale_up_threshold >= 10 && var.cpu_scale_up_threshold <= 95
    error_message = "CPU scale up threshold must be between 10 and 95 percent."
  }
}

variable "cpu_scale_down_threshold" {
  description = "CPU utilization threshold (percentage) to trigger scale down"
  type        = number
  default     = 30
  
  validation {
    condition     = var.cpu_scale_down_threshold >= 5 && var.cpu_scale_down_threshold <= 50
    error_message = "CPU scale down threshold must be between 5 and 50 percent."
  }
}

# ================================
# Development and Testing
# ================================

variable "enable_debug_mode" {
  description = "Enable debug mode (only for development/staging environments)"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying RDS instance (useful for testing)"
  type        = bool
  default     = true
}

variable "force_destroy_s3_buckets" {
  description = "Allow force destruction of S3 buckets with contents (dangerous!)"
  type        = bool
  default     = false
}