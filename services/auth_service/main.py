from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from utils.database import get_db_connection
from utils.jwt_handler import create_access_token

app = FastAPI(title="Auth Service")

# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    role: str  # EMPLOYEE or MANAGER

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/register")
def register_user(user: UserRegister):
    """Register a new user (Employee or Manager)."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Hash the password
    hashed_password = pwd_context.hash(user.password)

    # Insert user into the correct table
    if user.role.upper() == "EMPLOYEE":
        table = "employees"
    elif user.role.upper() == "MANAGER":
        table = "managers"
    else:
        raise HTTPException(status_code=400, detail="Invalid role")

    try:
        cur.execute(
            f"INSERT INTO {table} (username, email, password) VALUES (%s, %s, %s) RETURNING id",
            (user.username, user.email, hashed_password)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="User registration failed: " + str(e))
    finally:
        cur.close()
        conn.close()

    return {"id": user_id, "message": f"{user.role.capitalize()} registered successfully"}

@app.post("/login")
def login_user(user: UserLogin):
    """Authenticate a user and return a JWT token."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if user exists in both tables
    try:
        cur.execute(
            "SELECT id, password FROM employees WHERE email = %s UNION ALL "
            "SELECT id, password FROM managers WHERE email = %s",
            (user.email, user.email)
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        user_id, hashed_password = result

        # Verify the password
        if not pwd_context.verify(user.password, hashed_password):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Generate a JWT token
        access_token = create_access_token(data={"sub": user.email, "id": user_id})
    finally:
        cur.close()
        conn.close()

    return {"access_token": access_token, "token_type": "bearer"}
