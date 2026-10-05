from pydantic import BaseModel, Field
from decimal import Decimal

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
    device_id: str

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

class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str | None = None
    platform: str

class MPINLoginRequest(BaseModel):
    device_id: str
    mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )


class TransferRequest(BaseModel):
    receiver_phone: str
    amount: Decimal = Field(gt=0)
    mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )

class ChangeMPINRequest(BaseModel):
    current_mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )

    new_mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )

    confirm_mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )

class MPINResetRequest(BaseModel):
    phone: str


class MPINResetVerifyRequest(BaseModel):
    phone: str
    otp: str


class MPINResetConfirmRequest(BaseModel):
    reset_token: str

    new_mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )

    confirm_mpin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )