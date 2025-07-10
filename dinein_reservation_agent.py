import json
import os
from dotenv import load_dotenv
import boto3
from pydantic import BaseModel
from typing import List, Optional

# Load environment variables
load_dotenv()

# ---------- MCP CONTEXT ----------
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

# ---------- AWS BEDROCK CLIENT ----------
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
        modelId="amazon.titan-text-premier-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    return result["results"][0]["outputText"]

# ---------- RESERVATION LOGIC ----------
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

# ---------- MAIN FLOW ----------
if __name__ == "__main__":
    print("🛎️ Welcome to Hotel Dining Reservation Assistant!")
    user_input = input("🗣️ How can I help you today?\n> ")

    prompt = f"""
    Extract the structured reservation data from this customer message:
    \"{user_input}\"

    Respond ONLY with a valid JSON in this format:
    {{
      "party_size": int,
      "table_type": "booth" | "window" | "bar" | "standard" | "any",
      "date": "YYYY-MM-DD",
      "time": "HH:MM"
    }}

    If anything is missing, guess default values: table_type='any', time='19:00', date='2025-07-15'
    """

    response_text = invoke_nova(prompt)

    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError:
        print("❌ Could not parse reservation details from Nova.")
        print("Raw response:", response_text)
        exit(1)

    ctx = DiningReservationContext(
        date=extracted["date"],
        time=extracted["time"],
        party_size=extracted["party_size"],
        table_type=extracted["table_type"]
    )

    logic_response = reserve_table(ctx)

    confirmation_prompt = f"""
    You are a polite and helpful hotel dining reservation assistant.
    A guest asked: \"{user_input}\"
    System response: {logic_response}
    Generate a friendly confirmation or apology.
    """

    ai_response = invoke_nova(confirmation_prompt)
    print("\n🤖 Nova says:", ai_response)
