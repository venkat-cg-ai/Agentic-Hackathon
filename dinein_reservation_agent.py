# dinein_agent_system.py

import json
import os
from typing import List, Optional
from datetime import datetime, timedelta
import random

try:
    from dotenv import load_dotenv
    from pydantic import BaseModel
    import boto3
except ImportError as e:
    print("\n🔧 Required packages not found. Please install dependencies with:")
    print("pip install boto3 python-dotenv pydantic")
    raise e

# Load environment variables
load_dotenv()

# ---------- Context Models ----------
class GuestProfile(BaseModel):
    guest_id: str
    name: str
    loyalty_status: str
    preferences: List[str]
    visit_history: List[str]

class ReservationRequest(BaseModel):
    guest_id: str
    party_size: int
    date: str
    time: str
    channel: str  # web, phone, kiosk, app
    table_type: Optional[str] = "any"

class Table(BaseModel):
    table_id: str
    seats: int
    type: str  # window, booth, bar, etc.
    is_available: bool = True
    reserved_slots: List[str] = []

class ReservationStatus(BaseModel):
    reservation_id: str
    guest_id: str
    table_id: Optional[str]
    status: str  # confirmed, waitlisted, canceled
    reason: Optional[str] = None

# ---------- Mock Data ----------
mock_tables = [
    Table(table_id=f"T{i}", seats=random.choice([2, 4, 6]), type=random.choice(["booth", "window", "standard"]))
    for i in range(1, 11)
]

mock_guest_profiles = {
    "G123": GuestProfile(
        guest_id="G123",
        name="Alice",
        loyalty_status="Gold",
        preferences=["window", "vegetarian"],
        visit_history=["2025-07-01", "2025-07-05"]
    )
}

mock_reservations = []
mock_waitlist = []

# ---------- AWS Bedrock Setup ----------
AWS_REGION = os.getenv("AWS_REGION")
MODEL_ID = "amazon.titan-text-premier-v1:0"

if AWS_REGION and MODEL_ID:
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
else:
    bedrock = None
    print("⚠️ AWS credentials or model ID not configured. Nova model will be disabled.")

def invoke_nova(prompt: str) -> str:
    if not bedrock:
        return "{}"  # Return mock empty JSON if Nova is not set up
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 500,
            "stopSequences": [],
            "temperature": 0.7,
            "topP": 0.9
        }
    }
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    return result["results"][0]["outputText"]

# ---------- Agent Functions ----------
def is_conflict(table: Table, date: str, time: str) -> bool:
    return f"{date} {time}" in table.reserved_slots

def predict_no_show(guest_id: str) -> bool:
    guest = mock_guest_profiles.get(guest_id)
    if not guest:
        return False
    return random.random() < 0.1  # 10% chance of no-show for demo

def autofill_waitlist():
    if not mock_waitlist:
        return
    print("🔄 Checking for autofill opportunities from waitlist...")
    for request in mock_waitlist[:]:
        status = table_optimization_agent(request)
        if status.status == "confirmed":
            print(f"✅ Waitlist guest {request.guest_id} promoted to reservation.")
            mock_waitlist.remove(request)

def table_optimization_agent(request: ReservationRequest) -> ReservationStatus:
    preferred_tables = [
        t for t in mock_tables
        if t.seats >= request.party_size and
           (request.table_type == "any" or t.type == request.table_type) and
           not is_conflict(t, request.date, request.time)
    ]

    guest = mock_guest_profiles.get(request.guest_id)
    if guest and guest.loyalty_status == "Gold":
        preferred_tables.sort(key=lambda x: 0 if x.type in guest.preferences else 1)

    if preferred_tables:
        table = preferred_tables[0]
        table.reserved_slots.append(f"{request.date} {request.time}")
        table.is_available = False
        reservation_id = f"R{random.randint(1000,9999)}"
        return ReservationStatus(
            reservation_id=reservation_id,
            guest_id=request.guest_id,
            table_id=table.table_id,
            status="confirmed"
        )
    else:
        mock_waitlist.append(request)
        return ReservationStatus(
            reservation_id=f"W{random.randint(1000,9999)}",
            guest_id=request.guest_id,
            table_id=None,
            status="waitlisted",
            reason="No available table at requested time"
        )

def guest_personalization_agent(guest_id: str) -> str:
    guest = mock_guest_profiles.get(guest_id)
    if not guest:
        return "Welcome, guest!"
    greeting = f"Welcome back {guest.name}! As a {guest.loyalty_status} member, we’ve prepared a {guest.preferences[0]} table for you."
    return greeting

def reservation_confirmation_agent(status: ReservationStatus, request: ReservationRequest) -> str:
    if status.status == "confirmed":
        return f"Your reservation for {request.party_size} guests at {request.time} on {request.date} is confirmed at Table {status.table_id}. We look forward to hosting you! 🍽️"
    else:
        return f"We’re currently full at that time. You’ve been added to the waitlist. We’ll let you know if a table becomes available. ⏳"

def pos_crm_sync_agent(status: ReservationStatus):
    print(f"[POS Sync] Reservation {status.reservation_id} for guest {status.guest_id} synced to POS/CRM.")

def kitchen_alert_agent(status: ReservationStatus):
    if status.status == "confirmed":
        print(f"👨‍🍳 Kitchen notified of reservation {status.reservation_id} for guest {status.guest_id}.")

def parse_natural_language_request(input_text: str) -> ReservationRequest:
    prompt = f"""
    You are a hotel dining reservation agent. Your goal is to:
    - Understand reservation requests in natural language
    - Extract structured data needed for automated reservation systems
    - Fulfill guest preferences, improve seating utilization, manage waitlists

    Context:
    - Input may come from web, phone, app, or kiosk
    - Consider loyalty level, table type, no-show risk, and capacity

    Extract the following JSON from the request:
    {{
      "guest_id": "G123",
      "party_size": int,
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "channel": "web",
      "table_type": "window" | "booth" | "bar" | "standard" | "any"
    }}

    Assume default values if not specified: time='19:00', date='2025-07-15', table_type='any'
    Request: "{input_text}"
    """
    response = invoke_nova(prompt)
    try:
        data = json.loads(response)
        return ReservationRequest(**data)
    except Exception as e:
        print("❌ Failed to parse response from Nova:", response)
        raise e

# ---------- Main ----------
if __name__ == "__main__":
    print("\n🛎️ Welcome to the Hotel Dining Reservation Assistant!")
    user_input = input("🗣️ How can I help you today?\n> ")

    try:
        req = parse_natural_language_request(user_input)
        greeting = guest_personalization_agent(req.guest_id)
        print("👋", greeting)

        if predict_no_show(req.guest_id):
            print("⚠️ This guest has a high risk of no-show.")

        status = table_optimization_agent(req)
        print("📋 Reservation Status:", status.status)

        confirmation = reservation_confirmation_agent(status, req)
        print("💬", confirmation)

        pos_crm_sync_agent(status)
        kitchen_alert_agent(status)
        autofill_waitlist()

    except Exception as err:
        print("⚠️ Error handling your request:", err)
