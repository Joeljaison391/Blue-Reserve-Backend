from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from utils.database import get_db_connection
from utils.jwt_handler import get_current_user
from datetime import datetime, timedelta
import logging

# Initialize FastAPI
app = FastAPI(title="Booking Service")

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BookingRequest(BaseModel):
    seat_id: int
    start_time: str
    end_time: str

BLU_DOLLAR_COST = 5  # Cost per booking
MAX_DAILY_USAGE = 20  # Max BluDollars an employee can use per day


@app.post("/bookings")
def book_seat(request: BookingRequest, current_user: dict = Depends(get_current_user)):
    """
    Reserve a seat for a user. Ensures the employee has enough BluDollars before making a reservation.
    """
    try:
        start_dt = datetime.strptime(request.start_time, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(request.end_time, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use YYYY-MM-DD HH:MM")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if the seat is available
        cur.execute("""
            SELECT id FROM reservations 
            WHERE seat_id = %s AND (start_time < %s AND end_time > %s) AND status = 'RESERVED'
        """, (request.seat_id, end_dt, start_dt))

        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Seat is already booked for this time range")

        # Get employee's BluDollar usage & manager ID
        cur.execute("SELECT bluDollar_used, manager_id FROM employees WHERE id = %s", (current_user['id'],))
        employee = cur.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        bluDollar_used, manager_id = employee

        # Check total BluDollars used today
        today = datetime.now().date()
        cur.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE employee_id = %s AND type = 'RESERVATION' AND DATE(created_at) = %s
        """, (current_user['id'], today))
        total_used_today = cur.fetchone()[0] or 0

        if total_used_today + BLU_DOLLAR_COST > MAX_DAILY_USAGE:
            raise HTTPException(status_code=400, detail="Daily BluDollar usage limit reached (max 20 BluDollars)")

        # Get manager's BluDollar balance
        cur.execute("SELECT bluDollar_balance FROM managers WHERE id = %s", (manager_id,))
        manager_balance = cur.fetchone()
        if not manager_balance:
            raise HTTPException(status_code=404, detail="Manager not found")

        if manager_balance[0] < BLU_DOLLAR_COST:
            raise HTTPException(status_code=400, detail="Insufficient BluDollar balance")

        # Deduct BluDollar balance from manager
        cur.execute("UPDATE managers SET bluDollar_balance = bluDollar_balance - %s WHERE id = %s", (BLU_DOLLAR_COST, manager_id))

        # Update employee's used BluDollars
        cur.execute("UPDATE employees SET bluDollar_used = bluDollar_used + %s WHERE id = %s", (BLU_DOLLAR_COST, current_user['id']))

        # Record the transaction
        cur.execute("""
            INSERT INTO transactions (manager_id, employee_id, amount, type, reason)
            VALUES (%s, %s, %s, 'RESERVATION', 'Seat reservation')
        """, (manager_id, current_user['id'], BLU_DOLLAR_COST))

        # Reserve the seat
        cur.execute("""
            INSERT INTO reservations (seat_id, employee_id, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, 'RESERVED') RETURNING id
        """, (request.seat_id, current_user['id'], start_dt, end_dt))

        reservation_id = cur.fetchone()[0]
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"reservation_id": reservation_id, "message": "Seat booked successfully"}


@app.put("/bookings/{reservation_id}/cancel")
def cancel_booking(reservation_id: int, current_user: dict = Depends(get_current_user)):
    """
    Cancel a reservation, ensuring there is at least a 1-hour gap before the start time.
    Refunds BluDollars upon successful cancellation.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if the reservation exists
        cur.execute("""
            SELECT id, start_time, seat_id, employee_id FROM reservations 
            WHERE id = %s AND employee_id = %s AND status = 'RESERVED'
        """, (reservation_id, current_user['id']))

        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Reservation not found or already cancelled")

        reservation_start_time, seat_id, employee_id = result[1], result[2], result[3]

        # Ensure a 1-hour gap before cancellation is allowed
        current_time = datetime.now()
        if (reservation_start_time - current_time).total_seconds() < 3600:
            raise HTTPException(status_code=400, detail="Cannot cancel reservation less than 1 hour before start time")

        # Refund BluDollars
        cur.execute("SELECT manager_id FROM employees WHERE id = %s", (current_user['id'],))
        manager_id = cur.fetchone()[0]

        cur.execute("UPDATE managers SET bluDollar_balance = bluDollar_balance + %s WHERE id = %s", (BLU_DOLLAR_COST, manager_id))
        cur.execute("UPDATE employees SET bluDollar_used = bluDollar_used - %s WHERE id = %s", (BLU_DOLLAR_COST, current_user['id']))

        # Record the refund transaction
        cur.execute("""
            INSERT INTO transactions (manager_id, employee_id, amount, type, reason)
            VALUES (%s, %s, %s, 'CANCELLATION', 'Seat reservation cancellation refund')
        """, (manager_id, current_user['id'], BLU_DOLLAR_COST))

        # Cancel the reservation
        cur.execute("UPDATE reservations SET status = 'CANCELED' WHERE id = %s", (reservation_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"message": "Reservation cancelled and BluDollars refunded successfully"}
