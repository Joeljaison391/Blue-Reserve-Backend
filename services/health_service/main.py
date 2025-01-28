from fastapi import FastAPI
import subprocess
import platform
import psutil
import time
from datetime import datetime
from typing import Dict

app = FastAPI(title="Health Service")

# Start time of the service
START_TIME = time.time()


def get_uptime() -> str:
    """Calculate the uptime of the server."""
    current_time = time.time()
    uptime_seconds = int(current_time - START_TIME)
    uptime_minutes, seconds = divmod(uptime_seconds, 60)
    hours, minutes = divmod(uptime_minutes, 60)
    return f"{hours}h {minutes}m {seconds}s"


def get_running_services() -> Dict[str, str]:
    """Check the status of dependent services."""
    services = ["auth_service", "user_management_service", "seat_service", "reservation_service"]
    status = {}

    for service in services:
        try:
            # Check if the service container is running using Podman
            result = subprocess.run(
                ["podman", "inspect", "-f", "{{.State.Status}}", service],
                capture_output=True,
                text=True,
                check=False,
            )
            if "running" in result.stdout:
                status[service] = "Running"
            else:
                status[service] = "Not Running"
        except Exception as e:
            status[service] = f"Error: {str(e)}"

    return status


@app.get("/health")
def health_check():
    """Return detailed health information about the server and services."""
    try:
        # Get server details
        server_info = {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Processor": platform.processor(),
            "RAM": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
            "CPU Cores": psutil.cpu_count(),
            "Server Uptime": get_uptime(),
        }

        # Get services status
        services_status = get_running_services()

        return {
            "status": "Healthy",
            "server_info": server_info,
            "services_status": services_status,
        }

    except Exception as e:
        return {
            "status": "Unhealthy",
            "error": str(e),
        }


@app.get("/ping")
def ping():
    """Verify if the server and services are running successfully."""
    try:
        services_status = get_running_services()
        if all(status == "Running" for status in services_status.values()):
            return {"status": "Healthy", "message": "All services are running successfully."}
        else:
            return {"status": "Degraded", "message": "Some services are not running.", "services_status": services_status}
    except Exception as e:
        return {"status": "Unhealthy", "error": str(e)}
