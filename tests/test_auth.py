from pathlib import Path

from seqspec.auth import AuthProfile, AuthRegistry, init_profile


def test_auth_registry_loads_profiles_from_env_path(monkeypatch, tmp_path):
    config_path = tmp_path / "auth.toml"
    config_path.write_text(
        """
[profiles.igvf]
hosts = ["api.data.igvf.org", "data.igvf.org"]
kind = "basic"
username_env = "IGVF_ACCESS_KEY_ID"
password_env = "IGVF_ACCESS_KEY_SECRET"
""".strip()
        + "\n"
    )
    monkeypatch.setenv("SEQSPEC_AUTH_CONFIG", str(config_path))

    registry = AuthRegistry.load()

    assert len(registry.profile_summaries()) == 1
    assert registry.profile_summaries()[0]["name"] == "igvf"


def test_auth_registry_resolves_requests_auth(monkeypatch, tmp_path):
    config_path = tmp_path / "auth.toml"
    config_path.write_text(
        """
[profiles.igvf]
hosts = ["api.data.igvf.org"]
kind = "basic"
username_env = "IGVF_ACCESS_KEY_ID"
password_env = "IGVF_ACCESS_KEY_SECRET"
""".strip()
        + "\n"
    )
    monkeypatch.setenv("SEQSPEC_AUTH_CONFIG", str(config_path))
    monkeypatch.setenv("IGVF_ACCESS_KEY_ID", "alice")
    monkeypatch.setenv("IGVF_ACCESS_KEY_SECRET", "secret")

    registry = AuthRegistry.load()
    auth = registry.resolve_requests_auth(
        "https://api.data.igvf.org/reference-files/foo", "igvf"
    )

    assert auth == ("alice", "secret")


def test_init_profile_creates_config(monkeypatch, tmp_path):
    config_path = tmp_path / "config" / "auth.toml"
    monkeypatch.setenv("SEQSPEC_AUTH_CONFIG", str(config_path))

    output = init_profile(
        "igvf",
        AuthProfile(
            hosts=["api.data.igvf.org", "data.igvf.org"],
            kind="basic",
            username_env="IGVF_ACCESS_KEY_ID",
            password_env="IGVF_ACCESS_KEY_SECRET",
        ),
    )

    assert output["created_config"] is True
    assert Path(output["path"]).exists()
