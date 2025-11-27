"""Simple end-to-end smoke tests for the MindCare API."""
import os
import sys
import uuid
from datetime import datetime, timedelta

try:
    import requests
except ImportError as exc:
    raise SystemExit("Install the requests package to run this script: pip install requests") from exc


API_ROOT = os.getenv("API_BASE_URL", "https://mindcare-backend-1diu.onrender.com/api")
SESSION = requests.Session()


class APITestError(RuntimeError):
    pass


def call(method: str, path: str, expected: int = 200, **kwargs):
    url = f"{API_ROOT}{path}"
    response = SESSION.request(method, url, timeout=30, **kwargs)
    body = None
    try:
        body = response.json()
    except ValueError:
        body = response.text
    print(f"{method} {path} -> {response.status_code}")
    if response.status_code != expected:
        raise APITestError(f"Unexpected status for {method} {path}: {response.status_code} {body}")
    return body


def main():
    suffix = uuid.uuid4().hex[:8]
    email = f"test-{suffix}@example.com"
    username = f"testuser_{suffix}"
    password = "Passw0rd!"

    register_payload = {
        "email": email,
        "username": username,
        "password": password,
        "full_name": "API Tester",
    }
    call("POST", "/auth/register", expected=201, json=register_payload)

    login_payload = {"email": email, "password": password}
    login_body = call("POST", "/auth/login", json=login_payload)
    token = login_body["access_token"]
    SESSION.headers.update({"Authorization": f"Bearer {token}"})

    call("GET", "/auth/me")

    profile_payload = {
        "full_name": "API Test User",
        "phone": "+1-202-555-0100",
        "gender": "other",
        "emergency_contact": "Friend (202-555-0199)",
        "medical_history": "hypertension",
        "psychiatric_history": "none",
        "date_of_birth": "1990-01-01",
    }
    call("PUT", "/profile", json=profile_payload)

    call("GET", "/medications")

    med_payload = {
        "name": "Vitamin D",
        "dosage": "1000 IU",
        "frequency": "Daily",
        "time_to_take": "08:00",
        "start_date": datetime.utcnow().date().isoformat(),
        "end_date": (datetime.utcnow().date() + timedelta(days=30)).isoformat(),
        "refill_date": (datetime.utcnow().date() + timedelta(days=25)).isoformat(),
        "doctor_name": "Dr. Smith",
        "doctor_contact": "dr.smith@example.com",
        "notes": "Take with breakfast",
        "reminder_enabled": True,
    }
    med_body = call("POST", "/medications", expected=201, json=med_payload)
    med_id = med_body["id"]

    med_update = {"notes": "Take with breakfast and water"}
    call("PUT", f"/medications/{med_id}", json=med_update)

    call("GET", "/medications")

    appointment_payload = {
        "title": "Therapy Session",
        "description": "Weekly therapy check-in",
        "doctor_name": "Dr. Adams",
        "location": "123 Wellness St",
        "appointment_date": datetime.utcnow().replace(microsecond=0).isoformat(),
        "reminder_time": 120,
    }
    appointment_body = call("POST", "/appointments", expected=201, json=appointment_payload)
    appointment_id = appointment_body["id"]

    appointment_update = {"status": "completed"}
    call("PUT", f"/appointments/{appointment_id}", json=appointment_update)

    call("GET", "/appointments")

    post_payload = {
        "title": "Coping Strategies",
        "content": "Sharing healthy coping strategies that worked this week.",
        "category": "support",
    }
    post_body = call("POST", "/forum/posts", expected=201, json=post_payload)
    post_id = post_body["id"]

    call("GET", "/forum/posts")
    call("GET", f"/forum/posts/{post_id}")

    reply_payload = {"content": "Thanks for sharing these tips!"}
    call("POST", f"/forum/posts/{post_id}/replies", expected=201, json=reply_payload)

    call("GET", "/dashboard/stats")

    call("DELETE", f"/appointments/{appointment_id}")
    call("DELETE", f"/medications/{med_id}")

    print("All API checks passed.")


if __name__ == "__main__":
    try:
        main()
    except APITestError as error:
        print(f"API test failed: {error}")
        sys.exit(1)
    except requests.RequestException as error:
        print(f"Request error: {error}")
        sys.exit(1)
