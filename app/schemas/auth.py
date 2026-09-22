from pydantic import BaseModel


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