output "app_public_ip" {
  value = aws_instance.app.public_ip
}

output "celery_queue_url" {
  value = aws_sqs_queue.celery.url
}
