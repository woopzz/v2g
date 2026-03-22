terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }

  required_version = ">= 1.2"
}

provider "aws" {
  region = "eu-central-1"
}

resource "aws_sqs_queue" "celery" {
  name = "celery"
}

resource "aws_s3_bucket" "files" {
  bucket = "v2g"
}

output "celery_queue_url" {
  value = aws_sqs_queue.celery.url
}
