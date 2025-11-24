from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request
from sqlalchemy.orm import Session
from ...database import get_db
from ... import models, schemas
from ...auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
)
import secrets
from datetime import datetime, timedelta


router = APIRouter(prefix="/auth", tags=["auth"])

# inside file, replace register(...) with:
@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(models.User).filter(models.User.email == user_in.email).first()
        if existing:
            # validation error - return 400
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = get_password_hash(user_in.password)
        user = models.User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed,
            role=(user_in.role or "teacher"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        # common case: unique constraint on email
        raise HTTPException(status_code=400, detail="Database integrity error (likely duplicate email).")
    except SQLAlchemyError:
        db.rollback()
        # generic DB error
        raise HTTPException(status_code=500, detail="Database error while creating user.")
    except HTTPException:
        # re-raise HTTP errors we raised above without wrapping them
        raise
    except Exception as e:
        # defensive catch-all (should not mask bugs long-term)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
@router.post("/token")
async def login_for_access_token(request: Request, db: Session = Depends(get_db)):
    """Accept either form-encoded OAuth2 requests or JSON bodies.
    We try form parsing first (works for the OAuth2 form flow), then fall back to JSON.
    """
    username = None
    password = None
    # Try form data first (handles application/x-www-form-urlencoded)
    try:
        form = await request.form()
        username = form.get("username") or form.get("email")
        password = form.get("password")
    except Exception:
        # ignore form parsing errors and try JSON next
        pass
    # If not present in form, try JSON body
    if not username or not password:
        try:
            body = await request.json()
            if isinstance(body, dict):
                username = username or body.get("username") or body.get("email")
                password = password or body.get("password")
        except Exception:
            # leave username/password as-is
            pass
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot")
def forgot_password(req: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    # Do not reveal whether email exists to prevent enumeration attacks
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        return {"message": "If the email exists, a reset token was sent."}

    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    pr = models.PasswordReset(token=token, user_id=user.id, expires_at=expires, used=False)
    db.add(pr)
    db.commit()
    db.refresh(pr)

    # TODO: send the token to the user's email using an SMTP service
    # For development/testing we return the token in the response so you can test the reset flow.
    return {"message": "Password reset token generated.", "reset_token": token, "expires_at": expires.isoformat()}


@router.post("/reset")
def reset_password(req: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    pr = db.query(models.PasswordReset).filter(models.PasswordReset.token == req.token).first()
    if not pr or pr.used or pr.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).get(pr.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.hashed_password = get_password_hash(req.new_password)
    pr.used = True
    db.add(user)
    db.add(pr)
    db.commit()

    return {"message": "Password has been reset successfully."}
