from pathlib import Path
import yaml

for path in [Path(".github/workflows/ci-cd.yml"), Path(".github/workflows/monitoring.yml"), Path("render.yaml")]:
    data = yaml.safe_load(path.read_text())
    assert data, f"empty yaml: {path}"

ci = yaml.safe_load(Path(".github/workflows/ci-cd.yml").read_text())
assert "jobs" in ci and {"api-check", "web-check", "deploy-cloudflare", "deploy-render"}.issubset(ci["jobs"])
monitoring = yaml.safe_load(Path(".github/workflows/monitoring.yml").read_text())
assert "jobs" in monitoring and "production-probe" in monitoring["jobs"]
render = yaml.safe_load(Path("render.yaml").read_text())
assert render["services"][0]["healthCheckPath"] == "/api/v1/ready"
print("CI/CD and Render YAML valid")
