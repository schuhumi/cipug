from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path

from cipug.resolver import Image_Version_Resolver
from cipug.service import Service
from cipug.tools.version_modifier import ContainerVersion, VersionModifierTool


class SystemdUnitEntry(ABC):
    @abstractmethod
    def __str__(self) -> str:
        ...

class SystemdUnitKeyValue(SystemdUnitEntry):
    name: str
    value: str

    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return f"{self.name}={self.value}"

class SystemdUnitCipugKeyValue(SystemdUnitKeyValue):
    def __str__(self) -> str:
        return f"#cipug:{self.name}={self.value}"

class SystemdUnitComment(SystemdUnitEntry):
    content: str

    def __init__(self, content: str):
        self.content = content

    def __str__(self) -> str:
        return f"#{self.content}"

class SystemdUnitEmptyLine(SystemdUnitEntry):
    def __str__(self) -> str:
        return ""

class SystemdUnitFile:
    sections: OrderedDict[str, list[SystemdUnitEntry]]

    def add_to_section(self, section: str, entry: SystemdUnitEntry):
        if section not in self.sections.keys():
            self.sections[section] = []
        self.sections[section].append(entry)

    def __init__(self, path: Path):
        self.sections = OrderedDict()
        self.path = path  # Remember for writing back to disk
        with open(path) as f:
            key: str | None = None
            section: str = ""
            line_continues = False
            line = ""
            for line_ctr, thisline in enumerate(f):
                if thisline.endswith("\\\n"):  # concat multiline
                    if line_continues:
                        line += thisline
                    else:
                        line = thisline
                    line_continues = True
                    continue
                else:
                    if line_continues:
                        line += thisline
                    else:
                        line = thisline
                    line_continues = False
                line = line.rstrip("\n")
                line_strip = line.strip()
                if line_strip.startswith("[") and line_strip.endswith("]"):  # section
                    section = line_strip.removeprefix("[").removesuffix("]")
                    continue
                if line_strip == "":
                    self.add_to_section(section, SystemdUnitEmptyLine())
                    continue
                if line_strip.startswith("#") and not line_strip.startswith("#cipug:"):  # comments
                    self.add_to_section(section, SystemdUnitComment(line[1:]))
                    continue
                if "=" in line:
                    key, val = line_strip.split("=", 1)
                    if key.startswith("#cipug:"):
                        self.add_to_section(section, SystemdUnitCipugKeyValue(
                            key.removeprefix("#cipug:").strip(),
                            val
                        ))
                    else:
                        self.add_to_section(section, SystemdUnitKeyValue(key.strip(), val))
                    continue
                raise ValueError(f"{self.path}: Failed to parse line {line_ctr}: {line}")

    def __str__(self) -> str:
        s = ""
        for section, entries in self.sections.items():
            if section != "":
                s += f"[{section}]\n"
            for entry in entries:
                s += str(entry) + "\n"
        return s

    def write(self, path: Path | None = None):
        if path is None:
            # No specific location set: write back to where we read it from
            path = self.path
        path.write_text(str(self))

    def has_changes(self) -> bool:
        return str(self) != self.path.read_text()


class ContainerFile(SystemdUnitFile):
    @property
    def container(self) -> list[SystemdUnitEntry]:
        sec = self.sections.get("Container", None)
        if sec is None:
            raise ValueError("[Container] section missing")
        return sec

    @property
    def image_tagged(self) -> str | None:
        for entry in self.container:
            if isinstance(entry, SystemdUnitCipugKeyValue) and entry.name=="ImageTagged":
                return entry.value
        return None

    @image_tagged.setter
    def image_tagged(self, value: str) -> None:
        for entry in self.container:
            if isinstance(entry, SystemdUnitCipugKeyValue) and entry.name=="ImageTagged":
                entry.value = value
                return
        # entry doesn't exist yet
        self.container.append(SystemdUnitCipugKeyValue("ImageTagged", value))

    @property
    def image_hashed(self) -> str | None:
        for entry in self.container:
            if isinstance(entry, SystemdUnitKeyValue) and entry.name=="Image":
                return entry.value
        return None

    @image_hashed.setter
    def image_hashed(self, value: str) -> None:
        for entry in self.container:
            if isinstance(entry, SystemdUnitKeyValue) and entry.name=="Image":
                entry.value = value
                return
        # entry doesn't exist yet
        self.container.append(SystemdUnitKeyValue("Image", value))

    @property
    def container_name(self) -> str:
        for entry in self.container:
            if isinstance(entry, SystemdUnitKeyValue) and entry.name=="ContainerName":
                return entry.value + ".service"
        return self.path.stem + ".service"


class Quadlet(VersionModifierTool):
    @classmethod
    def assert_dependencies(cls):
        # We don't have any dependencies
        return

    @classmethod
    def check_if_folder_is_service(cls, path: Path) -> bool:
        if not path.is_dir():
            return False
        if len(list(path.glob("*.container"))) == 0:
            return False
        return True

    def __init__(
        self,
        svc: Service,
        resolver: Image_Version_Resolver,
    ) -> None:
        self.svc = svc
        self.resolver = resolver
        self.container_files: dict[str, ContainerFile] = {  # by name
            each.name: ContainerFile(each) for each in self.svc.path.glob("*.container")
        }
        self.container_versions: list[ContainerVersion] = []
        for name, cf in self.container_files.items():
            if cf.image_tagged is None:
                raise ValueError(f"{cf.path} is missing '#cipug:ImageTagged=...' variable")
            self.container_versions.append(
                ContainerVersion.from_tagged_and_hashed(
                    resolver=self.resolver,
                    name=name,
                    tagged=cf.image_tagged,
                    hashed=cf.image_hashed,
                )
            )

    def _store_next_hashes(self) -> None:
        for cv in self.container_versions:
            cf = self.container_files[cv.name]
            cf.image_hashed = cv.hashed_next
            cf.write()
