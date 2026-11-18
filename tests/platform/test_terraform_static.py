from pathlib import Path

import hcl2
import pytest

TF = Path(__file__).resolve().parents[2] / "deploy/terraform/main.tf"


@pytest.fixture(scope="module")
def tf() -> dict:
    with TF.open(encoding="utf-8") as f:
        return hcl2.load(f)


@pytest.mark.req("REQ-P-003")
def test_backend_s3_locking(tf):
    backend = tf["terraform"][0]["backend"][0]["s3"]
    assert backend["use_lockfile"] is True and backend["encrypt"] is True


@pytest.mark.req("REQ-P-004")
def test_ecr_immutable_scanned():
    text = TF.read_text(encoding="utf-8")
    assert 'image_tag_mutability = "IMMUTABLE"' in text and "scan_on_push = true" in text
    assert '"service-a", "service-b", "frontend"' in text and "aws_ecr_lifecycle_policy" in text


@pytest.mark.req("REQ-P-005")
def test_oidc_trust_and_least_privilege():
    text = TF.read_text(encoding="utf-8")
    assert "token.actions.githubusercontent.com:sub" in text and "ref:refs/heads/${var.github_branch}" in text
    assert "token.actions.githubusercontent.com:aud" in text
    # el único recurso comodín es GetAuthorizationToken
    assert text.count('resources = ["*"]') == 1
    assert '"*"' not in text.split("EcrPush")[1]
    assert "AWS_ACCESS_KEY" not in text
