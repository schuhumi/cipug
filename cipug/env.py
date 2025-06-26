from pathlib import Path
import copy

from cipug.log import log

class Env(dict):
    """Handle .env files for compose. This includes:
        - loading .env file as dictionary
        - changing entries
        - knowing if any entries where changed
        - writing back to disk
    """
    def __init__(self, path: Path):
        self.path = path  # Remember for writing back to disk
        with open(path, "r") as f:
            # .env file entries can be multiple lines, by adding \ before line ends.
            # If we find such a line, use the following variable to remember which
            # entry to append the next line to.
            key_to_append_next_line_to = None
            key = None
            for line_ctr, line in enumerate(f):
                line = line.rstrip("\n")
                if key_to_append_next_line_to is None:
                    # There was no \ at the end of the previous line -> new entry
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
