import tempfile
from pathlib import Path

from cipug.env import Env


def test_load_parse_store():
    with tempfile.TemporaryDirectory() as tmpdirname:
        env_file: Path = Path(tmpdirname) / ".env"

        env_file.write_text("""
A_VALUE=hello

ANOTHER=world
# Comment
MULTI_LINE=can \
have \
line \
breaks
              # whitespace
VALUE_WITH_WHITESPACE= <- there
CONFUSING=there_is_\
another_=_in_here!
""")
        env = Env(env_file)
        assert env["A_VALUE"] == "hello"
        assert env["ANOTHER"] == "world"
        assert env["MULTI_LINE"] == "can have line breaks"
        assert env["VALUE_WITH_WHITESPACE"] == " <- there"
        assert env["CONFUSING"] == "there_is_another_=_in_here!"

        assert not env.has_changes()
        env["ANOTHER"] = "goodbye"
        assert env.has_changes()

        env.write()
        assert not env.has_changes()

        assert env_file.read_text() == (
            "A_VALUE=hello\n"
            "ANOTHER=goodbye\n"
            "MULTI_LINE=can have line breaks\n"
            "VALUE_WITH_WHITESPACE= <- there\n"
            "CONFUSING=there_is_another_=_in_here!"
        )
