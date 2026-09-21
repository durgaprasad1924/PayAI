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