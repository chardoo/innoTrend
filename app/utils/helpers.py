from cmath import e
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt 
from passlib.context import CryptContext
from app.config.settings import settings
import random
import string
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    print("Verifying password")
    print(hashed_password)
    print(plain_password)
    me = plain_password.encode("utf-8")
    print(me)
    return bcrypt.checkpw(me, hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hash a password"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8') 

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("Decoded payload:", payload)
        return payload
    except Exception as e:
        print("Error decoding token:", e)
        return None

def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"ORD-{timestamp}-{random_str}"

def format_phone_number(phone: str) -> str:
    """Format phone number for SMS"""
    phone = ''.join(filter(str.isdigit, phone))
    if not phone.startswith('+'):
        if len(phone) == 10:
            phone = f"+1{phone}"
        elif len(phone) == 11 and phone.startswith('1'):
            phone = f"+{phone}"
    return phone
