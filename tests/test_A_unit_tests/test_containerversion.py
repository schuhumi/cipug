from cipug.tools.version_modifier import ContainerVersion


def test_container_version_from_tagged_and_hashed():
    cn = ContainerVersion.from_tagged_and_hashed(
        None,
        "NEXTCLOUD",
        "nextcloud:latest",
        "docker.io/library/nextcloud@sha256:a9ef7ed15dbf3f9fcf6dc2a41a15af572fcc077f220640cabfe574a3ffbf5766"
    )
    assert cn.resolver is None
    assert cn.name == "NEXTCLOUD"
    assert cn.image == "docker.io/library/nextcloud"
    assert cn.tag == "latest"
    assert cn.hash_current == "a9ef7ed15dbf3f9fcf6dc2a41a15af572fcc077f220640cabfe574a3ffbf5766"

    cn = ContainerVersion.from_tagged_and_hashed(
        None,
        "",
        "vaultwarden/server:latest",
        "docker.io/vaultwarden/server@sha256:43498a94b22f9563f2a94b53760ab3e710eefc0d0cac2efda4b12b9eb8690664",
    )
    assert cn.image == "docker.io/vaultwarden/server"
    assert cn.tag == "latest"
    assert cn.hash_current == "43498a94b22f9563f2a94b53760ab3e710eefc0d0cac2efda4b12b9eb8690664"
