import json
import os
from dotenv import load_dotenv
import boto3
from pydantic import BaseModel
from typing import List, Optional

# ---------- Load Environment Variables ----------
load_dotenv()

# ---------- MCP Contexts ----------
class GuestProfileContext(BaseModel):
    guest_id: str
    loyalty_status: str
    preferences: List[str]

class DiningReservationContext(BaseModel):
    date: str
    time: str
    party_size: int
    table_type: Optional[str] = "standard"
    status: str = "pending"

# ---------- AWS Bedrock Client ----------
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))

def invoke_nova(prompt: str):
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 400,
            "stopSequences": [],
            "temperature": 0.7,
            "topP": 0.9
        }
    }
    response = bedrock.invoke_model(
        modelId="amazon.titan-text-premier-v1:0",  # e.g. "amazon.nova-premier-v1:0"
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    return result["results"][0]["outputText"]

# ---------- Table Availability Logic ----------
def check_table_availability(date, time, party_size, table_type):
    with open("data/table_layout.json") as f:
        tables = json.load(f)["tables"]

    try:
        with open("data/reservations.json") as f:
            reservations = json.load(f)
    except FileNotFoundError:
        reservations = {}

    reserved_tables = reservations.get(date, {}).get(time, [])
    available = []
    for table_id, details in tables.items():
        if (table_id not in reserved_tables and
            details["seats"] >= party_size and
            (table_type == "any" or details["type"] == table_type)):
            available.append(table_id)

    return available

# ---------- Reservation Handling ----------
def reserve_table(ctx: DiningReservationContext):
    available = check_table_availability(ctx.date, ctx.time, ctx.party_size, ctx.table_type)
    if available:
        reserved_table = available[0]
        ctx.status = "confirmed"

        try:
            with open("data/reservations.json", "r") as f:
                reservations = json.load(f)
        except FileNotFoundError:
            reservations = {}

        reservations.setdefault(ctx.date, {}).setdefault(ctx.time, []).append(reserved_table)

        with open("data/reservations.json", "w") as f:
            json.dump(reservations, f, indent=2)

        return f"✅ Table {reserved_table} reserved successfully!"
    else:
        ctx.status = "waitlisted"
        return "❌ No table available. You’ve been added to the waitlist."

# ---------- Main Execution ----------
if __name__ == "__main__":
    print("🛎️ Welcome to Hotel Dining Reservation Assistant!")
    user_input = input("🗣️ How can I help you today?\n> ")

    # Step 1: Prompt Nova to extract structured data
    reservation_prompt  = f"""
You are a helpful assistant. Extract reservation details from the user message below.

Customer: "{user_input}"

Respond ONLY with valid JSON in this exact format:
{{
  "party_size": 2,
  "table_type": "any",
  "date": "2025-07-15",
  "time": "19:00"
}}

- If any detail is missing, use defaults:
  - party_size: 2
  - table_type: "any"
  - date: "2025-07-15"
  - time: "19:00"

❗IMPORTANT: Do not include any explanation, code comments, or Markdown. Only return the JSON object.
"""


    response_text = invoke_nova(reservation_prompt)

    # Step 2: Parse JSON response
    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError:
        print("❌ Could not parse reservation details from Nova.")
        print("Raw response:", response_text)
        exit(1)

    # Step 3: Build context from structured data
    ctx = DiningReservationContext(
        date=extracted["date"],
        time=extracted["time"],
        party_size=extracted["party_size"],
        table_type=extracted["table_type"]
    )

    # Step 4: Reserve table based on availability
    logic_response = reserve_table(ctx)

    # Step 5: Ask Nova to generate polite confirmation
    confirmation_prompt = f"""
    You are a polite and helpful hotel dining reservation assistant.
    A guest said: \"{user_input}\"
    The system action was: \"{logic_response}\"
    Please generate a friendly confirmation or apology message for the guest.
    """

    ai_response = invoke_nova(confirmation_prompt)
    print("\n🤖 Nova says:", ai_response)
