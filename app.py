import os
import json
import requests
import base64
from flask import Flask, request, jsonify
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Claude model through AWS Bedrock
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2"
)

# Flask app setup
app = Flask(__name__)

# Weatherstack API key from .env
WEATHERSTACK_API_KEY = os.getenv('WEATHER_API_KEY')

def get_weather_data(location):
    """
    Fetch weather data from Weatherstack API.
    """
    url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={location}"
    
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200 and 'current' in data:
        weather_info = data['current']
        return {
            'temperature': weather_info['temperature'],
            'humidity': weather_info['humidity'],
            'weather_description': weather_info['weather_descriptions'][0]
        }
    else:
        return None

def generate_conversation_text(system_prompts, messages):
    """
    Sends text-only messages to the Claude model on AWS Bedrock and returns the response.
    """
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    temperature = 0.3

    inference_config = {"temperature": temperature}

    # Send the message
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
    )

    # Extract the response content
    text_response = response["output"]["message"]["content"][0]["text"]
    return text_response

def generate_conversation_with_image(system_prompt, message, image_data):
    """
    Sends messages with image to the Claude model on AWS Bedrock and returns the response.
    """
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    prompt_config = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data["source"]["media_type"],
                            "data": image_data["source"]["data"],
                        },
                    },
                    {"type": "text", "text": message},
                ],
            }
        ],
        "system": system_prompt
    }

    body = json.dumps(prompt_config)
    accept = "application/json"
    content_type = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("content")[0].get("text")
    return results

@app.route('/chat', methods=['POST'])
def chat():
    """
    API endpoint for handling chat requests. 
    Receives user message, location, and optional image, incorporates weather data, and returns model response.
    """
    data = request.get_json()

    if not data or 'message' not in data or 'location' not in data:
        return jsonify({"error": "Message and location required"}), 400

    user_message = data['message']
    location = data['location']
    image_data = data.get('image')

    # Fetch weather data based on the user's location
    weather_data = get_weather_data(location)

    if weather_data:
        weather_info = f"The current weather in {location} is {weather_data['weather_description']}, " \
                       f"with a temperature of {weather_data['temperature']}°C and humidity of {weather_data['humidity']}%."
    else:
        weather_info = "Weather data is unavailable for the given location."

    # System prompt that includes weather data
    system_prompt = f"""
    The farmer is located in {location}. {weather_info} Use this weather data to provide contextually relevant advice.
    You are an expert agricultural advisor for the farmer who is specializing in crop management, soil health, and disease prevention. Provide clear, step-by-step advice to farmers, using logical reasoning and simple explanations. 
    Incorporate weather and soil data when available to make your recommendations actionable and context-specific.

    If an image is provided, analyze it for any visible plant diseases or issues, and incorporate your findings into your response.

    For each query:
    1. Break down the reasoning behind your recommendation in a step-by-step manner.
    2. Use simple language to ensure the farmer understands your reasoning.
    3. Provide examples where relevant to clarify your suggestions.

    You will strictly only provide advice on crop management, soil health, and disease prevention. Avoid discussing other topics.
    """

    if image_data:
        # Use invoke_model for queries with images
        response = generate_conversation_with_image(system_prompt, user_message, image_data)
    else:
        # Use converse for text-only queries
        messages = [{"role": "user", "content": [{"text": user_message}]}]
        response = generate_conversation_text([{"text": system_prompt}], messages)

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)