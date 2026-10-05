from datetime import datetime
from typing import Optional

# Request / response shapes (数据形状) shared by the routes.
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: str = Field(min_length=3, max_length=255)
    password: str


class LoginRequest(BaseModel):
    identifier: str = Field(description="Username or email")
    password: str


class OtpVerifyRequest(BaseModel):
    identifier: str = Field(description="Username or email")
    code: str = Field(min_length=6, max_length=6)


class OtpResendRequest(BaseModel):
    identifier: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpChallengeResponse(BaseModel):
    otp_required: bool = True
    detail: str = "A one-time code was sent."


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool


class AccountCreateRequest(BaseModel):
    account_type: str = "savings"
    currency: str = "HKD"


class AccountResponse(BaseModel):
    id: int
    account_number: str
    balance: float
    account_type: str
    currency: str
    status: str


class TransferRequest(BaseModel):
    from_account: str = Field(description="Source account number")
    to_account: str = Field(description="Destination account number")
    amount: float = Field(gt=0)
    idempotency_key: str = Field(
        min_length=8, max_length=64,
        description="Client-generated key; a replay with the same key is a no-op",
    )
    description: Optional[str] = None


class TransferResponse(BaseModel):
    outcome: str  # "new" | "replayed"
    reference: str
    amount: float
    from_account: str
    to_account: str


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    type: str
    amount: float
    balance_after: Optional[float]
    reference: Optional[str]
    status: str
    created_at: datetime


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: list[RoleResponse] = []


class AdminAccountResponse(AccountResponse):
    user_id: int


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity: Optional[str]
    entity_id: Optional[int]
    detail: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime


class RoleAssignRequest(BaseModel):
    name: str


class UserActiveRequest(BaseModel):
    is_active: bool
