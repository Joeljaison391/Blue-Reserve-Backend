import psycopg2
import os

# Database connection details (modify if needed)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "blu_reserve")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

# Predefined seat locations (you can customize)
SEAT_LOCATIONS = [
    "Ground Floor - Near Window", "Ground Floor - Center", "First Floor - Near Window",
    "First Floor - Center", "Second Floor - Balcony", "Second Floor - Lounge"
]


def create_seats():
    """Insert 50 seats into the database with 'AVAILABLE' status."""
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

        # Insert 50 seats (tables with 4 seats each)
        cur.execute("DELETE FROM seats")  # Clear existing seats (optional)

        table_id = 1
        for seat_number in range(1, 51):  # Create 50 seats
            location = SEAT_LOCATIONS[seat_number % len(SEAT_LOCATIONS)]  # Assign location

            # Insert seat into database
            cur.execute("""
                INSERT INTO seats (table_id, seat_number, location, status) 
                VALUES (%s, %s, %s, 'AVAILABLE')
            """, (table_id, (seat_number - 1) % 4 + 1, location))

            # Move to the next table every 4 seats
            if seat_number % 4 == 0:
                table_id += 1

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
