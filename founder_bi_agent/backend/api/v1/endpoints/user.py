from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from founder_bi_agent.backend.core.auth import verify_password, get_password_hash, create_access_token, decode_access_token
from founder_bi_agent.backend.db.postgres_db import PostgresManager
from founder_bi_agent.backend.core.config import AgentSettings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")

class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None

def get_db():
    settings = AgentSettings.from_env()
    return PostgresManager(settings)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload["sub"]
    db = get_db()
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
            from founder_bi_agent.backend.db.postgres_db import MockConnection
            if isinstance(conn, MockConnection):
                return {"id": 1, "username": username, "email": "mock@example.com"}
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return {"id": user[0], "username": user[1], "email": user[2]}
    finally:
        db.release_connection(conn)

@router.post("/register", response_model=UserResponse)
def register(user: UserRegister):
    db = get_db()
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            from founder_bi_agent.backend.db.postgres_db import MockConnection
            if not isinstance(conn, MockConnection):
                # Check if user exists
                cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Username already registered")
            
            hashed_pw = get_password_hash(user.password)
            cur.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s) RETURNING id, username, email",
                (user.username, hashed_pw, user.email)
            )
            from founder_bi_agent.backend.db.postgres_db import MockConnection
            if isinstance(conn, MockConnection):
                return {"id": 1, "username": user.username, "email": user.email}
            new_user = cur.fetchone()
            conn.commit()
            return {"id": new_user[0], "username": new_user[1], "email": new_user[2]}
    finally:
        db.release_connection(conn)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    conn = db.get_connection()
    try:
        from founder_bi_agent.backend.db.postgres_db import MockConnection
        is_mock = isinstance(conn, MockConnection)
        
        # In mock mode, allow 'test' user with any password for easy verification
        if is_mock and form_data.username == "test":
            access_token = create_access_token(data={"sub": "test", "user_id": 1})
            return {"access_token": access_token, "token_type": "bearer"}

        with conn.cursor() as cur:
            cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (form_data.username,))
            user = cur.fetchone()
            
            if is_mock:
                # If username exists in mock memory, allow it
                if user:
                    access_token = create_access_token(data={"sub": form_data.username, "user_id": 1})
                    return {"access_token": access_token, "token_type": "bearer"}
                else:
                    raise HTTPException(status_code=401, detail="User not found in mock store")

            if not user or not verify_password(form_data.password, user[2]):
                raise HTTPException(status_code=401, detail="Incorrect username or password")
            
            access_token = create_access_token(data={"sub": user[1], "user_id": user[0]})
            return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.release_connection(conn)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
