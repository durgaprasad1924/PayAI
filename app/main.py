from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import User, Wallet, WalletTransaction, Transfer

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
        wallet = db.get(Wallet, wallet_id)

        if wallet is None:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        transactions = (
            db.query(WalletTransaction)
            .filter(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.id)
            .all()
        )

        return [
            {
                "id": transaction.id,
                "wallet_id": transaction.wallet_id,
                "transaction_type": transaction.transaction_type,
                "amount": float(transaction.amount)
            }
            for transaction in transactions
        ]

    finally:
        db.close()


@app.post("/transfers")
def create_transfer(transfer_request: TransferRequest):
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

        # 4. Get both wallets in a consistent order
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

        # 5. Make sure both wallets exist
        if len(wallets) != 2:
            raise HTTPException(
                status_code=404,
                detail="Sender or receiver wallet not found"
            )
        # 6. Identify sender and receiver wallet
        if wallets[0].user_id == sender.id:
            sender_wallet = wallets[0]
            receiver_wallet = wallets[1]
        else:
            sender_wallet = wallets[1]
            receiver_wallet = wallets[0]

        # 7. Check sender balance
        if sender_wallet.balance < transfer_request.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient wallet balance"
            )

        # 8. Deduct from sender
        sender_wallet.balance = (
            sender_wallet.balance - transfer_request.amount
        )

        # 9. Add to receiver
        receiver_wallet.balance = (
            receiver_wallet.balance + transfer_request.amount
        )

        # 10. Create transfer record
        transfer = Transfer(
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=transfer_request.amount,
            status="COMPLETED"
        )

        db.add(transfer)

        # Generate transfer ID before creating ledger records
        db.flush()

        # 11. Sender ledger
        sender_transaction = WalletTransaction(
            wallet_id=sender_wallet.id,
            transfer_id=transfer.id,
            transaction_type="TRANSFER",
            transaction_role="SENDER",
            amount=transfer_request.amount
        )

        # 12. Receiver ledger
        receiver_transaction = WalletTransaction(
            wallet_id=receiver_wallet.id,
            transfer_id=transfer.id,
            transaction_type="TRANSFER",
            transaction_role="RECEIVER",
            amount=transfer_request.amount
        )

        db.add(sender_transaction)
        db.add(receiver_transaction)

        # 13. Commit everything atomically
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

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()