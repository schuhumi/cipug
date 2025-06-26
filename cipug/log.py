import sys
from typing import NoReturn, overload

from .colors import colors

class log():
    """Simple logging functionality, use:
    log("message") for normal output
    log.error("message", exit_code) for errors on stderr with optional exiting
    log.[v]verbose("message") for [very] verbose logs
    """
    verbosity=1 # default, gets overwritten in Config.load_from_env()

    def __new__(cls, msg: str, verbosity: int = 1, highlight: bool = False):
        if cls.verbosity>=verbosity:
            if highlight:
                print(f"{colors.Yellow}{msg}{colors.Reset}")
                return
            print(msg)

    @classmethod
    @overload
    def error(cls, msg: str):
        ...

    @classmethod
    @overload
    def error(cls, msg: str, exit_code: int) -> NoReturn:
        ...

    @classmethod
    def error(cls, msg: str, exit_code: int = 0) -> NoReturn | None:
        print(f"{colors.Bold}{colors.Red}{msg}{colors.Reset}", file=sys.stderr)
        if exit_code:
            sys.exit(exit_code)

    @classmethod
    def verbose(cls, msg: str):
        cls(f"{colors.Dim}{msg}{colors.Reset}", verbosity=2)

    @classmethod
    def vverbose(cls, msg: str):
        cls(f"{colors.Dim}{msg}{colors.Reset}", verbosity=3)
