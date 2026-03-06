from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class SegmentResponse(BaseModel):
    """
    id: record id
    hrs: hours worked
    rt: hourly rate
    amt: computed amount (hrs * rt)
    desc: description of work
    created_at: when segment was recorded
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    hrs: float
    rt: float
    amt: float
    desc: str | None
    created_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("id is required")
        if not isinstance(value, int):
            raise ValueError("id must be an integer")
        if value < 1:
            raise ValueError("id must be positive")
        return value

    @field_validator("hrs")
    @classmethod
    def validate_hrs(cls, value: float) -> float:
        if value is None:
            raise ValueError("hrs is required")
        if value < 0:
            raise ValueError("hrs cannot be negative")
        return value

    @field_validator("rt")
    @classmethod
    def validate_rt(cls, value: float) -> float:
        if value is None:
            raise ValueError("rt is required")
        if value < 0:
            raise ValueError("rt cannot be negative")
        return value

    @field_validator("amt")
    @classmethod
    def validate_amt(cls, value: float) -> float:
        if value is None:
            raise ValueError("amt is required")
        return round(value, 2)

    @field_validator("desc")
    @classmethod
    def validate_desc(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if len(value) > 1024:
                raise ValueError("desc too long")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("created_at is required")
        return value


class AdjustmentResponse(BaseModel):
    """
    id: record id
    amt: adjustment amount (negative for deductions)
    rsn: reason for adjustment
    created_at: when adjustment was made
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    amt: float
    rsn: str | None
    created_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("id is required")
        if not isinstance(value, int):
            raise ValueError("id must be an integer")
        if value < 1:
            raise ValueError("id must be positive")
        return value

    @field_validator("amt")
    @classmethod
    def validate_amt(cls, value: float) -> float:
        if value is None:
            raise ValueError("amt is required")
        return round(value, 2)

    @field_validator("rsn")
    @classmethod
    def validate_rsn(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if len(value) > 1024:
                raise ValueError("rsn too long")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("created_at is required")
        return value


class WorklogResponse(BaseModel):
    """
    id: record id
    user_id: worker uuid
    task_name: name of the task
    desc: task description
    amt: total computed amount (segments + adjustments)
    rmtnc_sts: remittance status (REMITTED / UNREMITTED)
    segments: list of time segments
    adjustments: list of adjustments
    created_at: when worklog was created
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: str
    task_name: str
    desc: str | None
    amt: float
    rmtnc_sts: str
    segments: list[SegmentResponse]
    adjustments: list[AdjustmentResponse]
    created_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("id is required")
        if not isinstance(value, int):
            raise ValueError("id must be an integer")
        if value < 1:
            raise ValueError("id must be positive")
        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        if value is None:
            raise ValueError("user_id is required")
        if not isinstance(value, str):
            raise ValueError("user_id must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("user_id cannot be empty")
        return value

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, value: str) -> str:
        if value is None:
            raise ValueError("task_name is required")
        if not isinstance(value, str):
            raise ValueError("task_name must be a string")
        value = value.strip()
        if len(value) == 0:
            raise ValueError("task_name cannot be empty")
        if len(value) > 255:
            raise ValueError("task_name too long")
        return value

    @field_validator("desc")
    @classmethod
    def validate_desc(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if len(value) > 1024:
                raise ValueError("desc too long")
        return value

    @field_validator("amt")
    @classmethod
    def validate_amt(cls, value: float) -> float:
        if value is None:
            raise ValueError("amt is required")
        return round(value, 2)

    @field_validator("rmtnc_sts")
    @classmethod
    def validate_rmtnc_sts(cls, value: str) -> str:
        if value is None:
            raise ValueError("rmtnc_sts is required")
        if value not in ("REMITTED", "UNREMITTED"):
            raise ValueError("rmtnc_sts must be REMITTED or UNREMITTED")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("created_at is required")
        return value


class WorklogListResponse(BaseModel):
    """
    data: list of worklogs
    cnt: total count
    """

    data: list[WorklogResponse]
    cnt: int

    @field_validator("cnt")
    @classmethod
    def validate_cnt(cls, value: int) -> int:
        if value is None:
            raise ValueError("cnt is required")
        if value < 0:
            raise ValueError("cnt cannot be negative")
        return value


class RemittanceDetail(BaseModel):
    """
    id: remittance record id
    user_id: worker uuid
    ttl_amt: total amount
    sts: remittance status
    created_at: when remittance was created
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: str
    ttl_amt: float
    sts: str
    created_at: datetime

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: int) -> int:
        if value is None:
            raise ValueError("id is required")
        if not isinstance(value, int):
            raise ValueError("id must be an integer")
        if value < 1:
            raise ValueError("id must be positive")
        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        if value is None:
            raise ValueError("user_id is required")
        value = str(value).strip()
        if len(value) == 0:
            raise ValueError("user_id cannot be empty")
        return value

    @field_validator("ttl_amt")
    @classmethod
    def validate_ttl_amt(cls, value: float) -> float:
        if value is None:
            raise ValueError("ttl_amt is required")
        return round(value, 2)

    @field_validator("sts")
    @classmethod
    def validate_sts(cls, value: str) -> str:
        if value is None:
            raise ValueError("sts is required")
        allowed = {"PENDING", "COMPLETED", "FAILED", "CANCELLED"}
        if value not in allowed:
            raise ValueError(f"sts must be one of {allowed}")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        if value is None:
            raise ValueError("created_at is required")
        return value


class GenerateRemittancesResponse(BaseModel):
    """
    msg: summary message
    cnt: number of remittances created
    remittances: list of created remittances
    """

    msg: str
    cnt: int
    remittances: list[RemittanceDetail]

    @field_validator("msg")
    @classmethod
    def validate_msg(cls, value: str) -> str:
        if value is None:
            raise ValueError("msg is required")
        if not isinstance(value, str):
            raise ValueError("msg must be a string")
        return value

    @field_validator("cnt")
    @classmethod
    def validate_cnt(cls, value: int) -> int:
        if value is None:
            raise ValueError("cnt is required")
        if value < 0:
            raise ValueError("cnt cannot be negative")
        return value
