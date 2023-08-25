# cipug

The **c**ontainer **i**mages **p**inning and **u**pdating **g**adget, designed to work with compose.

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

## Installation

You need to have skopeo, snapper and docker-compose or podman-compose installed. You need to organize your services in the way that is described in the "How it works" section. And you need Python >= 3.10 to run cipug.py, but no virtual environment with additional dependencies. It all works with what is included in Python :)


## Configuration

Due to questionable decisions by its developer, cipug has no support for command line arguments. It is controlled by environment variables and optionally a config file. If you need just one set of configuration and do not want to prepend the command with it, you can put that in a global environment variable config file like `/etc/environment` and reboot. If you want to have specific configuration files, you can populate an arbitrary json-file with a list of similar key-value pairs, and pass that using the `CIPUG_CONFIG_FILE` environment variable. You need to omit the `CIPUG_` prefix, hence the configuration file could look like this for example:
```json
{
    "SERVICES_ROOT": "/path/to/some/folder",
    "SERVICE_STOP_START": false
}
```
You can then run cipug like this:
```
$ CIPUG_CONFIG_FILE=/path/to/cipug-config.json /path/to/cipug.py
```


## Environment Variables

Name | Purpose | Values | Default
---|---|---|---
`CIPUG_CONFIG_FILE` | [Optional] Specify a json file where the remaining settings should be read from | some path | *unset*
`CIPUG_SERVICES_ROOT` | Folder where subvolumes with each a service in them reside | some absolute path | *unset*
`CIPUG_COMPOSE_FILE_NAME` | What compose file to look out for at each service | Just the filename. This means all services need to have the same compose-file filename! | `compose.yml`
`CIPUG_ENV_FILE_NAME` | What environment file to look out for at each service | Just the filename. This means all services need to have the same environment-file filename! | `.env`
`CIPUG_COMPOSE_TOOL` | Used to stop (`down`) and start (`up -d`) services | `podman-compose`, `docker-compose` or any other such tool| `podman-compose`
`CIPUG_SERVICE_STOP_START` | Whether to stop services before and start them up again after an image update | `true`/`false`, `0/`/`1` or `yes`/`no` (case insensitive) | `true`
`CIPUG_SERVICE_SNAPSHOT` | Whether to create a snapshot using snapper before setting up a new container image | `true`/`false`, `0/`/`1` or `yes`/`no` (case insensitive) | `true`
`CIPUG_VERBOSITY` | Sets exhaustiveness of logs | `0` = just errors, `1` = normal, `2` = verbose, `3` = highly verbose | `1`
`CIPUG_CACHE_DURATION` | cipug caches image-tag resolutions to not exhaust docker-hub's rate limit so quickly | integer amount of seconds | `3600` (1h)
`CIPUG_CACHE_LOCATION` | location where to store the cache in the form of a json file | some path | `<tmp-directory>/cipug_cache.json` 



