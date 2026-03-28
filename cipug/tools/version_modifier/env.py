import copy
import re
from pathlib import Path

from cipug.config import Config
from cipug.log import log
from cipug.resolver import Image_Version_Resolver
from cipug.service import Service

from .base import ContainerVersion, VersionModifierTool


class EnvFile(dict[str, str]):
    """Handle .env files for compose. This includes:
        - loading .env file as dictionary
        - changing entries
        - knowing if any entries where changed
        - writing back to disk
    """
    def __init__(self, path: Path):
        self.path = path  # Remember for writing back to disk
        with open(path) as f:
            # .env file entries can be multiple lines, by adding \ before line ends.
            # If we find such a line, use the following variable to remember which
            # entry to append the next line to.
            key_to_append_next_line_to = None
            key = None
            for line_ctr, line in enumerate(f):
                line = line.rstrip("\n")
                if key_to_append_next_line_to is None:
                    # There was no \ at the end of the previous line -> new entry
                    if line.strip() == "":  # Ignore empty lines
                        continue
                    if line.strip().startswith("#"):  # Ignore comments
                        continue
                    key, val = line.split("=", 1)
                    self[key] = val
                    if line[-1]=="\\":
                        key_to_append_next_line_to = key
                elif key is not None:
                    # There was a \ at the end of the previous line
                    # -> line belongs to previous key
                    self[key] += "\n" + line
                    if line[-1]!="\\":
                        key_to_append_next_line_to = None
                else:
                    # There was a \ at the end of the previous line, but we don't
                    # have a previous key where this line belongs to
                    log.error(f"Cannot append line {line_ctr} of .env to previous line.")

        # Remember the the state of the .env on disk. This way we later know
        # whether we need to write updates back to disk
        self.diskstate = {key:copy.copy(val) for key, val in self.items()}

        log.vverbose(f"Loaded environment file {path}: \n{'-'*10}\n{self}\n{'-'*10}")

    def has_changes(self):
        for key in self.keys():
            if key not in self.diskstate:
                return True
            if self[key] != self.diskstate[key]:
                return True
        for key in self.diskstate.keys():
            if key not in self:
                return True
        return False

    def write(self, path: Path | None = None):
        if path is None:
            # No specific location set: write back to where we read it from
            path = self.path
        with open(path, "w") as f:
            f.write("\n".join([
                f"{key}={val}" for key, val in self.items()
            ]))
            self.diskstate = {key:copy.copy(val) for key, val in self.items()}

    def __str__(self):
        return "\n".join([
            f"{key}={val}" for key, val in self.items()
        ])


# Check for environment variables in the tagged image (${VAR} format)
def replace_env_vars(s: str, vars: dict[str, str]):
    def replace_var(match: re.Match[str]) -> str:
        var_name: str = match.group(1)
        fallback: str = match.group(0)
        return vars.get(var_name, fallback)

    pattern = r"\${([A-Za-z0-9_]+)}"
    return re.sub(pattern, replace_var, s)


class Env(VersionModifierTool):
    @classmethod
    def assert_dependencies(cls):
        # We don't have any dependencies
        return

    @classmethod
    def check_if_folder_is_service(cls, path: Path) -> bool:
        config = Config()
        if not path.is_dir():
            return False
        if not (path / config["COMPOSE_FILE_NAME"]).is_file():
            return False
        if not (path / config["ENV_FILE_NAME"]).is_file():
            return False
        return True

    def __init__(
        self,
        svc: Service,
        resolver: Image_Version_Resolver,
    ) -> None:
        self.config = Config()
        self.svc = svc
        self.resolver = resolver
        log.vverbose(
            f"Searching {self.config['ENV_FILE_NAME']} for SERVICE_*_IMAGE_TAGGED "
            "entries that should get resolved to SERVICE_*_IMAGE_HASHED entries."
        )
        self.file = EnvFile(svc.path / self.config["ENV_FILE_NAME"])
        self.container_versions: list[ContainerVersion] = []
        for variable, value in self.file.items():
            if variable.startswith("SERVICE_") and variable.endswith("_IMAGE_TAGGED"):
                name = variable.removeprefix("SERVICE_").removesuffix("_IMAGE_TAGGED")
                tagged = value

                # Apply environment variable substitution
                interpolated_image = replace_env_vars(tagged, self.file)
                if interpolated_image != tagged:
                    log.verbose(f"Interpolated image name: {tagged} → {interpolated_image}")
                    tagged = interpolated_image

                log.verbose(f'Found tagged image entry for "{name}": {tagged}')

                hashed_current = self.file.get(f"SERVICE_{name}_IMAGE_HASHED", None)
                if hashed_current is None:
                    log.verbose(
                        f'There\'s no hashed image reference for "{name}"'
                        f" in {self.config['ENV_FILE_NAME']} currently"
                    )
                else:
                    log.verbose(f'The current hashed image reference for "{name}" is: {hashed_current}')

                self.container_versions.append(
                    ContainerVersion.from_tagged_and_hashed(
                        resolver = self.resolver,
                        name = name,
                        tagged = tagged,
                        hashed = hashed_current
                    )
                )

    def _store_next_hashes(self) -> None:
        for cv in self.container_versions:
            self.file[f"SERVICE_{cv.name}_IMAGE_HASHED"] = cv.hashed_next
        self.file.write()
