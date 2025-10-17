from tests.mock_tools.tools.base import MockTool, Action
import json

mock_data  = {
    "docker://ghcr.io/immich-app/immich-server:release": {
        "Name": "ghcr.io/immich-app/immich-server",
        "Digest": "sha256:72a9b9de6c6abfa7a9c9cdc244ae4d2bd9fea2ae00997f194cbd10aca72ea210",
        "RepoTags": [],
        "Created": "2025-10-15T19:26:59.439284494Z",
        "DockerVersion": "",
        "Labels": {
            "org.opencontainers.image.created": "2025-10-15T19:24:51.468Z",
            "org.opencontainers.image.description": "High performance self-hosted photo and video management solution.",
            "org.opencontainers.image.licenses": "AGPL-3.0",
            "org.opencontainers.image.revision": "43eccca86a4b25deb132bda72ac4d846332f3e6d",
            "org.opencontainers.image.source": "https://github.com/immich-app/immich",
            "org.opencontainers.image.title": "immich",
            "org.opencontainers.image.url": "https://github.com/immich-app/immich",
            "org.opencontainers.image.version": "v2.1.0"
        },
        "Architecture": "amd64",
        "Os": "linux",
        "Layers": [
            "sha256:396b1da7636e2dcd10565cb4f2f952cbb4a8a38b58d3b86a2cacb172fb70117c",
            "sha256:c06c7d5debd60ba5e039513fb405e868e4dea802634462b0e0e92c7667547a20",
            "sha256:6b9d6ac9b0f9eb85f79b00eb45c2593d2a53d5cb55d4f37fe09ed6609f42c937",
            "sha256:c3756cb0d50f63526a0e085ef730da1e7cd9f381e6ee141419dcbc936346903a",
            "sha256:2a434cb0ef0e6270689f144b545cd93155837dab7170c00fa4633a171f4e1b1d",
            "sha256:cf83e48f496ee602f3f411b7a03b918790be4f556b465577e344d6326b11afd8",
            "sha256:fb3a52a86c51dccd98558d658433183ad4d51dc3469123efb1de689b3406a7d0",
            "sha256:a87ef2944ae3e9314508270955be73149cb66621cf0b31029b7513901a8a9de5",
            "sha256:3c6e0f822e983b4baacff85102caf060ac85c627177c747e6cd8ab873d0c14e6",
            "sha256:9bb8f5fec87514c56cccd87cc4f8713003775636bce808cc10f708365eadb6b1",
            "sha256:7b569af334bc657887f878a25e3e11496c5ada20cd4b565b93f74646d2d1b19d",
            "sha256:1a15eda7ef2d5dcc57e2008a3b7d149a418d3bc0a517cace1ffde2904b173b9f",
            "sha256:cd610e300ec4ad7011a09be433784a62a119fce18f4e4367a8663df6a028557e",
            "sha256:ed7feaecc61735da016b9b6af4c162d81c0f1f40dd9ba059f34f5662afb7130f",
            "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1",
            "sha256:c73f3882885da7bff5c4e940f0bec564f67da0e1ea42d3ea2ab104cb533a1602",
            "sha256:756f8b6f7b4ce3a10fc8c9aabaafd44b83c5467eb66261c16f02da2a72b4fa41",
            "sha256:19d98c34a704508fd72b38e01edae7aff801f5b84ea821ab89cfe9418522818a",
            "sha256:081e96395164ba53e52b927ac72a42efb11cbe6c86b437c4e5f1e06784136e09",
            "sha256:3f6e24ea430f27266d9c49096f29a3a298d51242b1174705725d4afd1fcc76c9",
            "sha256:e7f5b8f417d430572d85616b4bac45d574e50ef7e64661b43c67343925736d48"
        ],
        "LayersData": [
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:396b1da7636e2dcd10565cb4f2f952cbb4a8a38b58d3b86a2cacb172fb70117c",
                "Size": 29773285,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:c06c7d5debd60ba5e039513fb405e868e4dea802634462b0e0e92c7667547a20",
                "Size": 3309,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:6b9d6ac9b0f9eb85f79b00eb45c2593d2a53d5cb55d4f37fe09ed6609f42c937",
                "Size": 49006197,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:c3756cb0d50f63526a0e085ef730da1e7cd9f381e6ee141419dcbc936346903a",
                "Size": 1717141,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:2a434cb0ef0e6270689f144b545cd93155837dab7170c00fa4633a171f4e1b1d",
                "Size": 449,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:cf83e48f496ee602f3f411b7a03b918790be4f556b465577e344d6326b11afd8",
                "Size": 95,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:fb3a52a86c51dccd98558d658433183ad4d51dc3469123efb1de689b3406a7d0",
                "Size": 1113,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:a87ef2944ae3e9314508270955be73149cb66621cf0b31029b7513901a8a9de5",
                "Size": 39521631,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:3c6e0f822e983b4baacff85102caf060ac85c627177c747e6cd8ab873d0c14e6",
                "Size": 3795,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:9bb8f5fec87514c56cccd87cc4f8713003775636bce808cc10f708365eadb6b1",
                "Size": 330988706,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:7b569af334bc657887f878a25e3e11496c5ada20cd4b565b93f74646d2d1b19d",
                "Size": 39975238,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:1a15eda7ef2d5dcc57e2008a3b7d149a418d3bc0a517cace1ffde2904b173b9f",
                "Size": 18082081,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:cd610e300ec4ad7011a09be433784a62a119fce18f4e4367a8663df6a028557e",
                "Size": 132,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:ed7feaecc61735da016b9b6af4c162d81c0f1f40dd9ba059f34f5662afb7130f",
                "Size": 7518,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1",
                "Size": 32,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:c73f3882885da7bff5c4e940f0bec564f67da0e1ea42d3ea2ab104cb533a1602",
                "Size": 102517452,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:756f8b6f7b4ce3a10fc8c9aabaafd44b83c5467eb66261c16f02da2a72b4fa41",
                "Size": 17245872,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:19d98c34a704508fd72b38e01edae7aff801f5b84ea821ab89cfe9418522818a",
                "Size": 754276,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:081e96395164ba53e52b927ac72a42efb11cbe6c86b437c4e5f1e06784136e09",
                "Size": 215,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:3f6e24ea430f27266d9c49096f29a3a298d51242b1174705725d4afd1fcc76c9",
                "Size": 11148,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:e7f5b8f417d430572d85616b4bac45d574e50ef7e64661b43c67343925736d48",
                "Size": 11102,
                "Annotations": None
            }
        ],
        "Env": [
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/src/app/server/bin",
            "NODE_VERSION=22.18.0",
            "YARN_VERSION=1.22.22",
            "DEBIAN_RELEASE=trixie",
            "LD_LIBRARY_PATH=/usr/lib/jellyfin-ffmpeg/lib:/usr/lib/wsl/lib:",
            "NODE_ENV=production",
            "NVIDIA_DRIVER_CAPABILITIES=all",
            "NVIDIA_VISIBLE_DEVICES=all",
            "IMMICH_BUILD=18540213782",
            "IMMICH_BUILD_URL=https://github.com/immich-app/immich/actions/runs/18540213782",
            "IMMICH_BUILD_IMAGE=v2.1.0",
            "IMMICH_BUILD_IMAGE_URL=https://github.com/immich-app/immich/pkgs/container/immich-server",
            "IMMICH_REPOSITORY=immich-app/immich",
            "IMMICH_REPOSITORY_URL=https://github.com/immich-app/immich",
            "IMMICH_SOURCE_REF=v2.1.0",
            "IMMICH_SOURCE_COMMIT=43eccca86a4b25deb132bda72ac4d846332f3e6d",
            "IMMICH_SOURCE_URL=https://github.com/immich-app/immich/commit/43eccca86a4b25deb132bda72ac4d846332f3e6d"
        ]
    }

}


class Skopeo(MockTool):
    name: str = "skopeo"

    def run(self, argv: list[str]) -> Action:
        match argv[1:]:
            case ["--version"]:
                return Action(
                    stdout="skopeo version 1.20.0\n"
                )
            case ["inspect", "--no-tags", image]:
                if image not in mock_data:
                    return Action(
                        returncode=99, stderr="Error: image not in mock database"
                    )
                return Action(
                    stdout=json.dumps(
                        mock_data[image],
                        indent=4
                    )
                )
        return Action(
            returncode=99, stderr="Error: Invalid command for Skopeo MockTool"
        )
