from tests.helper import call_cipug
from subprocess import CompletedProcess
import json
import tempfile
from pathlib import Path
import pytest

from cipug.config import Config, unset


# Do not include config file path in these settings templates.
# Also leave the verbosity level to default, otherwise the parsing of cipug's output may fail.
Settings_A = {
    "SERVICES_ROOT": "/some/path",
    "COMPOSE_TOOL": "podman compose",
    "CONTAINER_TOOL": "podman",
}
Settings_B = {
    "COMPOSE_TOOL": "docker compose",
    "CONTAINER_TOOL": "docker",
    "SERVICE_PULL": True,
    "CACHE_DURATION": 8287289823,
    "COMPOSE_FILE_NAME": "this-is-not-default.yaml123"
}
Settings_Default = {
    key: default_and_type[0]
    for key, default_and_type in Config.settings_schema.items()
}
Settings_Required = [
    key for key, value in Settings_Default.items() if value is unset
]
@pytest.mark.parametrize("env_settings,file_settings", [
    ({}, {}),
    (Settings_A, {}),
    (Settings_B, {}),
    (Settings_A, Settings_B),
    (Settings_B, Settings_A),
    ({}, Settings_A),
    ({}, Settings_B)
])
def test_config_loading(env_settings: dict, file_settings: dict):
    # Test that config file loading works and that environment varibles have priority

    with tempfile.TemporaryDirectory() as tmpdirname:
        config_file: Path = Path(tmpdirname) / "cipug-test-config-file.json"
        if not file_settings:
            if config_file.is_file():
                config_file.unlink()
        else:
            config_file.write_text(json.dumps(file_settings, indent=2))
            env_settings = dict() if not env_settings else env_settings.copy()
            env_settings["CONFIG_FILE"] = str(config_file.resolve())

        print(f"Calling cipug with environment variables: {json.dumps(env_settings, indent=2)}")
        if file_settings:
            print(f"Config file location: {config_file}")
            print(f"Config file content: {config_file.read_text()}")
        else:
            print(f"No config file in use.")

        cp: CompletedProcess = call_cipug(
            args=["--print-config-json"],
            env={
                f"CIPUG_{key}":val for key, val in env_settings.items()
            }
        )

        # Check if required settings are missing, in this case we expect failure
        required_settings_missing: list[str] = []
        for key in Settings_Required:
            if key in env_settings:
                continue
            if key in file_settings:
                continue
            required_settings_missing.append(key)
        if required_settings_missing:
            assert cp.returncode != 0, (
                f"Expected failure, since settings {required_settings_missing} are missing.\n"
                f"How cipug parsed the settings: {cp.stdout}"
            )
            return

        # When this point is reached, all required settings are present, we expect success
        assert cp.returncode == 0, (
            f"cipug failed unexpectedly with return code {cp.returncode}:\n"
            f"{cp.stdout}"
            f"{cp.stderr}"
        )
        config_result = json.loads(cp.stdout)
        for key, val in config_result.items():
            # Priority: environment variables > config file > defaults
            if key in env_settings:
                assert val == env_settings[key]
                continue
            if key in file_settings:
                assert val == file_settings[key]
                continue
            # If the key wasn't present in any settings, it should be the default value.
            # Special case: for default Path() objects we need to stringify them to compare
            # (as they don't json-serialize)
            val_default = Settings_Default[key]
            if isinstance(val_default, Path):
                val_default = str(val_default)
            assert val == val_default


def test_config_file_in_config_file():
    # Make sure that specifying a config file inside the config file raises an error
    with tempfile.TemporaryDirectory() as tmpdirname:
        config_file: Path = Path(tmpdirname) / "cipug-test-config-file.json"
        config_file.write_text(
            json.dumps(
                {
                    "CONFIG_FILE": "path/to/another/config/file",
                    "SERVICES_ROOT": "/some/path",
                },
                indent=2
            )
        )
        cp: CompletedProcess = call_cipug(
            args=["--print-config-json"],
            env={
                "CIPUG_CONFIG_FILE": str(config_file.resolve())
            }
        )
        assert cp.returncode != 0
