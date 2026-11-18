from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.req("REQ-P-006")

CFG = Path(__file__).resolve().parents[2] / "deploy/eksctl/cluster.yaml"


@pytest.fixture(scope="module")
def cfg() -> dict:
    return yaml.safe_load(CFG.read_text(encoding="utf-8"))


def test_metadata(cfg):
    assert cfg["metadata"]["name"] == "biblioteca-eks"
    assert cfg["metadata"]["region"] == "us-east-1"
    assert cfg["metadata"]["version"] in {"1.35", "1.36", "1.37"}


def test_nodegroup_2_t3_medium(cfg):
    ng = cfg["managedNodeGroups"][0]
    assert ng["instanceType"] == "t3.medium"
    assert ng["desiredCapacity"] == 2 and ng["minSize"] == 2


def test_addons(cfg):
    names = {a["name"] for a in cfg["addons"]}
    assert {"vpc-cni", "coredns", "kube-proxy", "aws-ebs-csi-driver"} <= names
    ebs = next(a for a in cfg["addons"] if a["name"] == "aws-ebs-csi-driver")
    assert ebs["wellKnownPolicies"]["ebsCSIController"] is True
    assert cfg["iam"]["withOIDC"] is True


def test_access_entry_scoped_to_namespace(cfg):
    entry = cfg["accessConfig"]["accessEntries"][0]
    assert entry["principalARN"].endswith(":role/biblioteca-github-actions")
    pol = entry["accessPolicies"][0]
    assert pol["policyARN"].endswith("AmazonEKSEditPolicy")
    assert pol["accessScope"] == {"type": "namespace", "namespaces": ["biblioteca"]}


def test_no_literal_account_id():
    import re

    assert not re.search(r"\b\d{12}\b", CFG.read_text(encoding="utf-8"))
