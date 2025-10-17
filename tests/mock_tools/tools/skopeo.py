from tests.mock_tools.tools.base import MockTool, Action
import json

mock_data  = {
    "docker://ghcr.io/immich-app/immich-server:v1.132.3": {
        "Name": "ghcr.io/immich-app/immich-server",
        "Digest": "sha256:6680d88486251b0264a78a1934fe82eef875555aa6d84d703a0980328a5d5c31",
        "RepoTags": [],
        "Created": "2025-04-28T15:19:02.536847314Z",
        "DockerVersion": "",
        "Labels": {
            "org.opencontainers.image.created": "2025-04-28T15:16:39.733Z",
            "org.opencontainers.image.description": "High performance self-hosted photo and video management solution.",
            "org.opencontainers.image.licenses": "AGPL-3.0",
            "org.opencontainers.image.revision": "02994883fe3f3972323bb6759d0170a4062f5236",
            "org.opencontainers.image.source": "https://github.com/immich-app/immich",
            "org.opencontainers.image.title": "immich",
            "org.opencontainers.image.url": "https://github.com/immich-app/immich",
            "org.opencontainers.image.version": "v1.132.3"
        },
        "Architecture": "amd64",
        "Os": "linux",
        "Layers": [
            "sha256:6e909acdb790c5a1989d9cfc795fda5a246ad6664bb27b5c688e2b734b2c5fad",
            "sha256:d714f4673cad3750083007b710a3d74ea21d34db71daaa04e44bafafb9d58445",
            "sha256:be84add755f800c3580c34f5f0e56856b96013886d9bfd3f08b0f0d957b77466",
            "sha256:9a8d89ceeab1eb03867d4edc7c38bf07c9277acb361a5973c71c00fb4d222901",
            "sha256:4c07c1809c8eebaab536b60272897848a5b72b4451b9e51bc7118d5aef302f75",
            "sha256:4b9ddc9fcd99e9db347badc9c25637cee42a9eef55cd98dd9127ceabbb0083e6",
            "sha256:8ccef78c3b11ec9325b13606a5eb1b02c25eef79418c3e6f771e0fcb78cbf6a9",
            "sha256:d7eef232885e3d757ad716cd1c48a86500e57e1573a36fee0bc60583b283cc7c",
            "sha256:b43bd143aa84d2c3ceca83a2bfb01805f98bf52d5838b3e9d17f7c15816d9197",
            "sha256:56c104725db98ef1a869a4703676e4e5ce20af6f4f66c7ff2506a5899124f0ee",
            "sha256:13004ec1a21ea8e0b0e9d11a16b1a4396841f08c4dc83ddadaf3faff2dffa8e7",
            "sha256:2220cab64ee511e7429b273793e52c1e21d01b8028a05fc7652e5fbe4a2012d5",
            "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1",
            "sha256:3f8be4c489f5f5f1e201a82e66db04d5dae3041c12227bd503c5dadb013d7c99",
            "sha256:eb98cc321ff0c685e1a8062ecbcd04be27474eef1b1c3c7193cb4a3e32f2f1fb",
            "sha256:96f756e9c69d48f87d21162a0801eb70bbbf9577a00d0482f2c261ccbf0528ab",
            "sha256:22014be2f2d658af3036a345ff26cc65506c45e431cfc32d7fa6d8c0aef49007",
            "sha256:238e9536a299e4c7052fd63791600eab2d63ad376d66d15d6b9855a3a4e2084a",
            "sha256:ea667375bd871346e26733c4b5d1438cd8249c8b85bdd443961d8bf5fd92afc3",
            "sha256:66801314ef77cbe2c26b04d2ea1e2171dff2691380dae91a619b11a5236da236",
            "sha256:db50dc8e4251d4f730c716561b0675451dbefebbd04255d68230711031b61458",
            "sha256:29338c290ecd511ebf187eda21bf7a9c1747b31ebebadb3755e60e6ea0611902",
            "sha256:672a94486b6da8572fb2d20b18fcdd688546b663d6417fb309e23320213d199a",
            "sha256:002db8e47c9205492274e9bb45277fe25c53034eb643188d1cc50a7ede449c82"
        ],
        "LayersData": [
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:6e909acdb790c5a1989d9cfc795fda5a246ad6664bb27b5c688e2b734b2c5fad",
                "Size": 28204865,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:d714f4673cad3750083007b710a3d74ea21d34db71daaa04e44bafafb9d58445",
                "Size": 3313,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:be84add755f800c3580c34f5f0e56856b96013886d9bfd3f08b0f0d957b77466",
                "Size": 48314646,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:9a8d89ceeab1eb03867d4edc7c38bf07c9277acb361a5973c71c00fb4d222901",
                "Size": 1712503,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:4c07c1809c8eebaab536b60272897848a5b72b4451b9e51bc7118d5aef302f75",
                "Size": 448,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:4b9ddc9fcd99e9db347badc9c25637cee42a9eef55cd98dd9127ceabbb0083e6",
                "Size": 95,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:8ccef78c3b11ec9325b13606a5eb1b02c25eef79418c3e6f771e0fcb78cbf6a9",
                "Size": 1323,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:d7eef232885e3d757ad716cd1c48a86500e57e1573a36fee0bc60583b283cc7c",
                "Size": 382083236,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:b43bd143aa84d2c3ceca83a2bfb01805f98bf52d5838b3e9d17f7c15816d9197",
                "Size": 39868218,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:56c104725db98ef1a869a4703676e4e5ce20af6f4f66c7ff2506a5899124f0ee",
                "Size": 17669160,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:13004ec1a21ea8e0b0e9d11a16b1a4396841f08c4dc83ddadaf3faff2dffa8e7",
                "Size": 132,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:2220cab64ee511e7429b273793e52c1e21d01b8028a05fc7652e5fbe4a2012d5",
                "Size": 7871,
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
                "Digest": "sha256:3f8be4c489f5f5f1e201a82e66db04d5dae3041c12227bd503c5dadb013d7c99",
                "Size": 154002319,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:eb98cc321ff0c685e1a8062ecbcd04be27474eef1b1c3c7193cb4a3e32f2f1fb",
                "Size": 795455,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:96f756e9c69d48f87d21162a0801eb70bbbf9577a00d0482f2c261ccbf0528ab",
                "Size": 645,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:22014be2f2d658af3036a345ff26cc65506c45e431cfc32d7fa6d8c0aef49007",
                "Size": 15459652,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:238e9536a299e4c7052fd63791600eab2d63ad376d66d15d6b9855a3a4e2084a",
                "Size": 6500,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:ea667375bd871346e26733c4b5d1438cd8249c8b85bdd443961d8bf5fd92afc3",
                "Size": 153318,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:66801314ef77cbe2c26b04d2ea1e2171dff2691380dae91a619b11a5236da236",
                "Size": 622,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:db50dc8e4251d4f730c716561b0675451dbefebbd04255d68230711031b61458",
                "Size": 614,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:29338c290ecd511ebf187eda21bf7a9c1747b31ebebadb3755e60e6ea0611902",
                "Size": 1061633,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:672a94486b6da8572fb2d20b18fcdd688546b663d6417fb309e23320213d199a",
                "Size": 11146,
                "Annotations": None
            },
            {
                "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "Digest": "sha256:002db8e47c9205492274e9bb45277fe25c53034eb643188d1cc50a7ede449c82",
                "Size": 11102,
                "Annotations": None
            }
        ],
        "Env": [
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/src/app/bin",
            "NODE_VERSION=22.14.0",
            "YARN_VERSION=1.22.22",
            "LD_LIBRARY_PATH=/usr/lib/jellyfin-ffmpeg/lib:/usr/lib/wsl/lib:",
            "NODE_ENV=production",
            "NVIDIA_DRIVER_CAPABILITIES=all",
            "NVIDIA_VISIBLE_DEVICES=all",
            "IMMICH_BUILD=14709928600",
            "IMMICH_BUILD_URL=https://github.com/immich-app/immich/actions/runs/14709928600",
            "IMMICH_BUILD_IMAGE=v1.132.3",
            "IMMICH_BUILD_IMAGE_URL=https://github.com/immich-app/immich/pkgs/container/immich-server",
            "IMMICH_REPOSITORY=immich-app/immich",
            "IMMICH_REPOSITORY_URL=https://github.com/immich-app/immich",
            "IMMICH_SOURCE_REF=v1.132.3",
            "IMMICH_SOURCE_COMMIT=02994883fe3f3972323bb6759d0170a4062f5236",
            "IMMICH_SOURCE_URL=https://github.com/immich-app/immich/commit/02994883fe3f3972323bb6759d0170a4062f5236"
        ]
    }

}


class Skopeo(MockTool):
    name: str = "skopeo"

    def run(self, argv: list[str]) -> Action:
        match argv[1:]:
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
