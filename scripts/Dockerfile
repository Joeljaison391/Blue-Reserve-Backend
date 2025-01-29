FROM python:3.9

WORKDIR /app

COPY initialize_seats.py /app/
COPY initialize_seats.sh /app/
RUN chmod +x /app/initialize_seats.sh

RUN pip install psycopg2

CMD ["/bin/sh", "/app/initialize_seats.sh"]

