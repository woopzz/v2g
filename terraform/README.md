[What is Infrastructure as Code with Terraform?](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code)

### Generate new SSH key

```bash
ssh-keygen -t ed25519 -f .ssh/v2g
```

### Terraform CLI commands

```bash
# This is the first command you should run after writing a new Terraform configuration or cloning an existing configuration from version control.
terraform init

# Formats Terraform configuration file contents so that it matches the canonical format and style.
terraform fmt

# Validates the configuration files in a directory.
terraform validate

# Creates an execution plan, which lets you preview the changes that Terraform plans to make to your infrastructure.
terraform plan

# Executes the operations proposed in a Terraform plan.
terraform apply

# Extracts the value of an output variable from the state file.
terraform output

# Deprovisions all objects managed by a Terraform configuration.
terraform destroy
```
