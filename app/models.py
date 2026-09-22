from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    email_verified = Column(Boolean,nullable=False,default=False)
    phone = Column(String(20),unique=True,nullable=True)
    phone_verified = Column(Boolean,nullable=False,default=False)

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=0) 


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True)
    sender_wallet_id = Column(Integer,ForeignKey("wallets.id"),nullable=False)
    receiver_wallet_id = Column(Integer,ForeignKey("wallets.id"),nullable=False)
    amount = Column(Numeric(12, 2),nullable=False)
    status = Column(String(20),nullable=False,default="COMPLETED")
    idempotency_key = Column(String(100),unique=True,nullable=False)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer,ForeignKey("wallets.id"),nullable=False)
    transfer_id = Column(Integer,ForeignKey("transfers.id"),nullable=True)
    transaction_type = Column(String(20),nullable=False)
    transaction_role = Column(String(20),nullable=True)
    amount = Column(Numeric(12, 2),nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False,default=lambda: datetime.now(timezone.utc))

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=True)
    identifier = Column(String(255),nullable=False)
    channel = Column(String(10),nullable=False)
    purpose = Column(String(30),nullable=False)
    otp_hash = Column(String(255),nullable=False)
    expires_at = Column(DateTime(timezone=True),nullable=False)
    attempts = Column(Integer,nullable=False,default=0)
    used_at = Column(DateTime(timezone=True),nullable=True)
    created_at = Column(DateTime(timezone=True),nullable=False,default=lambda: datetime.now(timezone.utc))


class RegistrationChallenge(Base):
    __tablename__ = "registration_challenges"

    id = Column(Integer, primary_key=True)
    registration_token = Column(String(255),unique=True,nullable=False)
    phone = Column(String(20),unique=True,nullable=False)
    phone_verified = Column(Boolean,nullable=False,default=False)
    name = Column(String(100),nullable=True)
    email = Column(String(255),nullable=True)
    email_verified = Column(Boolean,nullable=False,default=False)
    status = Column(String(20),nullable=False,default="IN_PROGRESS")
    expires_at = Column(DateTime(timezone=True),nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    