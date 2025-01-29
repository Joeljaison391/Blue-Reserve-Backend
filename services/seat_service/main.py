from fastapi import FastAPI, HTTPException, Query, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.database import get_db_connection
from utils.jwt_handler import get_current_user
from datetime import datetime
import logging

# Initialize FastAPI
app = FastAPI(title="Seat Management Service")
security = HTTPBearer()

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@app.get("/seats")
def get_seats(
    start_time: str = Query(..., description="Start time in YYYY-MM-DD HH:MM format"),
    end_time: str = Query(..., description="End time in YYYY-MM-DD HH:MM format"),
    filter: str = Query("available", description="Filter: 'available' for free seats, 'all' for all seats"),
    current_user: dict = Depends(get_current_user)  # Authenticate user
):
    """
    Fetch seats based on the given time range.

    - `filter="available"` → Returns only available seats.
    - `filter="all"` → Returns all seats (both available and reserved).
    - Requires authentication via JWT.
    """

    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use YYYY-MM-DD HH:MM")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if filter.lower() == "available":
            # Fetch only available seats during the given time range
            query = """
                SELECT id, table_id, seat_number, location, status
                FROM seats
                WHERE id NOT IN (
                    SELECT seat_id FROM reservations
                    WHERE (start_time < %s AND end_time > %s)
                )
            """
            cur.execute(query, (end_dt, start_dt))

        elif filter.lower() == "all":
            # Fetch all seats, regardless of reservation status
            query = """
                SELECT id, table_id, seat_number, location, status FROM seats
            """
            cur.execute(query)

        else:
            raise HTTPException(status_code=400, detail="Invalid filter value. Use 'available' or 'all'.")

        seats = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return [
        {"id": seat[0], "table_id": seat[1], "seat_number": seat[2], "location": seat[3], "status": seat[4]}
        for seat in seats
    ]


@app.get("/seats/{seat_id}")
def get_seat_details(seat_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get details of a specific seat along with its reserved time slots.
    - Requires authentication via JWT.
    """

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch seat details
        cur.execute("""
            SELECT id, table_id, seat_number, location, status
            FROM seats WHERE id = %s
        """, (seat_id,))

        seat = cur.fetchone()
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")

        # Fetch reservation time slots for this seat
        cur.execute("""
            SELECT start_time, end_time, status FROM reservations WHERE seat_id = %s
        """, (seat_id,))

        reservations = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    return {
        "seat_id": seat[0],
        "table_id": seat[1],
        "seat_number": seat[2],
        "location": seat[3],
        "status": seat[4],
        "reservations": [
            {"start_time": res[0], "end_time": res[1], "status": res[2]}
            for res in reservations
        ]
    }
