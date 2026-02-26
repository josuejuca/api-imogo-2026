from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=30)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    origin: int
    device: int


class RegisterResponse(BaseModel):   
    public_id: str
    message: str

class SocialAuthRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=50)
    type: str = Field(min_length=2, max_length=50)
    provider_id: str = Field(min_length=1, max_length=255)
    email: EmailStr
    device: int
    photo_url: str | None = Field(default=None, max_length=255)
    name: str = Field(min_length=2, max_length=120)

class SocialAuthResponse(BaseModel):
    token: str
    key: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginResponse(BaseModel):
    token: str
    key: str


class RenewResponse(BaseModel):
    token: str


class MeResponse(BaseModel):
    photo: str
    phone: str
    email: EmailStr
    name: str
    status: int
    public_id: str
    profile: int
