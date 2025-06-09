from datetime import datetime, timedelta
from typing import Any, Dict
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User, Lawyer
from app.schemas.user import UserCreate, UserInDB, Token, TokenData, LawyerCreate

router = APIRouter(
    prefix="/auth",  # 명시적으로 /auth 경로 설정
    tags=["auth"]
)

# 비밀번호 암호화
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    return None

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/token", response_model=Token, summary="로그인 전용 토큰 발급")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token, summary="일반 사용자 회원가입")
async def register_user(
    user_in: UserCreate, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        print("\n\n회원가입 요청 데이터:", user_in.dict())
        
        # 이메일 중복 확인
        db_user = db.query(User).filter(User.email == user_in.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        print("비밀번호 해시 작업")
        hashed_password = get_password_hash(user_in.password)
        
        # 사용자 생성 - 데이터베이스 필드에 맞게 매핑
        db_user = User(
            email=user_in.email,
            name=user_in.full_name,  # full_name을 name 필드에 매핑
            password=hashed_password,
            is_lawyer=False
        )
        
        # 데이터베이스에 필드가 없는 추가 데이터(nickname, phone, address 등)는 저장하지 않음
        # 필요한 경우 별도의 테이블에 저장하거나 테이블 구조를 변경해야 함
        
        print("사용자 데이터:", {
            "email": user_in.email,
            "name": user_in.full_name,
            "is_lawyer": False
        })
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print("사용자 생성 완료, ID:", db_user.user_id)
        
        # 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email}, expires_delta=access_token_expires
        )
        
        print("토큰 생성 완료")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        db.rollback()  # 오류 발생 시 트랜잭션 롤백
        print("회원가입 처리 중 오류:", str(e))
        print(traceback.format_exc())
        raise

@router.get("/test", summary="API 테스트")
def test_auth_endpoint():
    return {"message": "Auth API is working correctly"}

@router.post("/register/lawyer", response_model=Token, summary="변호사 회원가입")
async def register_lawyer(
    lawyer_in: LawyerCreate, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        print("\n\n변호사 회원가입 요청 데이터:", lawyer_in.dict())
        
        # 이메일 중복 확인
        db_user = db.query(User).filter(User.email == lawyer_in.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # 변호사 자격번호 중복 확인
        db_lawyer = db.query(Lawyer).filter(Lawyer.registration_number == lawyer_in.license_number).first()
        if db_lawyer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered",
            )
        
        print("비밀번호 해시 작업")
        hashed_password = get_password_hash(lawyer_in.password)
        
        # 사용자 생성
        db_user = User(
            email=lawyer_in.email,
            name=lawyer_in.full_name,
            password=hashed_password,
            is_lawyer=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print("변호사 사용자 생성 완료, ID:", db_user.user_id)
        
        # 변호사 정보 생성
        db_lawyer = Lawyer(
            user_id=db_user.user_id,
            registration_number=lawyer_in.license_number,
            expertise=','.join(lawyer_in.specialization) if lawyer_in.specialization else '',
            region=lawyer_in.address,
            verified=False
        )
        db.add(db_lawyer)
        db.commit()
        db.refresh(db_lawyer)
        
        print("변호사 정보 생성 완료")
        
        # 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email}, expires_delta=access_token_expires
        )
        
        print("토큰 생성 완료")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        db.rollback()  # 오류 발생 시 트랜잭션 롤백
        print("변호사 회원가입 처리 중 오류:", str(e))
        print(traceback.format_exc())
        raise
