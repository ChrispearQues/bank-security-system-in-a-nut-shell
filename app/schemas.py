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
