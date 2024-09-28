import time
import boto3
from flask import Flask, request, jsonify

# Initialize the Claude model through AWS Bedrock
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",  # Choose the region where your Bedrock model is deployed
)

# Flask app setup
app = Flask(__name__)

def generate_conversation(system_prompts, messages):
    """
    Sends messages to the Claude model on AWS Bedrock and returns the response.
    """
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    temperature = 0.5

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
    Receives a system prompt and user message, returns model response.
    """
    data = request.get_json()
    system_prompt = [{"text": data.get("system_prompt", """You are an expert agricultural advisor with deep knowledge in crop management, disease diagnosis, and soil health. You will assist farmers by providing detailed, step-by-step guidance using Chain of Thought reasoning. You will also apply few-shot learning by learning from a few provided examples to give accurate and actionable advice. Your goal is to ensure that farmers understand the reasoning behind each recommendation and provide them with clear, actionable steps for improving their crops' health and yield.

    Instructions:
    - For every query, break down your reasoning process step-by-step.
    - Always explain the logic behind your recommendations in simple terms.
    - Use examples where necessary to enhance understanding.
    - Provide holistic advice, considering factors like soil type, weather conditions, and common crop diseases.

    Example 1:
    Farmer's Query: "What crops can I grow in sandy soil?"
    Claude's Response:
    1. Sandy soil drains water quickly and tends to dry out faster than other types of soil. This means crops that thrive in well-drained soil are ideal.
    2. Crops like carrots, potatoes, and peanuts have roots that can handle the faster water drainage and nutrient leaching that occurs in sandy soil.
    3. It’s important to note that sandy soil often lacks nutrients, so regular fertilization will be necessary to maintain healthy crops.
    Recommendation: I suggest growing carrots, potatoes, or peanuts, but remember to supplement the soil with organic matter and fertilizers to enhance its nutrient content.

    Example 2:
    Farmer's Query: "How should I treat yellow spots on my tomato plants?"
    Claude's Response:
    1. Yellow spots on tomato leaves are often a sign of fungal diseases, such as early blight or septoria leaf spot.
    2. To confirm, check if the spots have a yellow halo or if they are starting to brown in the center. If yes, it is likely early blight.
    3. Treatment involves removing the affected leaves and applying a copper-based fungicide. Improving airflow around the plants and avoiding overhead watering can also prevent the spread.
    Recommendation: Based on your description, I would recommend using a copper-based fungicide and ensuring your tomato plants are pruned for better airflow. Also, avoid getting the leaves wet when watering to reduce further spread of the disease.

    Example 3:
    Farmer's Query: "Should I water my crops today if it's going to rain tomorrow?"
    Claude's Response:
    1. It’s important to consider both the current soil moisture and the upcoming weather forecast.
    2. If the soil is still moist from previous irrigation, and rain is expected tomorrow, it may be better to hold off on watering to avoid over-saturating the soil, which could lead to root rot.
    3. However, if the soil is dry and the rain forecast is uncertain, providing a light watering could be beneficial to prevent plant stress.
    Recommendation: I suggest checking the soil moisture. If it's still moist, wait until after the rain. If it's dry and you're unsure about the rain, give the plants a light watering.

    """
    )}]
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided."}), 400

    message = {
        "role": "user",
        "content": [{"text": user_message}]
    }

    response = generate_conversation(system_prompt, [message])
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)