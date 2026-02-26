from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.security import create_jwt, decode_jwt, generate_api_key, hash_password, verify_password
from src.db.session import get_db
from src.models import ExternalID, User
from src.schemas import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    RenewResponse,
    SocialAuthRequest,
    SocialAuthResponse,
)

router = APIRouter()

DEFAULT_PHOTO = "https://juca.eu.org/img/icon_dafault.jpg"
VALID_DEVICES = {10, 20}
API_KEY_MAX_ATTEMPTS = 10
DEFAULT_SOCIAL_ORIGIN = 90
SOCIAL_PHONE_MAX_ATTEMPTS = 10


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


def build_unique_social_phone(db: Session) -> str:
    for _ in range(SOCIAL_PHONE_MAX_ATTEMPTS):
        candidate = f"00000000000-{secrets.token_hex(6)}"
        exists = db.query(User.id).filter(User.phone == candidate).first()
        if not exists:
            return candidate
    raise HTTPException(status_code=500, detail="failed to generate unique social phone")


def get_user_from_api_key(db: Session, api_key: str | None) -> User:
    if not api_key:
        raise HTTPException(status_code=401, detail="missing api key")

    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=403, detail="invalid api key")

    return user

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

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="invalid credentials")

    jwt_payload = {
        "photo": user.photo,
        "phone": user.phone,
        "email": user.email,
        "name": user.name,
        "status": user.status,
        "public_id": user.public_id,
        "profile": user.profile,
    }
    token = create_jwt(jwt_payload, settings.secret_key, settings.jwt_expires_days)

    return LoginResponse(token=token, key=user.api_key)

@router.post("/social", response_model=SocialAuthResponse, status_code=status.HTTP_200_OK)
def social_auth(payload: SocialAuthRequest, db: Session = Depends(get_db)) -> SocialAuthResponse:
    if payload.device not in VALID_DEVICES:
        raise HTTPException(status_code=400, detail="device must be 10 (mobile) or 20 (desktop)")

    provider = payload.provider.strip().lower()
    auth_type = payload.type.strip().lower()
    email = payload.email.lower()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            photo=payload.photo_url or DEFAULT_PHOTO,
            phone=build_unique_social_phone(db),
            email=email,
            name=payload.name,
            password=hash_password(secrets.token_urlsafe(24)),
            status=1,
            origin=DEFAULT_SOCIAL_ORIGIN,
            is_deleted=False,
            is_verified=True,
            profile=1,
            public_id="pending",
            device=payload.device,
            api_key=build_unique_api_key(db),
        )
        db.add(user)
        db.flush()

        user.public_id = build_public_id(payload.device, user.id)

    external = (
        db.query(ExternalID)
        .filter(ExternalID.provider == provider, ExternalID.provider_id == payload.provider_id)
        .first()
    )
    if external and external.user_id != user.id:
        raise HTTPException(status_code=409, detail="external_id already linked to another user")

    if not external:
        external_by_user = (
            db.query(ExternalID)
            .filter(ExternalID.user_id == user.id, ExternalID.provider == provider)
            .first()
        )
        if external_by_user:
            external_by_user.provider_id = payload.provider_id
            external_by_user.type = auth_type
            external_by_user.device = payload.device
        else:
            external = ExternalID(
                user_id=user.id,
                provider=provider,
                type=auth_type,
                provider_id=payload.provider_id,
                device=payload.device,
            )
            db.add(external)

    db.commit()
    db.refresh(user)

    jwt_payload = {
        "photo": user.photo,
        "phone": user.phone,
        "email": user.email,
        "name": user.name,
        "status": user.status,
        "public_id": user.public_id,
        "profile": user.profile,
    }
    token = create_jwt(jwt_payload, settings.secret_key, settings.jwt_expires_days)

    return SocialAuthResponse(token=token, key=user.api_key)

@router.post("/renew", response_model=RenewResponse, status_code=status.HTTP_200_OK)
def renew_token(
    db: Session = Depends(get_db),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> RenewResponse:
    user = get_user_from_api_key(db, api_key)

    jwt_payload = {
        "photo": user.photo,
        "phone": user.phone,
        "email": user.email,
        "name": user.name,
        "status": user.status,
        "public_id": user.public_id,
        "profile": user.profile,
    }
    new_token = create_jwt(jwt_payload, settings.secret_key, settings.jwt_expires_days)

    return RenewResponse(token=new_token)


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
def me(
    db: Session = Depends(get_db),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> MeResponse:
    user = get_user_from_api_key(db, api_key)

    return MeResponse(
        photo=user.photo,
        phone=user.phone,
        email=user.email,
        name=user.name,
        status=user.status,
        public_id=user.public_id,
        profile=user.profile,
    )
