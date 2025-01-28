# Use Python slim image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install required libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service code
COPY . .

# Expose the port for the health service
EXPOSE 8005

# Start the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
