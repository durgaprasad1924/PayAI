from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import RegistrationChallenge, User, OTPVerification, Wallet, WalletTransaction, Transfer, DateTime
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.schemas.auth import OTPRequest, OTPVerifyRequest, RegistrationStartRequest, RegistrationPhoneVerifyRequest, RegistrationDetailsRequest, RegistrationEmailVerifyRequest
from app.services.otp_service import generate_otp, hash_otp, verify_otp
from app.services.registration_service import generate_registration_token

app = FastAPI(title="PayAI")


class UserCreate(BaseModel):
    name: str
    email: str

class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)

class WithdrawRequest(BaseModel):
    amount: Decimal = Field(gt=0) 

class TransferRequest(BaseModel):
    sender_user_id: int
    receiver_user_id: int
    amount: Decimal = Field(gt=0)

@app.get("/")
def root():
    return {
        "message": "Welcome to PayAI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.post("/users")
def create_user(user: UserCreate):
    db = SessionLocal()

    try:
        new_user = User(
            name=user.name,
            email=user.email
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    finally:
        db.close()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }

    finally:
        db.close()

@app.get("/users")
def get_users():
    db = SessionLocal()

    try:
        users = db.query(User).all()

        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
            for user in users
        ]

    finally:
        db.close()


@app.post("/users/{user_id}/wallet")
def create_wallet(user_id: int):
    db = SessionLocal()

    try:
        # Check whether user exists
        user = db.get(User, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Check whether wallet already exists
        existing_wallet = db.query(Wallet).filter(
            Wallet.user_id == user_id
        ).first()

        if existing_wallet is not None:
            raise HTTPException(
                status_code=409,
                detail="Wallet already exists for this user"
            )

        # Create wallet
        wallet = Wallet(
            user_id=user_id,
            balance=0
        )

        db.add(wallet)
        db.commit()
        db.refresh(wallet)

        return {
            "id": wallet.id,
            "user_id": wallet.user_id,
            "balance": float(wallet.balance)
        }

    finally:
        db.close()

@app.get("/users/{user_id}/wallet")
def get_wallet(user_id: int):
    db = SessionLocal()

    try:
        wallet = db.query(Wallet).filter(
            Wallet.user_id == user_id
        ).first()

        if wallet is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        return {
            "id": wallet.id,
            "user_id": wallet.user_id,
            "balance": float(wallet.balance)
        }

    finally:
        db.close()

@app.post("/wallets/{wallet_id}/deposit")
def deposit_money(wallet_id: int, deposit: DepositRequest):
    db = SessionLocal()

    try:
        wallet = db.get(Wallet, wallet_id)

        if wallet is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        # Update wallet balance
        wallet.balance = wallet.balance + deposit.amount

        # Create transaction record
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="DEPOSIT",
            amount=deposit.amount
        )

        db.add(transaction)

        # Save both changes together
        db.commit()

        db.refresh(wallet)
        db.refresh(transaction)

        return {
            "wallet_id": wallet.id,
            "transaction_id": transaction.id,
            "transaction_type": transaction.transaction_type,
            "amount": float(transaction.amount),
            "balance": float(wallet.balance)
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

@app.post("/wallets/{wallet_id}/withdraw")
def withdraw_money(wallet_id: int, withdrawal: WithdrawRequest):
    db = SessionLocal()

    try:
        wallet = db.get(Wallet, wallet_id)

        if wallet is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        # Check sufficient balance
        if wallet.balance < withdrawal.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient wallet balance"
            )

        # Decrease wallet balance
        wallet.balance = wallet.balance - withdrawal.amount

        # Create transaction record
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="WITHDRAWAL",
            amount=withdrawal.amount
        )

        db.add(transaction)

        # Save both changes together
        db.commit()

        db.refresh(wallet)
        db.refresh(transaction)

        return {
            "wallet_id": wallet.id,
            "transaction_id": transaction.id,
            "transaction_type": transaction.transaction_type,
            "amount": float(transaction.amount),
            "balance": float(wallet.balance)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@app.get("/wallets/{wallet_id}/transactions")
def get_wallet_transactions(wallet_id: int):
    db = SessionLocal()

    try:
        # 1. Check wallet exists
        wallet = db.get(Wallet, wallet_id)

        if wallet is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        # 2. Get transactions for this wallet
        transactions = (
            db.query(WalletTransaction)
            .filter(
                WalletTransaction.wallet_id == wallet_id
            )
            .order_by(
                WalletTransaction.created_at.desc(),
                WalletTransaction.id.desc()
            )
            .all()
        )

        result = []

        for transaction in transactions:

            created_at_ist = transaction.created_at.astimezone(
                ZoneInfo("Asia/Kolkata")
            )

            item = {
                "transaction_id": transaction.id,
                "transaction_type": transaction.transaction_type,
                "amount": float(transaction.amount),
                "created_at": created_at_ist.isoformat()
            }

            if transaction.transaction_type == "DEPOSIT":
                item["direction"] = "CREDIT"
                item["description"] = "Money added to wallet"

            elif transaction.transaction_type == "WITHDRAWAL":
                item["direction"] = "DEBIT"
                item["description"] = "Money withdrawn from wallet"

            # 3. Add P2P transfer information
            elif transaction.transaction_type == "TRANSFER":

                transfer = db.get(
                    Transfer,
                    transaction.transfer_id
                )

                if transfer is not None:

                    item["transfer_id"] = transfer.id
                    item["transaction_role"] = (
                        transaction.transaction_role
                    )
                    item["status"] = transfer.status

                    # Find the other wallet
                    if transaction.wallet_id == transfer.sender_wallet_id:
                        counterparty_wallet_id = (
                            transfer.receiver_wallet_id
                        )
                    else:
                        counterparty_wallet_id = (
                            transfer.sender_wallet_id
                        )

                    # Find counterparty wallet
                    counterparty_wallet = db.get(
                        Wallet,
                        counterparty_wallet_id
                    )

                    if counterparty_wallet is not None:

                        # Find counterparty user
                        counterparty_user = db.get(
                            User,
                            counterparty_wallet.user_id
                        )

                        if counterparty_user is not None:
                            item["counterparty_user_id"] = (
                                counterparty_user.id
                            )
                            item["counterparty_name"] = (
                                counterparty_user.name
                            )

                            if transaction.transaction_role == "SENDER":
                                item["direction"] = "DEBIT"
                                item["description"] = (
                                    f"Sent to {counterparty_user.name}"
                                )
                            else:
                                item["direction"] = "CREDIT"
                                item["description"] = (
                                    f"Received from {counterparty_user.name}"
                                )

            result.append(item)

        return result

    finally:
        db.close()

@app.post("/transfers")
def create_transfer(
    transfer_request: TransferRequest,
    idempotency_key: str = Header(...)
):
    db = SessionLocal()

    try:

        # 1. Sender and receiver cannot be the same user
        if transfer_request.sender_user_id == transfer_request.receiver_user_id:
            raise HTTPException(
                status_code=400,
                detail="Sender and receiver cannot be the same user"
            )

        # 2. Find sender
        sender = db.get(User, transfer_request.sender_user_id)

        if sender is None:
            raise HTTPException(
                status_code=404,
                detail="Sender user not found"
            )

        # 3. Find receiver
        receiver = db.get(User, transfer_request.receiver_user_id)

        if receiver is None:
            raise HTTPException(
                status_code=404,
                detail="Receiver user not found"
            )

        # 4. Check whether this idempotency key was already processed
        existing_transfer = (
            db.query(Transfer)
            .filter(Transfer.idempotency_key == idempotency_key)
            .first()
        )

        if existing_transfer is not None:

            # Find wallets belonging to the original transfer
            if (
                existing_transfer.sender_wallet_id
                != db.get(Wallet, existing_transfer.sender_wallet_id).id
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid existing transfer"
                )

            original_sender_wallet = db.get(
                Wallet,
                existing_transfer.sender_wallet_id
            )

            original_receiver_wallet = db.get(
                Wallet,
                existing_transfer.receiver_wallet_id
            )

            if (
                original_sender_wallet.user_id != sender.id
                or original_receiver_wallet.user_id != receiver.id
                or existing_transfer.amount != transfer_request.amount
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Idempotency key already used with different payment details"
                )

            return {
                "transfer_id": existing_transfer.id,
                "amount": float(existing_transfer.amount),
                "status": existing_transfer.status,
                "message": "Transfer already processed"
            }

        # 5. Get both wallets in a consistent order
        wallet_user_ids = sorted([
            sender.id,
            receiver.id
        ])

        wallets = (
            db.query(Wallet)
            .filter(Wallet.user_id.in_(wallet_user_ids))
            .order_by(Wallet.user_id)
            .with_for_update()
            .all()
        )

        # 6. Make sure both wallets exist
        if len(wallets) != 2:
            raise HTTPException(
                status_code=404,
                detail="Sender or receiver wallet not found"
            )

        # 7. Identify sender and receiver wallet
        if wallets[0].user_id == sender.id:
            sender_wallet = wallets[0]
            receiver_wallet = wallets[1]
        else:
            sender_wallet = wallets[1]
            receiver_wallet = wallets[0]

        # 8. Check sender balance
        if sender_wallet.balance < transfer_request.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient wallet balance"
            )

        # 9. Deduct from sender
        sender_wallet.balance = (
            sender_wallet.balance - transfer_request.amount
        )

        # 10. Add to receiver
        receiver_wallet.balance = (
            receiver_wallet.balance + transfer_request.amount
        )

        # 11. Create transfer record
        transfer = Transfer(
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=transfer_request.amount,
            status="COMPLETED",
            idempotency_key=idempotency_key
        )

        db.add(transfer)

        # Generate transfer ID before creating ledger records
        db.flush()

        # 12. Sender ledger
        sender_transaction = WalletTransaction(
            wallet_id=sender_wallet.id,
            transfer_id=transfer.id,
            transaction_type="TRANSFER",
            transaction_role="SENDER",
            amount=transfer_request.amount
        )

        # 13. Receiver ledger
        receiver_transaction = WalletTransaction(
            wallet_id=receiver_wallet.id,
            transfer_id=transfer.id,
            transaction_type="TRANSFER",
            transaction_role="RECEIVER",
            amount=transfer_request.amount
        )

        db.add(sender_transaction)
        db.add(receiver_transaction)

        # 14. Commit everything atomically
        db.commit()

        db.refresh(transfer)
        db.refresh(sender_wallet)
        db.refresh(receiver_wallet)

        return {
            "transfer_id": transfer.id,
            "sender_user_id": sender.id,
            "receiver_user_id": receiver.id,
            "amount": float(transfer.amount),
            "status": transfer.status,
            "sender_balance": float(sender_wallet.balance),
            "receiver_balance": float(receiver_wallet.balance)
        }

    except IntegrityError:

        # Another concurrent request may have created
        # this idempotency key first.
        db.rollback()

        existing_transfer = (
            db.query(Transfer)
            .filter(Transfer.idempotency_key == idempotency_key)
            .first()
        )

        if existing_transfer is not None:
            return {
                "transfer_id": existing_transfer.id,
                "amount": float(existing_transfer.amount),
                "status": existing_transfer.status,
                "message": "Transfer already processed"
            }

        raise

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

@app.post("/auth/request-otp")
def request_otp(request: OTPRequest):
    db = SessionLocal()

    try:
        otp = generate_otp()
        otp_hash = hash_otp(otp)

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)

        otp_record = OTPVerification(
            identifier=request.identifier,
            channel=request.channel,
            purpose=request.purpose,
            otp_hash=otp_hash,
            expires_at=expires_at
        )

        db.add(otp_record)
        db.commit()
        db.refresh(otp_record)

        return {
            "message": "OTP generated successfully",
            "otp": otp,
            "expires_at": expires_at.isoformat()
        }

    finally:
        db.close()

@app.post("/auth/verify-otp")
def verify_otp_endpoint(request: OTPVerifyRequest):
    db = SessionLocal()

    try:
        otp_record = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.identifier == request.identifier,
                OTPVerification.channel == request.channel,
                OTPVerification.purpose == request.purpose,
                OTPVerification.used_at.is_(None)
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not otp_record:
            return {
                "message": "Invalid or expired OTP"
            }

        now = datetime.now(timezone.utc)

        if otp_record.expires_at <= now:
            return {
                "message": "OTP has expired"
            }

        if otp_record.attempts >= 5:
            return {
                "message": "Too many invalid attempts"
            }

        is_valid = verify_otp(
            request.otp,
            otp_record.otp_hash
        )

        if not is_valid:
            otp_record.attempts += 1
            db.commit()

            return {
                "message": "Invalid OTP",
                "attempts_remaining": 5 - otp_record.attempts
            }

        otp_record.used_at = now

        if request.purpose == "PHONE_VERIFICATION":
            user = (
                db.query(User)
                .filter(User.phone == request.identifier)
                .first()
            )

            if user:
                user.phone_verified = True

        elif request.purpose == "EMAIL_VERIFICATION":
            user = (
                db.query(User)
                .filter(User.email == request.identifier)
                .first()
        )

        if user:
            user.email_verified = True


        if user:
            user.phone_verified = True

        db.commit()

        return {
            "message": "OTP verified successfully"
        }

    finally:
        db.close()


@app.post("/auth/register/start")
def start_registration(request: RegistrationStartRequest):
    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.phone == request.phone)
            .first()
        )

        if existing_user:
            return {
                "message": "Phone number is already registered"
            }

        now = datetime.now(timezone.utc)

        registration = (
            db.query(RegistrationChallenge)
            .filter(
                RegistrationChallenge.phone == request.phone,
                RegistrationChallenge.status == "IN_PROGRESS"
            )
            .order_by(RegistrationChallenge.created_at.desc())
            .first()
        )

        if registration and registration.expires_at <= now:
            registration.status = "EXPIRED"
            registration = None

        if not registration:
            registration = RegistrationChallenge(
                registration_token=generate_registration_token(),
                phone=request.phone,
                expires_at=now + timedelta(minutes=15)
            )

            db.add(registration)
            db.flush()

        otp = generate_otp()
        otp_hash = hash_otp(otp)

        otp_record = OTPVerification(
            identifier=request.phone,
            channel="PHONE",
            purpose="PHONE_REGISTRATION",
            otp_hash=otp_hash,
            expires_at=now + timedelta(minutes=5)
        )

        db.add(otp_record)
        db.commit()
        db.refresh(registration)

        return {
            "message": "Registration started",
            "registration_token": registration.registration_token,
            "otp": otp,
            "expires_at": registration.expires_at.isoformat()
        }

    finally:
        db.close()


@app.post("/auth/register/verify-phone")
def verify_registration_phone(
    request: RegistrationPhoneVerifyRequest
): 

    db = SessionLocal()

    try:
        registration = (
            db.query(RegistrationChallenge)
            .filter(
                RegistrationChallenge.registration_token == request.registration_token
            )
            .first()
        )

        if not registration:
            return {
                "message": "Registration not found"
            }

        now = datetime.now(timezone.utc)

        if registration.status != "IN_PROGRESS":
            return {
                "message": "Registration is no longer active"
            }

        if registration.expires_at <= now:
            registration.status = "EXPIRED"
            db.commit()

            return {
                "message": "Registration has expired"
            }

        if registration.phone_verified:
            return {
                "message": "Phone number is already verified"
            }

        otp_record = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.identifier == registration.phone,
                OTPVerification.channel == "PHONE",
                OTPVerification.purpose == "PHONE_REGISTRATION",
                OTPVerification.used_at.is_(None)
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not otp_record:
            return {
                "message": "OTP not found"
            }

        if otp_record.expires_at <= now:
            return {
                "message": "OTP has expired"
            }

        if otp_record.attempts >= 5:
            return {
                "message": "Too many invalid attempts"
            }

        is_valid = verify_otp(
            request.otp,
            otp_record.otp_hash
        )

        if not is_valid:
            otp_record.attempts += 1
            db.commit()

            return {
                "message": "Invalid OTP",
                "attempts_remaining": 5 - otp_record.attempts
            }

        otp_record.used_at = now
        registration.phone_verified = True

        db.commit()

        return {
            "message": "Phone number verified successfully",
            "registration_id": registration.id
        }

    finally:
        db.close()


@app.post("/auth/register/details")
def register_details(request: RegistrationDetailsRequest):
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        registration = (
            db.query(RegistrationChallenge)
            .filter(
                RegistrationChallenge.registration_token
                == request.registration_token
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration session not found"
            )

        if registration.status != "IN_PROGRESS":
            raise HTTPException(
                status_code=400,
                detail="Registration session is no longer active"
            )

        if registration.expires_at <= now:
            registration.status = "EXPIRED"
            db.commit()

            raise HTTPException(
                status_code=400,
                detail="Registration session has expired"
            )

        if not registration.phone_verified:
            raise HTTPException(
                status_code=400,
                detail="Phone number must be verified first"
            )

        existing_user = (
            db.query(User)
            .filter(User.email == request.email)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email address is already registered"
            )

        registration.name = request.name
        registration.email = request.email

        otp = generate_otp()
        otp_hash = hash_otp(otp)

        otp_record = OTPVerification(
            identifier=request.email,
            channel="EMAIL",
            purpose="EMAIL_REGISTRATION",
            otp_hash=otp_hash,
            expires_at=now + timedelta(minutes=5)
        )

        db.add(otp_record)
        db.commit()

        return {
            "message": "Registration details saved. Email OTP generated.",
            "otp": otp,
            "expires_at": otp_record.expires_at.isoformat()
        }

    finally:
        db.close()

@app.post("/auth/register/verify-email")
def verify_registration_email(
    request: RegistrationEmailVerifyRequest
):
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        registration = (
            db.query(RegistrationChallenge)
            .filter(
                RegistrationChallenge.registration_token
                == request.registration_token
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration session not found"
            )

        if registration.status != "IN_PROGRESS":
            raise HTTPException(
                status_code=400,
                detail="Registration session is no longer active"
            )

        if registration.expires_at <= now:
            registration.status = "EXPIRED"
            db.commit()

            raise HTTPException(
                status_code=400,
                detail="Registration session has expired"
            )

        if not registration.phone_verified:
            raise HTTPException(
                status_code=400,
                detail="Phone number must be verified first"
            )

        if not registration.email:
            raise HTTPException(
                status_code=400,
                detail="Email address has not been provided"
            )

        if registration.email_verified:
            raise HTTPException(
                status_code=400,
                detail="Email address is already verified"
            )

        otp_record = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.identifier == registration.email,
                OTPVerification.channel == "EMAIL",
                OTPVerification.purpose == "EMAIL_REGISTRATION",
                OTPVerification.used_at.is_(None),
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not otp_record:
            raise HTTPException(
                status_code=400,
                detail="No active email OTP found"
            )

        if otp_record.expires_at <= now:
            raise HTTPException(
                status_code=400,
                detail="Email OTP has expired"
            )

        if otp_record.attempts >= 5:
            raise HTTPException(
                status_code=400,
                detail="Maximum OTP attempts exceeded"
            )

        if not verify_otp(request.otp, otp_record.otp_hash):
            otp_record.attempts += 1
            db.commit()

            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )

        existing_user = (
            db.query(User)
            .filter(
                (User.email == registration.email)
                | (User.phone == registration.phone)
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="User already exists with this email or phone"
            )

        otp_record.used_at = now
        registration.email_verified = True

        user = User(
            name=registration.name,
            email=registration.email,
            email_verified=True,
            phone=registration.phone,
            phone_verified=True,
        )

        db.add(user)

        registration.status = "COMPLETED"

        db.commit()
        db.refresh(user)

        return {
            "message": "Registration completed successfully",
            "user_id": user.id,
        }

    finally:
        db.close()