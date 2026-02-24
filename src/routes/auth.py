from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import generate_api_key, hash_password
from src.db.session import get_db
from src.models import User
from src.schemas import RegisterRequest, RegisterResponse

router = APIRouter()

DEFAULT_PHOTO = "https://juca.eu.org/img/icon_dafault.jpg"
VALID_DEVICES = {10, 20}
API_KEY_MAX_ATTEMPTS = 10


def build_public_id(device: int, user_id: int) -> str:
    date_part = datetime.utcnow().strftime("%d%m%y")
    return f"{device}{date_part}{user_id}"


def build_unique_api_key(db: Session) -> str:
    for _ in range(API_KEY_MAX_ATTEMPTS):
        candidate = generate_api_key()
        exists = db.query(User.id).filter(User.api_key == candidate).first()
        if not exists:
            return candidate
    raise HTTPException(status_code=500, detail="failed to generate unique api_key")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    if payload.device not in VALID_DEVICES:
        raise HTTPException(status_code=400, detail="device must be 10 (mobile) or 20 (desktop)")

    existing_email = db.query(User.id).filter(User.email == payload.email.lower()).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="email already registered")

    existing_phone = db.query(User.id).filter(User.phone == payload.phone).first()
    if existing_phone:
        raise HTTPException(status_code=409, detail="phone already registered")

    user = User(
        photo=DEFAULT_PHOTO,
        phone=payload.phone,
        email=payload.email.lower(),
        name=payload.name,
        password=hash_password(payload.password),
        status=1,
        origin=payload.origin,
        is_deleted=False,
        is_verified=False,
        profile=1,
        public_id="pending",
        device=payload.device,
        api_key=build_unique_api_key(db),
    )

    db.add(user)
    db.flush()

    user.public_id = build_public_id(payload.device, user.id)

    db.commit()
    db.refresh(user)

    return RegisterResponse(
        public_id=user.public_id,
        message="User created successfully.",
    )
