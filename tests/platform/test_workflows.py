from pathlib import Path

import pytest
import yaml

WF = Path(__file__).resolve().parents[2] / ".github/workflows"


def load(name: str) -> dict:
    return yaml.safe_load((WF / name).read_text(encoding="utf-8"))


@pytest.mark.req("REQ-P-013")
def test_ci_runs_verify_without_aws():
    ci = load("ci.yml")
    text = (WF / "ci.yml").read_text(encoding="utf-8")
    assert ci["permissions"] == {"contents": "read"}
    assert "make verify" in text and "gitleaks" in text
    assert "configure-aws-credentials" not in text


@pytest.mark.req("REQ-P-014")
def test_cd_uses_oidc_and_deploys():
    cd = load("cd.yml")
    text = (WF / "cd.yml").read_text(encoding="utf-8")
    assert cd["permissions"] == {"id-token": "write", "contents": "read"}
    assert "AWS_ACCESS_KEY_ID" not in text and "AWS_SECRET_ACCESS_KEY" not in text
    assert "role-to-assume: ${{ vars.AWS_ROLE_ARN }}" in text
    assert "IMAGE_TAG: ${{ github.sha }}" in text
    assert "rollout status" in text and "kubectl apply -n biblioteca" in text
    assert cd["concurrency"]["group"] == "cd-main"
