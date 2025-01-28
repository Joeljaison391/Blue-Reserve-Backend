from fastapi import FastAPI, HTTPException, Depends, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from utils.database import get_db_connection
from utils.jwt_handler import decode_access_token
from passlib.context import CryptContext
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Management Service")
security = HTTPBearer()

# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to authenticate users via JWT
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Extract JWT token from Authorization header and decode it."""
    token = credentials.credentials
    logger.debug(f"Received Token: {token}")

    user_data = decode_access_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

    logger.debug(f"Decoded User Data: {user_data}")
    return user_data

class UpdateUserDetails(BaseModel):
    username: str = None
    email: str = None
    password: str = None

@app.get("/users/{user_id}")
def get_user_details(user_id: int, current_user: dict = Depends(get_current_user)):
    """Retrieve user details by ID."""
    logger.debug(f"Fetching details for user ID: {user_id}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, username, email, bluDollar_balance, 'EMPLOYEE' AS role FROM employees WHERE id = %s
            UNION ALL
            SELECT id, username, email, bluDollar_balance, 'MANAGER' AS role FROM managers WHERE id = %s
        """, (user_id, user_id))

        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    finally:
        cur.close()
        conn.close()

    return {"id": user[0], "username": user[1], "email": user[2], "bluDollar_balance": user[3], "role": user[4]}

@app.put("/users/{user_id}")
def update_user_details(user_id: int, details: UpdateUserDetails, current_user: dict = Depends(get_current_user)):
    """Update user details (username, email, or password)."""
    logger.debug(f"Updating user {user_id} with details: {details}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Determine if the user exists and fetch role
        cur.execute("""
            SELECT 'EMPLOYEE' AS role FROM employees WHERE id = %s
            UNION ALL
            SELECT 'MANAGER' AS role FROM managers WHERE id = %s
        """, (user_id, user_id))

        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        role = result[0]

        # Build the update query dynamically
        fields = []
        values = []
        if details.username:
            fields.append("username = %s")
            values.append(details.username)
        if details.email:
            fields.append("email = %s")
            values.append(details.email)
        if details.password:
            hashed_password = pwd_context.hash(details.password)  # Hash the password before updating
            fields.append("password = %s")
            values.append(hashed_password)

        if fields:
            query = f"UPDATE {role.lower()}s SET {', '.join(fields)} WHERE id = %s"
            values.append(user_id)
            cur.execute(query, values)
            conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"message": "User details updated successfully"}

@app.get("/users/{user_id}/role")
def get_user_role(user_id: int, current_user: dict = Depends(get_current_user)):
    """Retrieve the role of a user."""
    logger.debug(f"Fetching role for user ID: {user_id}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 'EMPLOYEE' AS role FROM employees WHERE id = %s
            UNION ALL
            SELECT 'MANAGER' AS role FROM managers WHERE id = %s
        """, (user_id, user_id))

        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
    finally:
        cur.close()
        conn.close()

    return {"user_id": user_id, "role": result[0]}

@app.get("/users")
def get_users_by_role(role: str = Query(None, regex="^(EMPLOYEE|MANAGER)$"),
                      current_user: dict = Depends(get_current_user)):
    """Retrieve all users filtered by role."""
    logger.debug(f"Fetching all users with role: {role}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if role == "EMPLOYEE":
            cur.execute("SELECT id, username, email, bluDollar_balance FROM employees")
        elif role == "MANAGER":
            cur.execute("SELECT id, username, email, bluDollar_balance FROM managers")
        else:
            raise HTTPException(status_code=400, detail="Invalid role")

        users = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return [{"id": user[0], "username": user[1], "email": user[2], "bluDollar_balance": user[3]} for user in users]

@app.get("/users/search")
def search_users(username: str = None, email: str = None, current_user: dict = Depends(get_current_user)):
    """Search users by username or email."""
    logger.debug(f"Searching users with username: {username}, email: {email}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if username:
            cur.execute("""
                SELECT id, username, email, bluDollar_balance, 'EMPLOYEE' AS role FROM employees WHERE username ILIKE %s
                UNION ALL
                SELECT id, username, email, bluDollar_balance, 'MANAGER' AS role FROM managers WHERE username ILIKE %s
            """, (f"%{username}%", f"%{username}%"))
        elif email:
            cur.execute("""
                SELECT id, username, email, bluDollar_balance, 'EMPLOYEE' AS role FROM employees WHERE email ILIKE %s
                UNION ALL
                SELECT id, username, email, bluDollar_balance, 'MANAGER' AS role FROM managers WHERE email ILIKE %s
            """, (f"%{email}%", f"%{email}%"))
        else:
            raise HTTPException(status_code=400, detail="Query parameter 'username' or 'email' is required")

        users = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return [{"id": user[0], "username": user[1], "email": user[2], "bluDollar_balance": user[3], "role": user[4]} for user in users]
