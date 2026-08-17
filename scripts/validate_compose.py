from pathlib import Path
import yaml

config = yaml.safe_load(Path("docker-compose.yml").read_text())
assert set(config["services"]) == {"web", "api", "postgres", "redis"}
assert "pulse_pg_data" in config["volumes"]
assert "pulse_redis_data" in config["volumes"]
assert any("001_pulse_events.sql" in str(item) for item in config["services"]["postgres"]["volumes"])
assert config["services"]["api"]["environment"]["REDIS_URL"] == "redis://redis:6379/0"
print("compose yaml ok")
