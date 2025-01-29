import psycopg2
import os

# Database connection details
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "blu_reserve")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

def create_seats():
    """Insert 50 seats into the database."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port="5432"
        )
        cur = conn.cursor()

        # Clear existing seats (optional)
        cur.execute("DELETE FROM seats;")

        # Insert 50 seats (only seat_number, as per the schema)
        for seat_number in range(1, 51):  # Seat numbers between 1 and 50
            cur.execute("""
                INSERT INTO seats (seat_number) 
                VALUES (%s);
            """, (seat_number,))

        conn.commit()
        print("[✅] Successfully inserted 50 seats into the database.")

    except Exception as e:
        print(f"[❌] Error inserting seats: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


# Run the script
if __name__ == "__main__":
    create_seats()
