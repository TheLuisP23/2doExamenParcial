from pathlib import Path

import pytest
import yaml

K8S = Path(__file__).resolve().parents[2] / "deploy/k8s"
DOCS = [d for f in sorted(K8S.rglob("*.yaml")) for d in yaml.safe_load_all(f.read_text(encoding="utf-8")) if d]
WORKLOADS = [d for d in DOCS if d["kind"] in {"Deployment", "StatefulSet"}]


def kinds(kind):
    return [d for d in DOCS if d["kind"] == kind]


@pytest.mark.req("REQ-P-007")
def test_storageclass_gp3():
    sc = kinds("StorageClass")[0]
    assert sc["provisioner"] == "ebs.csi.aws.com" and sc["parameters"]["type"] == "gp3"
    assert sc["volumeBindingMode"] == "WaitForFirstConsumer"


@pytest.mark.req("REQ-P-008", "REQ-P-009")
def test_databases_statefulsets_with_pvc():
    sts = {d["metadata"]["name"]: d for d in kinds("StatefulSet")}
    assert set(sts) == {"postgres", "mongo"}
    for s in sts.values():
        assert s["spec"]["volumeClaimTemplates"][0]["spec"]["storageClassName"] == "gp3"


@pytest.mark.req("REQ-P-010")
def test_every_container_has_requests_limits_and_probes():
    for w in WORKLOADS:
        for c in w["spec"]["template"]["spec"]["containers"]:
            res = c["resources"]
            assert {"cpu", "memory"} <= set(res["requests"]) and {"cpu", "memory"} <= set(res["limits"])
            assert "readinessProbe" in c and "livenessProbe" in c
            assert c["securityContext"]["allowPrivilegeEscalation"] is False
        assert w["spec"]["template"]["spec"]["securityContext"]["runAsNonRoot"] is True


@pytest.mark.req("REQ-P-011")
def test_single_loadbalancer_is_frontend_80():
    lbs = [s for s in kinds("Service") if s["spec"].get("type") == "LoadBalancer"]
    assert [s["metadata"]["name"] for s in lbs] == ["frontend"]
    assert lbs[0]["spec"]["ports"][0]["port"] == 80 and lbs[0]["spec"]["ports"][0]["targetPort"] == 8080


@pytest.mark.req("REQ-P-012")
def test_no_secret_values_in_repo():
    assert kinds("Secret") == []


@pytest.mark.req("REQ-P-017")
def test_namespace_and_labels():
    for d in DOCS:
        if d["kind"] in {"Namespace", "StorageClass"}:
            continue
        assert d["metadata"]["namespace"] == "biblioteca"
        assert d["metadata"]["labels"]["app.kubernetes.io/part-of"] == "biblioteca"


@pytest.mark.req("REQ-SYS-002")
def test_each_service_uses_only_its_database():
    deps = {d["metadata"]["name"]: d for d in kinds("Deployment")}
    env_a = str(deps["service-a"]["spec"]["template"]["spec"]["containers"][0]["env"])
    env_b = str(deps["service-b"]["spec"]["template"]["spec"]["containers"][0]["env"])
    assert "postgres" in env_a and "mongo" not in env_a and "service-b" not in env_a
    assert "mongo" in env_b and "postgres" not in env_b and "service-a" not in env_b
