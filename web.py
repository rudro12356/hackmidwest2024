import streamlit as st
import requests
import json
import base64
from PIL import Image
import io

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    .css-1y0tads {display: none;}
    footer {visibility: hidden;}
    
    /* Main Chat Pane Styling */
    .main-pane {
        padding: 10px;
        background-color: #f4f4f4;
        border-radius: 10px;
        box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Side Pane Styling */
    .side-pane {
        padding: 20px;
        background-color: #2e7bcf;
        color: white;
        height: 100vh;
        border-radius: 10px;
    }
    
    /* Message Bubbles */
    .user-message {
        background-color: #d1ecf1;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        color: #0c5460;
    }
    
    .assistant-message {
        background-color: #f8d7da;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        color: #721c24;
    }

    /* Input Box Styling */
    .stTextInput>div>div>input {
        border-radius: 10px;
        padding: 10px;
        border: 2px solid #2e7bcf;
    }
    
    /* Button Styling */
    .stButton>button {
        background-color: #2e7bcf;
        color: white;
        border-radius: 5px;
        padding: 10px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# Function to convert PIL image to base64 string
def pil_to_base64(image, format="png"):
    with io.BytesIO() as buffer:
        image.save(buffer, format)
        return base64.b64encode(buffer.getvalue()).decode()


# Side pane for future features, useful tips, or links
with st.sidebar:
    # st.markdown("<div class='side-pane'>", unsafe_allow_html=True)

    # Add Farmer's ChatGPT logo or image
    st.image("https://img.freepik.com/premium-vector/farmer-using-smartphone-app-that-integrates-ai-technology-weather-data-alert-them-any_216520-124477.jpg", use_column_width=True)

    st.title("Farmer's Personal Assistant")
    st.write("Ask any farming-related questions.")
    st.write("Future Options:")
    st.write("- Crop Diseases")
    st.write("- Weather Forecasts")
    st.write("- Soil Recommendations")
    st.markdown("</div>", unsafe_allow_html=True)

# Title of the app
st.markdown("<h1 style='color:#2e7bcf;'>Farming Assistant</h1>", unsafe_allow_html=True)

# Placeholder for chat interface
st.markdown("<div class='main-pane'>", unsafe_allow_html=True)

# User input field
user_query = st.text_input("Ask me anything about farming:")

user_location = st.text_input("Enter your location (e.g., 'Lawrence, Kansas'):")

# user image input
uploaded_image = st.file_uploader("Upload an image of your crop (optional for disease detection):", type=["png", "jpg", "jpeg"])

# Button to get response
if st.button("Get Answer"):
    if user_query and user_location:
        # Payload for the API request
        api_url = "http://localhost:3000/chat"
        payload = {
            "message": user_query,
            "location": user_location
        }
        
        # If an image is uploaded, convert it to base64 and add it to the payload
        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            image_base64 = pil_to_base64(image)
            payload["image"] = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",  # Adjust media type based on image type
                    "data": image_base64
                }
            }
        
        try:
            # Make a POST request to the Flask API
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                st.markdown(f"<div class='user-message'>{user_query}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='assistant-message'>{data['response']}</div>", unsafe_allow_html=True)
            else:
                st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Failed to connect to the API: {str(e)}")
    else:
        st.warning("Please enter both a query and a location.")

st.markdown("</div>", unsafe_allow_html=True)