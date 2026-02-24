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
