from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)


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

