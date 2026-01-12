provider "aws" {
  profile = "default"
  region  = "eu-central-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_vpc" "main" {
  cidr_block         = "10.0.0.0/16"
  enable_dns_support = true

  tags = {
    name = "v2g-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-central-1a"

  tags = {
    Name = "v2g-subnet-public"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "v2g-igw"
  }
}

resource "aws_route_table" "main" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "v2g-rtb"
  }
}

resource "aws_route_table_association" "main" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.main.id
}

resource "aws_security_group" "allow_ssh" {
  name   = "allow-ssh"
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "v2g-sg-allow-ssh"
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh" {
  security_group_id = aws_security_group.allow_ssh.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_security_group" "expose_tcp_8000" {
  name   = "expose-tcp-8000"
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "v2g-sg-expose-tcp-8000"
  }
}

resource "aws_vpc_security_group_ingress_rule" "expose_tcp_8000" {
  security_group_id = aws_security_group.expose_tcp_8000.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 8000
  to_port           = 8000
}

resource "aws_key_pair" "common" {
  key_name   = "v2g-key-common"
  public_key = file("./v2g.pub")
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
  key_name      = aws_key_pair.common.key_name

  subnet_id = aws_subnet.public.id
  vpc_security_group_ids = [
    aws_security_group.allow_ssh.id,
    aws_security_group.expose_tcp_8000.id,
  ]
  associate_public_ip_address = true

  tags = {
    Name = "v2g-instance-app"
  }
}
