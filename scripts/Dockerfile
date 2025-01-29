# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the initialization script
COPY initialize_seats.py .

# Run the script on container startup
CMD ["python", "initialize_seats.py"]
