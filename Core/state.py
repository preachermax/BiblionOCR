from enum import Enum


class ProjectState(Enum):
    INIT = "INIT"
    VALIDATE = "VALIDATE"
    PROVENANCE = "PROVENANCE"
    RIS = "RIS"
    WRITE = "WRITE"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"