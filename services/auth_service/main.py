from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from utils.database import get_db_connection
from utils.jwt_handler import create_access_token
import logging

app = FastAPI(title="Auth Service")

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    role: str  # EMPLOYEE or MANAGER
    manager_id: int = None  # Only required if role is EMPLOYEE

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
    logger.debug(f"Hashed password for {user.email}: {hashed_password}")

    try:
        if user.role.upper() == "EMPLOYEE":
            if user.manager_id is None:
                raise HTTPException(status_code=400, detail="Manager ID is required for employees")

            # Check if manager exists
            cur.execute("SELECT id FROM managers WHERE id = %s", (user.manager_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Manager not found")

            cur.execute(
                "INSERT INTO employees (username, email, password, manager_id) VALUES (%s, %s, %s, %s) RETURNING id",
                (user.username, user.email, hashed_password, user.manager_id)
            )

        elif user.role.upper() == "MANAGER":
            cur.execute(
                "INSERT INTO managers (username, email, password, bluDollar_balance) VALUES (%s, %s, %s, %s) RETURNING id",
                (user.username, user.email, hashed_password, 200)  # Managers start with 200 BluDollars
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid role")

        user_id = cur.fetchone()[0]
        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Database error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        cur.close()
        conn.close()

    return {"id": user_id, "message": f"{user.role.capitalize()} registered successfully"}

@app.post("/login")
def login_user(user: UserLogin):
    """Authenticate a user and return a JWT token."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch hashed password and user details from the database
        cur.execute(
            "SELECT id, password, 'EMPLOYEE' AS role, manager_id FROM employees WHERE email = %s UNION ALL "
            "SELECT id, password, 'MANAGER' AS role, NULL FROM managers WHERE email = %s",
            (user.email, user.email)
        )
        result = cur.fetchone()

        if not result:
            logger.warning(f"Login failed for email: {user.email} - User not found.")
            raise HTTPException(status_code=400, detail="Invalid email or password")

        user_id, hashed_password, role, manager_id = result
        logger.debug(f"Stored hash for {user.email}: {hashed_password}")

        if not pwd_context.verify(user.password, hashed_password):
            logger.warning(f"Login failed for email: {user.email} - Incorrect password.")
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Generate JWT token
        token_data = {"sub": user.email, "id": user_id, "role": role}
        if role == "EMPLOYEE":
            token_data["manager_id"] = manager_id  # Include manager_id for employees

        access_token = create_access_token(data=token_data)
        logger.info(f"User {user.email} logged in successfully")

    except Exception as e:
        logger.error(f"Database error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        cur.close()
        conn.close()

    return {"access_token": access_token, "token_type": "bearer"}
