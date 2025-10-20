from pathlib import Path
from tempfile import TemporaryDirectory

from cipug.resolver import Image_Version_Resolver
from tests.mock_tools import Skopeo as SkopeoMock
from tests.mock_tools.environment import Environment, LogEntry


def test_skopeo():
    # We want to work with a controlled test cache. Therefore we create
    # a temporary directory with our cache in it.
    tmp_ctx = TemporaryDirectory()
    tmp_path = Path(tmp_ctx.name)
    test_cache = tmp_path / "cipug_test_cache.json"

    with Environment(
        tools = [SkopeoMock],
        env_overwrites = {
            "CIPUG_CACHE_LOCATION": str(test_cache.resolve()),
            "CIPUG_CACHE_DURATION": str(3600)
        },
        tmp_ctx = tmp_ctx  # reuse the temporary directory for the environment
    ) as e:
        resolver = Image_Version_Resolver()
        assert not test_cache.is_file()  # Cache file doesn't exist yet
        image_tagged = "ghcr.io/immich-app/immich-server:release"
        image_hashed = resolver.resolve_image_version(image_tagged)
        assert image_hashed == (
            "ghcr.io/immich-app/immich-server@sha256:"
            "72a9b9de6c6abfa7a9c9cdc244ae4d2bd9fea2ae00997f194cbd10aca72ea210"
        )
        assert test_cache.is_file()  # Cache file exists now

        # We expect one successful call to the mock skopeo binary
        log: list[LogEntry] = e.log
        assert len(log) == 1
        entry = log[0]
        assert entry.name == "skopeo"
        assert entry.action.returncode == 0

        # Resolve the same image tag again. Our test_cache should be used
        # now and we expect no additional call to skopeo (the number of calls
        # stays 1 from above)
        image_hashed = resolver.resolve_image_version(image_tagged)
        assert image_hashed == (
            "ghcr.io/immich-app/immich-server@sha256:"
            "72a9b9de6c6abfa7a9c9cdc244ae4d2bd9fea2ae00997f194cbd10aca72ea210"
        )
        assert len(e.log) == 1
