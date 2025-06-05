import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
STRIPE_CLIENT_ID = os.getenv("STRIPE_CLIENT_ID")

# Simple file-based user storage (in production, use a proper database)
USERS_FILE = "app/data/users.json"

security = HTTPBearer()

class AuthManager:
    def __init__(self):
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Any]:
        """Load users from JSON file"""
        try:
            os.makedirs("app/data", exist_ok=True)
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_users(self):
        """Save users to JSON file"""
        os.makedirs("app/data", exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump(self.users, f, indent=2)
    
    def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user"""
        if email in self.users:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            "email": email,
            "name": name,
            "password_hash": password_hash.decode('utf-8'),
            "created_at": datetime.now().isoformat(),
            "oauth_tokens": {},
            "settings": {
                "scenes": {"stripe": 2, "calendar": 3, "youtube": 1},
                "selected_device": {
                    "device_id": os.getenv("GOVEE_DEVICE_ID", ""),
                    "model": os.getenv("GOVEE_MODEL", ""),
                    "name": "Smart Curtain Lights 1"
                }
            }
        }
        
        self.users[email] = user_data
        self._save_users()
        
        return {"email": email, "name": name, "created_at": user_data["created_at"]}
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = self.users.get(email)
        if not user:
            return None
        
        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            return {
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
        return None
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user = self.users.get(email)
        if user:
            return {
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"],
                "oauth_tokens": user.get("oauth_tokens", {}),
                "settings": user.get("settings", {})
            }
        return None
    
    def update_oauth_tokens(self, email: str, service: str, tokens: Dict[str, Any]):
        """Update OAuth tokens for a user"""
        if email in self.users:
            if "oauth_tokens" not in self.users[email]:
                self.users[email]["oauth_tokens"] = {}
            self.users[email]["oauth_tokens"][service] = tokens
            self._save_users()
    
    def get_oauth_tokens(self, email: str, service: str) -> Optional[Dict[str, Any]]:
        """Get OAuth tokens for a user and service"""
        user = self.users.get(email)
        if user and "oauth_tokens" in user:
            return user["oauth_tokens"].get(service)
        return None
    
    def update_user_settings(self, email: str, settings: Dict[str, Any]):
        """Update user settings"""
        if email in self.users:
            self.users[email]["settings"] = settings
            self._save_users()
    
    def get_user_settings(self, email: str) -> Dict[str, Any]:
        """Get user settings"""
        user = self.users.get(email)
        if user:
            return user.get("settings", {})
        return {}

# Global auth manager instance
auth_manager = AuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    email = payload.get("sub")
    
    user = auth_manager.get_user(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_oauth_redirect_uri(service: str) -> str:
    """Get OAuth redirect URI for a service"""
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    return f"{base_url}/oauth/{service}/callback"

def get_google_oauth_url(state: str) -> str:
    """Generate Google OAuth URL"""
    client_id = GOOGLE_CLIENT_ID
    redirect_uri = get_oauth_redirect_uri("google")
    scope = "openid email profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/youtube.readonly"
    
    return (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"response_type=code&"
        f"state={state}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

def get_stripe_oauth_url(state: str) -> str:
    """Generate Stripe Connect OAuth URL"""
    client_id = STRIPE_CLIENT_ID
    redirect_uri = get_oauth_redirect_uri("stripe")
    
    return (
        f"https://connect.stripe.com/oauth/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"state={state}&"
        f"scope=read_write"
    ) 