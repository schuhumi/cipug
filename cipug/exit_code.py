
class Exit_Code:
    code: int
    def __init__(self, code: int):
        for v in globals().values():
            if not isinstance(v, self.__class__):
                continue
            if v.code == code:
                raise ValueError(f"Exit code {code} is already taken by {v.name}")

        self.code = code

    @property
    def name(self) -> str:
        return [k for k,v in globals().items() if v is self].pop()


# When exiting the program, we can only return one value. -1 (=255) serves as an
# indicator that there were more than one reason for signaling failure.
MULTIPLE_ERRORS = Exit_Code(-1)


SYSTEM_ERROR = Exit_Code(10)

FILE_NOT_FOUND = Exit_Code(20)
DIRECTORY_NOT_FOUND = Exit_Code(21)
UNKNOWN_FILE_FORMAT = Exit_Code(22)
UNKOWN_DATA_STRUCTURE = Exit_Code(23)
TYPE_ERROR = Exit_Code(24)
VALUE_ERROR = Exit_Code(25)


TOOL_ERROR = Exit_Code(30)
SNAPSHOT_ERROR = Exit_Code(31)
ENV_ERROR = Exit_Code(32)
IMAGE_PULL_ERROR = Exit_Code(33)
SERVICE_RESTART_ERROR = Exit_Code(34)

SNAPSHOTS_NOK = Exit_Code(40)
