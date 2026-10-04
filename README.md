# cipug

The **c**ontainer **i**mages **p**inning and **u**pdating **g**adget, designed to work with podman or docker compose and quadlet.

*But, what is it for?*

If you host a couple of services on a server through podman- or docker-compose, you'll have compose files with `image: ...` references in there. If you're of the lazy & adventureous kind, you'll likely use images with the `:latest` tag, such that you always get the newest images. **But what if your service breaks after pulling a new image?**

Hopefully you did a btrfs-snapshot of the data before, but maybe not? And what image where you running before? The `:latest` from - mhmm - a month ago? What version was that?

cipug is here to help!


## How it works

In a nutshell, you run cipug regularly and every time it checks what image tags like `:latest` resolve to, and if there is a new "latest" container it snapshots the respective service, stops it, replaces the hash-based image-reference, and starts up the service again. That way, you can roll back to a previous snapshot and have both the data and the container from that point in time.

To work, cipug expects a folder structure similar to this (the .snapshots location could be a different one):
```
/mnt/data/services        <- one folder on a btrfs drive with all services
  + nextcloud             <- subvolume with one of possibly many services
    + .snapshots          <- where snapper puts nextcloud snapshots
    + compose.yml         <- for docker-compose or podman-compose
    + .env                <- cipug works on this
    + html-data           <- bind-mounted data that gets snapshotted too
    + sql-data            <- <same as html-data>
  + paperless-ngx
    + ...
  + ...
```

As an example, in your compose-file, instead of writing `image: nextcloud:latest` you write `image: ${SERVICE_NEXTCLOUD_IMAGE_HASHED}`. What image you want that to be, you specify in the .env file using `SERVICE_NEXTCLOUD_IMAGE_TAGGED=nextcloud:latest`.

When you run cipug, it recognizes entries in the `SERVICE_*_IMAGE_TAGGED` style in .env, and resolves them using skopeo. It then creates/updates the results in .env like this: `SERVICE_NEXTCLOUD_IMAGE_HASHED=docker.io/library/nextcloud@sha256:bbcaf...`. And that is how your compose-file knows which image it should use!

Besides from doing a snapshot and restarting the service, the big appeal with this is that you snapshot the digest-hash of the image as wel. And that is why you can roll back to that image later together with the data, should the update fail for some reason.

## Quadlet mode

Services can also be organized as systemd-quadlet units instead of compose files. Set `CIPUG_COMPOSE_TOOL=quadlet` and lay out each service like this:
```
/mnt/data/services
  + navidrome             <- service folder (this is what gets snapshotted)
    + quadlet             <- the unit files that cipug manages (CIPUG_QUADLET_DIR)
      + navidrome.container
    + data                <- bind-mounted data that gets snapshotted too
    + .snapshots
```
A folder counts as a service when its `quadlet` subfolder holds at least one `*.container` file.

In each `*.container` unit, cipug maintains the `Image=` key of the `[Container]` section as an immutable digest pin, and remembers the mutable tag that it should keep up-to-date in a comment line right next to it:
```
[Container]
#cipug:ImageTagged=docker.io/deluan/navidrome:latest
Image=docker.io/deluan/navidrome@sha256:9012939114fbb...
```

To make systemd find these files, cipug creates a symlink named after the service folder — `~/.config/containers/systemd/<service-name>.units -> <service>/quadlet` (location configurable via `CIPUG_QUADLET_INSTALL_DIR`) — and runs `systemctl --user daemon-reload`. Note that the quadlet generator derives the systemd unit name from the unit *file* (`whoami.container` → `whoami.service`), regardless of what `ContainerName=` says inside.

With every run cipug also tidies that symlink directory: links whose quadlet folder vanished (you got rid of a service) are removed, and links with a wrong name get renamed to the convention above. Removing means *only the symlink itself* — cipug never deletes files, directories, or symlink targets, and it leaves symlinks alone that don't point into your services tree.

A configuration for quadlet mode looks like this:
```json
{
    "SERVICES_ROOT": "/mnt/data/services",
    "COMPOSE_TOOL": "quadlet",
    "CONTAINER_TOOL": "podman"
}
```

## Installation

You need to have skopeo and snapper installed, plus either docker-compose or podman-compose (compose mode) or a recent podman with quadlet support and a running systemd user session (quadlet mode). You need to organize your services in the way that is described in the "How it works" and "Quadlet mode" sections. And you need Python >= 3.10 to run cipug.py, but no virtual environment with additional dependencies. It all works with what is included in Python :)

## Modes of Operation

 - `cipug.sh --update` or without arguments: perform updates as described above
 - `cipug.sh --check-snapshots`: check for existence of recent snapshots. Currently cipug supports snapper snapshots, [btrbk](https://github.com/digint/btrbk) snapshots and zfs snapshots. Their location relative to each service subvolume as well as their maximum allowed age can be configured with the variables below.
 - `cipug.sh --print-config` / `cipug.sh --print-config-json`: print the effective configuration (as text / as json) and exit

## Configuration

Due to questionable decisions by its developer, cipug is not being configured by command line arguments. It is controlled by environment variables and optionally a config file. If you need just one set of configuration and do not want to prepend the command with it, you can put that in a global environment variable config file like `/etc/environment` and reboot. If you want to have specific configuration files, you can populate an arbitrary json-file with a list of similar key-value pairs, and pass that using the `CIPUG_CONFIG_FILE` environment variable. You need to omit the `CIPUG_` prefix, hence the configuration file could look like this for example:
```json
{
    "SERVICES_ROOT": "/path/to/some/folder",
    "SERVICE_STOP_START": false
}
```
You can then run cipug like this:
```
$ CIPUG_CONFIG_FILE=/path/to/cipug-config.json /path/to/cipug.sh
```
When config values are present in both a config file and as environment variable, the environment variable has precedence.

## Configuration Variables

Name | Purpose | Values | Default
---|---|---|---
`CIPUG_CONFIG_FILE` | [Optional] Specify a json file where the remaining settings should be read from | Some path | *unset*
`CIPUG_SERVICES_ROOT` | Folder where subvolumes with each a service in them reside | Some absolute path | *unset*
`CIPUG_SERVICES_FILTER` | Only work on a subset of the services | Comma-separated list of service names that shall be considered | *unset*
`CIPUG_SERVICES_FILTER_EXCLUDE` | Only work on a subset of the services | Comma-separated list of service names that shall be ignored | *unset*
`CIPUG_COMPOSE_FILE_NAME` | What compose file to look out for at each service | Just the filename. This means all services need to have the same compose-file filename! | `compose.yml`
`CIPUG_ENV_FILE_NAME` | What environment file to look out for at each service | Just the filename. This means all services need to have the same environment-file filename! | `.env`
`CIPUG_COMPOSE_TOOL` | Which mode cipug runs in, and with that: how to stop and start services and where the image version pins live | `podman-compose`, `docker-compose`, `docker compose` (compose mode, `.env` pins) or `quadlet` (quadlet mode, `*.container` pins)| `podman-compose`
`CIPUG_QUADLET_DIR` | Name of the subfolder inside each service folder that contains the quadlet unit files (`*.container`, `*.network`, ...) | Just the folder name | `quadlet`
`CIPUG_QUADLET_INSTALL_DIR` | Where cipug creates and tidies the `<service-name>.units` symlinks pointing to each service's quadlet folder. Should be a location that the quadlet generator of the systemd user session scans | some path, `~` is expanded | `~/.config/containers/systemd`
`CIPUG_CONTAINER_TOOL` | Used to prune the images | `podman`, `docker` or any such tool | `podman`
`CIPUG_SERVICE_STOP_START` | Whether to stop services before and start them up again after an image update | `true`/`false`, `0/`/`1` or `yes`/`no` (case insensitive) | `true`
`CIPUG_STOP_START_METHOD` | Choose how to restart containers. This enables the use of systemd integration for podman compose. Ignored for `quadlet`, which always restarts via `systemctl --user` | `compose`: use `$CIPUG_COMPOSE_TOOL down` and `$CIPUG_COMPOSE_TOOL up -d`.<br/> `systemd-system` or `systemd-user`: use `systemctl [--user] restart $CIPUG_COMPOSE_TOOL@<service name>` | `compose`
`CIPUG_SERVICE_SNAPSHOT` | Whether to create a snapshot using snapper before setting up a new container image | `true`/`false`, `0/`/`1` or `yes`/`no` (case insensitive) | `true`
`CIPUG_PRUNE_IMAGES` | Whether to prune images | `true`/`false`, `0/`/`1` or `yes`/`no` (case insensitive) | `true`
`CIPUG_VERBOSITY` | Sets exhaustiveness of logs | `0` = just errors, `1` = normal, `2` = verbose, `3` = highly verbose | `1`
`CIPUG_CACHE_DURATION` | cipug caches image-tag resolutions to not exhaust docker-hub's rate limit so quickly | integer amount of seconds | `3600` (1h)
`CIPUG_CACHE_LOCATION` | location where to store the cache in the form of a json file | some path | `<tmp-directory>/cipug_cache.json`
`CIPUG_SNAPSHOTS_DIR_SNAPPER` and `CIPUG_SNAPSHOTS_DIR_BTRBK` | location of the respective snapshots | path relative to each service | *unset*
`CIPUG_SNAPSHOTS_ENABLE_ZFS` | whether snapshots are expected from zfs | `true`/`false`, `0`/`1` or `yes`/`no` (case insensitive) | `false`
`CIPUG_SNAPSHOTS_MAX_AGE_SNAPPER`, `CIPUG_SNAPSHOTS_MAX_AGE_BTRBK` and `CIPUG_SNAPSHOTS_MAX_AGE_ZFS` | maximum allowed age of snapshots | hours (integer or floating point) | `1.5`, `36` and `1.5`
