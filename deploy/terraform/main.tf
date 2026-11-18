# REQ-P-003 (backend), REQ-P-004 (ECR), REQ-P-005 (OIDC + rol IAM de mínimo privilegio)
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "biblioteca", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "github_repository" {
  type    = string
  default = "TheLuisP23/2doExamenParcial"
}

variable "github_branch" {
  type    = string
  default = "main"
}

variable "cluster_name" {
  type    = string
  default = "biblioteca-eks"
}

variable "repositories" {
  type    = list(string)
  default = ["service-a", "service-b", "frontend"]
}

data "aws_caller_identity" "current" {}

# ── ECR ───────────────────────────────────────────────────────────────────────
resource "aws_ecr_repository" "this" {
  for_each             = toset(var.repositories)
  name                 = "biblioteca/${each.key}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
  image_scanning_configuration {
    scan_on_push = true
  }
  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "conservar las últimas 10 imágenes"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 10 }
      action       = { type = "expire" }
    }]
  })
}

# ── OIDC de GitHub + rol ────────────────────────────────────────────────────────
# El proveedor OIDC de GitHub ya existía en la cuenta: se referencia, no se gestiona.
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/${var.github_branch}"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "biblioteca-github-actions"
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

data "aws_iam_policy_document" "ci" {
  statement {
    sid       = "EcrAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    sid = "EcrPush"
    actions = [
      "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:BatchGetImage", "ecr:DescribeImages",
    ]
    resources = [for r in aws_ecr_repository.this : r.arn]
  }
  statement {
    sid       = "EksDescribe"
    actions   = ["eks:DescribeCluster"]
    resources = ["arn:aws:eks:${var.region}:${data.aws_caller_identity.current.account_id}:cluster/${var.cluster_name}"]
  }
}

resource "aws_iam_role_policy" "ci" {
  name   = "biblioteca-ci"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.ci.json
}

output "ecr_registry" {
  value = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}
