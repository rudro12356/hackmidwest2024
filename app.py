import os
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
    region_name="us-west-2"  # Choose the region where your Bedrock model is deployed
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
    
def pil_to_base64(image_data):
    """
    Converts an uploaded image to a base64 string.
    """
    return base64.b64encode(image_data).decode("utf-8")

def generate_conversation(system_prompts, messages):
    """
    Sends messages to the Claude model on AWS Bedrock and returns the response.
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

@app.route('/chat', methods=['POST'])
def chat():
    """
    API endpoint for handling chat requests. 
    Receives user message and location, incorporates weather data, and returns model response.
    """
    data = request.get_json()

    if not data or 'message' not in data or 'location' not in data:
        return jsonify({"error": "Message and location required"}), 400

    user_message = data['message']
    location = data['location']

    # Fetch weather data based on the user's location
    weather_data = get_weather_data(location)

    if weather_data:
        # Incorporate the weather data into the system prompt
        weather_info = f"The current weather in {location} is {weather_data['weather_description']}, " \
                       f"with a temperature of {weather_data['temperature']}°C and humidity of {weather_data['humidity']}%."
    else:
        weather_info = "Weather data is unavailable for the given location."

    # System prompt that includes weather data
    system_prompt = [{
        "text": f"""
        The farmer is located in {location}. {weather_info} Use this weather data to provide contextually relevant advice.
        You are an expert agricultural advisor for the farmer who is specializing in crop management, soil health, and disease prevention. Provide clear, step-by-step advice to farmers, using logical reasoning and simple explanations. 
        Incorporate weather and soil data when available to make your recommendations actionable and context-specific.

            For each query:
            1. Break down the reasoning behind your recommendation in a step-by-step manner.
            2. Use simple language to ensure the farmer understands your reasoning.
            3. Provide examples where relevant to clarify your suggestions.

            **Example 1**:
            Query: "What crops should I grow in sandy soil?"
            Response:
            1. Sandy soil drains quickly, which makes it ideal for crops that prefer well-drained soil.
            2. Crops like carrots, peanuts, and potatoes are well-suited to sandy soil because they thrive in low-moisture environments.
            Recommendation: I suggest growing carrots, peanuts, or potatoes, but ensure regular fertilization to improve soil nutrients.

            **Example 2**:
            Query: "How should I treat yellow spots on tomato leaves?"
            Response:
            1. Yellow spots can indicate a fungal disease like early blight or septoria leaf spot.
            2. Inspect the leaves for a yellow halo or browning in the center to confirm.
            3. Treat by removing affected leaves and applying a copper-based fungicide.
            Recommendation: Apply copper-based fungicide and ensure good airflow to reduce disease spread.

            **Example 3**:
            Query: "Should I water my crops today if it's going to rain tomorrow?"
            Response:
            1. Consider the current soil moisture and weather forecast.
            2. If the soil is still moist and rain is expected, it's better to wait to avoid overwatering.
            Recommendation: Check soil moisture levels. If moist, wait for the rain; if dry, water lightly.

        You will strictly only provide advice on crop management, soil health, and disease prevention. Avoid discussing other topics.
        """
    }]

    message = {
        "role": "user",
        "content": [{"text": user_message}]
    }

    # Get the response from Claude
    response = generate_conversation(system_prompt, [message])
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)