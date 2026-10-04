import tempfile
from pathlib import Path

from cipug.resolver import Image_Version_Resolver
from cipug.service import Service
from cipug.tools.container.quadlet import QuadletTool
from cipug.tools.version_modifier.quadlet import ContainerFile, Quadlet, get_quadlet_dir
from tests.mock_tools import Systemctl as SystemctlMock
from tests.mock_tools.environment import Environment

# A unit file in the style that cipug has to work with: multi-line values with
# line continuations, a #cipug: entry, and a ContainerName that differs from the
# file name
UNIT_FILE = """[Unit]

[Service]
Restart=always

[Container]
ContainerName=whoami_quadlet
#cipug:ImageTagged=docker.io/traefik/whoami:latest
Image=docker.io/traefik/whoami@sha256:200689790a0a0ea48ca45992e0450bc26ccab5307375b41c84dfc4f2475937ab
Network=traefik.network
Label=traefik.enable=true \\
\tquadlet=true \\
\ttraefik.http.routers.whoamiq.rule=Host(`whoamiq.sqrt.stream`)

[Install]
WantedBy=default.target
"""


def test_load_parse_store():
    with tempfile.TemporaryDirectory() as tmpdirname:
        container_file: Path = Path(tmpdirname) / "whoami.container"
        container_file.write_text(UNIT_FILE)

        cf = ContainerFile(container_file)
        assert not cf.has_changes()
        assert cf.image_tagged == "docker.io/traefik/whoami:latest"
        assert cf.image_hashed == (
            "docker.io/traefik/whoami@sha256:"
            "200689790a0a0ea48ca45992e0450bc26ccab5307375b41c84dfc4f2475937ab"
        )
        # The systemd unit is named after the file, not after ContainerName=
        assert cf.container_name == "whoami.service"

        cf.image_hashed = "docker.io/traefik/whoami@sha256:deadbeef"
        assert cf.has_changes()
        cf.write()
        assert not cf.has_changes()

        # Everything that cipug doesn't touch must survive the write
        written = container_file.read_text()
        assert "#cipug:ImageTagged=docker.io/traefik/whoami:latest\n" in written
        assert "ContainerName=whoami_quadlet\n" in written
        assert "\\\n\tquadlet=true \\\n" in written
        assert "Image=docker.io/traefik/whoami@sha256:deadbeef\n" in written


def test_service_detection():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        # A service: quadlet unit files in the QUADLET_DIR subdirectory
        with_quadlet_dir = tmp_path / "with_quadlet_dir"
        (with_quadlet_dir / "quadlet").mkdir(parents=True)
        (with_quadlet_dir / "quadlet" / "whoami.container").write_text(UNIT_FILE)
        # Not a service: unit files in the service folder root (no flat layout support)
        flat = tmp_path / "flat"
        flat.mkdir()
        (flat / "whoami.container").write_text(UNIT_FILE)
        # Not a service: no quadlet files at all
        empty = tmp_path / "empty"
        empty.mkdir()

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),  # Not needed for the test, but Config() checks for it
            },
        ):
            assert get_quadlet_dir(with_quadlet_dir) == with_quadlet_dir / "quadlet"
            assert Quadlet.check_if_folder_is_service(with_quadlet_dir)
            assert not Quadlet.check_if_folder_is_service(flat)
            assert not Quadlet.check_if_folder_is_service(empty)
            assert not Quadlet.check_if_folder_is_service(tmp_path / "does_not_exist")


def test_quadlet_dir_setting():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        custom = tmp_path / "custom"
        (custom / "units").mkdir(parents=True)
        (custom / "units" / "whoami.container").write_text(UNIT_FILE)
        default_dir = tmp_path / "default"
        (default_dir / "quadlet").mkdir(parents=True)
        (default_dir / "quadlet" / "whoami.container").write_text(UNIT_FILE)

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
                "CIPUG_QUADLET_DIR": "units",
            },
        ):
            assert get_quadlet_dir(custom) == custom / "units"
            assert Quadlet.check_if_folder_is_service(custom)
            assert not Quadlet.check_if_folder_is_service(default_dir)


def test_quadlet_reads_container_versions():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        svc_path = tmp_path / "traefik_quadlet"
        (svc_path / "quadlet").mkdir(parents=True)
        (svc_path / "quadlet" / "whoami.container").write_text(UNIT_FILE)
        (svc_path / "quadlet" / "traefik.network").write_text(
            "[Network]\nIPv6=true\nInternal=true\n"
        )

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
            },
        ):
            quadlet = Quadlet(Service(svc_path), Image_Version_Resolver())
            # Only *.container files are version-handled, the .network is not
            assert len(quadlet.container_versions) == 1
            cv = quadlet.container_versions[0]
            assert cv.name == "whoami.container"
            assert cv.tagged == "docker.io/traefik/whoami:latest"
            assert cv.hash_current == (
                "200689790a0a0ea48ca45992e0450bc26ccab5307375b41c84dfc4f2475937ab"
            )


def test_quadlet_tool_install():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        svc_path = tmp_path / "myservice"
        (svc_path / "quadlet").mkdir(parents=True)
        (svc_path / "quadlet" / "myservice.container").write_text(UNIT_FILE)
        install_dir = tmp_path / "install_dir"

        with Environment(
            tools=[SystemctlMock],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
                "CIPUG_QUADLET_INSTALL_DIR": str(install_dir),
            },
        ) as e:
            tool = QuadletTool()
            svc = Service(svc_path)

            assert tool.install(svc)
            link = install_dir / f"{svc.name}.units"
            assert link.is_symlink()
            assert link.resolve() == (svc_path / "quadlet").resolve()
            assert e.log.pop(0).cmdline == ["systemctl", "--user", "daemon-reload"]

            # Installing again is idempotent
            assert tool.install(svc)
            assert e.log.pop(0).cmdline == ["systemctl", "--user", "daemon-reload"]

            # A symlink pointing somewhere else is an error, not silently overwritten
            link.unlink()
            link.symlink_to(tmp_path / "elsewhere")
            assert not tool.install(svc)
            assert len(e.log) == 2  # no additional daemon-reload


def _make_service(tmp_path: Path, name: str) -> Path:
    """A service folder with a quadlet dir holding one container unit"""
    quadlet_dir = tmp_path / name / "quadlet"
    quadlet_dir.mkdir(parents=True)
    (quadlet_dir / f"{name}.container").write_text(UNIT_FILE)
    return quadlet_dir


def test_cleanup_removes_dangling_links():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        install_dir = tmp_path / "install_dir"
        install_dir.mkdir()

        # Dangling link to a quadlet dir of a (now removed) service: to be removed
        gone = tmp_path / "gone_service" / "quadlet"
        dangling = install_dir / "gone_service.units"
        dangling.symlink_to(gone)
        # Dangling link to something that isn't a service's quadlet dir: to be kept
        unrelated = install_dir / "unrelated.units"
        unrelated.symlink_to(tmp_path / "nope" / "somewhere_else")

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
                "CIPUG_QUADLET_INSTALL_DIR": str(install_dir),
            },
        ):
            tool = QuadletTool()
            assert tool.cleanup()
            assert not dangling.exists() and not dangling.is_symlink()
            assert unrelated.is_symlink()


def test_cleanup_renames_wrongly_named_link():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        quadlet_dir = _make_service(tmp_path, "traefik_quadlet")
        install_dir = tmp_path / "install_dir"
        install_dir.mkdir()
        (install_dir / "user").mkdir()
        wrong = install_dir / "user" / "traefik.units"
        wrong.symlink_to(quadlet_dir)

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
                "CIPUG_QUADLET_INSTALL_DIR": str(install_dir),
            },
        ):
            tool = QuadletTool()
            assert tool.cleanup()
            fixed = install_dir / "traefik_quadlet.units"
            assert fixed.is_symlink()
            assert fixed.resolve() == quadlet_dir.resolve()
            assert not wrong.is_symlink()
            # Nothing inside the quadlet dir may have been touched
            assert (quadlet_dir / "traefik_quadlet.container").is_file()


def test_cleanup_removes_redundant_link():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        quadlet_dir = _make_service(tmp_path, "navidrome")
        install_dir = tmp_path / "install_dir"
        install_dir.mkdir()
        correct = install_dir / "navidrome.units"
        correct.symlink_to(quadlet_dir)
        redundant = install_dir / "navidrome-old.units"
        redundant.symlink_to(quadlet_dir)

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
                "CIPUG_QUADLET_INSTALL_DIR": str(install_dir),
            },
        ):
            tool = QuadletTool()
            assert tool.cleanup()
            assert correct.is_symlink()
            assert not redundant.is_symlink()
            assert (quadlet_dir / "navidrome.container").is_file()


def test_cleanup_never_touches_non_symlinks():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        quadlet_dir = _make_service(tmp_path, "navidrome")
        install_dir = tmp_path / "install_dir"
        install_dir.mkdir()
        # A regular file and a real directory that look like managed links
        a_file = install_dir / "navidrome.units"
        a_file.write_text("i am a file, do not delete me\n")
        a_dir = install_dir / "subdir.units"
        a_dir.mkdir()
        a_dir_content = a_dir / "important.container"
        a_dir_content.write_text(UNIT_FILE)

        with Environment(
            tools=[],
            env_overwrites={
                "CIPUG_SERVICES_ROOT": str(tmp_path),
                "CIPUG_QUADLET_INSTALL_DIR": str(install_dir),
            },
        ):
            tool = QuadletTool()
            assert tool.cleanup()
            assert a_file.is_file()
            assert a_dir.is_dir()
            assert a_dir_content.is_file()
            # The quadlet dir of the service is untouched throughout
            assert (quadlet_dir / "navidrome.container").is_file()
            # (That removing a symlink never touches its target directory or
            # the target's contents is covered by the rename/redundant tests)
