# Agentic-Hackathon

Step 1:  Install Dependencies

python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt

Step 2:Configure AWS Access

Edit the `.env` file in the root folder:

AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.titan-text-premier-v1:0 // You can use other models as well 

Step 3: Run the agent and type your prompt:
python dinein_reservation_agent.py

Example input:

book a table for 4 near the bar at 7:30 PM