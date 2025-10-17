from tempfile import TemporaryDirectory
from pathlib import Path
from tests.mock_tools.environment import Environment, LogEntry
from tests.mock_tools import PodmanCompose, DockerCompose, Snapper, Skopeo, Systemctl
from tests.helper import call_cipug
import pytest

@pytest.mark.parametrize(
    "container_tool, service_stop_start, stop_start_method, do_snapshot, prune_images",
    [
        ("docker", True, "compose", True, False),
        ("podman", False, "compose", False, True),
        ("podman", True, "systemd-user", True, False),
        ("podman", False, "systemd-system", False, True),
    ],
)
def test_update_podman_compose(
    container_tool: str,
    service_stop_start: bool,
    stop_start_method: str,
    do_snapshot: bool,
    prune_images: bool,
):
    # Complete End2End test, where cipug updates a non-existing immich service in the
    # testing environment with only mock tools.

    # We want to work with a controlled test cache. Therefore we create
    # a temporary directory with our cache in it. We also use that for our service.
    tmp_ctx = TemporaryDirectory()
    tmp_path = Path(tmp_ctx.name)
    test_cache = tmp_path / "cipug_test_cache.json"
    test_services = tmp_path / "services"
    service_example = test_services / "immich"
    example_env = service_example / ".env"
    example_compose = service_example / "compose.yml"

    with Environment(
        tools = [PodmanCompose, DockerCompose, Snapper, Skopeo, Systemctl],
        env_overwrites = {
            "MOCK_TOOL_SNAPPER_ENV_CONF": str(service_example)  # Add our service example to the snapper mock tool
        },
        tmp_ctx = tmp_ctx  # reuse the temporary directory for the environment
    ) as e:
        test_services.mkdir()
        service_example.mkdir()
        example_compose.touch()
        # The testing .env with a random outdated hash
        example_env.write_text(
            "SERVICE_IMMICHSERVER_IMAGE_TAGGED=ghcr.io/immich-app/immich-server:release\n"
            "ERVICE_IMMICHSERVER_IMAGE_HASHED=ghcr.io/immich-app/immich-server@"
            "sha256:8286638680f0a38a7cb380be64ed77d1d1cfe6d0e0b843f64bff92b24289078d"
        )

        cp: CompletedProcess = call_cipug(
            env={
                "CIPUG_SERVICES_ROOT": test_services,
                "CIPUG_COMPOSE_FILE_NAME": "compose.yml",
                "CIPUG_ENV_FILE_NAME": ".env",
                "CIPUG_COMPOSE_TOOL": f"{container_tool} compose",
                "CIPUG_CONTAINER_TOOL": container_tool,
                "CIPUG_SERVICE_STOP_START": service_stop_start,
                "CIPUG_STOP_START_METHOD": stop_start_method,
                "CIPUG_SERVICE_SNAPSHOT": do_snapshot,
                "CIPUG_PRUNE_IMAGES": prune_images,
                "CIPUG_CACHE_LOCATION": test_cache,
                "CIPUG_CACHE_DURATION": 3600,
            }
        )
        print(cp.stdout)
        print(cp.stderr)

        assert cp.returncode == 0
        # This hash is what the skopeo mock tool has stored for resolving immich:release. After running
        # cipug we should find it in .env.
        assert "72a9b9de6c6abfa7a9c9cdc244ae4d2bd9fea2ae00997f194cbd10aca72ea210" in example_env.read_text()

        log = e.log  # e.log causes reading the logs from disk every time, which wouldn't work with pop() below

        # Check that the correct order and arguments of called tools. Changes in how cipug works may require
        # reordering/adjustments here!
        assert log.pop(0).cmdline == ["skopeo", "--version"]
        if service_stop_start:
            assert log.pop(0).cmdline == [container_tool, "--version"]
        if do_snapshot:
            assert log.pop(0).cmdline == ["snapper", "--version"]
        if prune_images:
            assert log.pop(0).cmdline == [container_tool, "image", "prune", "-f"]
        assert log.pop(0).cmdline == ["snapper", "--jsonout", "list-configs"]
        assert log.pop(0).cmdline[:3] == ["skopeo", "inspect", "--no-tags"]
        assert log.pop(0).cmdline == [container_tool, "compose", "ps"]
        if do_snapshot:
            assert log.pop(0).cmdline[:4] == ["snapper", "-c", "envconf", "create"]
        assert log.pop(0).cmdline == [container_tool, "compose", "pull"]
        if service_stop_start:
            if stop_start_method == "compose":
                assert log.pop(0).cmdline == [container_tool, "compose", "down"]
                assert log.pop(0).cmdline == [container_tool, "compose", "up", "-d"]
            elif stop_start_method == "systemd-user":
                assert log.pop(0).cmdline == ["systemctl", "--user", "restart", f"{container_tool}-compose@immich"]
            elif stop_start_method == "systemd-system":
                assert log.pop(0).cmdline == ["systemctl", "restart", f"{container_tool}-compose@immich"]
            else:
                raise NotImplementedError(f"Unsupported stop_start_method: {stop_start_method}")
