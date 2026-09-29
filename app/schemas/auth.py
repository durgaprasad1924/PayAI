from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    identifier: str
    channel: str
    purpose: str

class OTPVerifyRequest(BaseModel):
    identifier: str
    channel: str
    purpose: str
    otp: str

class RegistrationStartRequest(BaseModel):
    phone: str


class RegistrationPhoneVerifyRequest(BaseModel):
    registration_token: str
    otp: str

class RegistrationDetailsRequest(BaseModel):
    registration_token: str
    name: str
    email: str

class RegistrationEmailVerifyRequest(BaseModel):
    registration_token: str
    otp: str

class LoginRequest(BaseModel):
    identifier: str
    channel: str

class LoginVerifyRequest(BaseModel):
    identifier: str
    channel: str
    otp: str

class SetMPINRequest(BaseModel):
    mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )

    confirm_mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )