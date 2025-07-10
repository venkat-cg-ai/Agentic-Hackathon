import boto3
import json
from dotenv import load_dotenv
import os

load_dotenv()
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))

prompt = {
    "inputText": "Write a welcoming message to a hotel guest.",
    "textGenerationConfig": {
        "maxTokenCount": 200,
        "temperature": 0.7,
        "topP": 0.9,
        "stopSequences": []
    }
}

response = bedrock.invoke_model(
    modelId="amazon.titan-text-premier-v1:0",
    contentType="application/json",
    accept="application/json",
    body=json.dumps(prompt)
)

output = json.loads(response['body'].read())
print(output["results"][0]["outputText"])
