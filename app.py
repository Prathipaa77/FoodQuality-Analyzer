import gradio as gr
from PIL import Image
import pytesseract
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from utils import clean_text

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Verify Tesseract installation
if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
    raise FileNotFoundError(f"Tesseract executable not found at {pytesseract.pytesseract.tesseract_cmd}. Ensure Tesseract is installed.")

# Load environment variables
load_dotenv(dotenv_path="D:/food/.env")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file. Ensure D:/food/.env contains GROQ_API_KEY=your_key starting with 'gsk_'.")
if not GROQ_API_KEY.startswith("gsk_"):
    raise ValueError("Invalid GROQ_API_KEY format. It must start with 'gsk_'. Get a valid key from https://console.groq.com.")

# HealthProfile class
class HealthProfile:
    def __init__(self):
        self.allergies = []
        self.dietary_restrictions = []

    def load_profile(self):
        self.allergies = ["gluten"]
        self.dietary_restrictions = ["low sugar", "high protein"]

# Chain class for LLM-based analysis
class Chain:
    def __init__(self):
        try:
            self.llm = ChatGroq(
                temperature=0,
                groq_api_key=GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile"  # Updated model
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize ChatGroq: {e}")

    def analyze_nutrients(self, cleaned_data, health_profile):
        prompt_analysis = PromptTemplate.from_template(
            """
            ### NUTRIENT DATA:
            {nutrient_data}

            ### HEALTH PROFILE:
            Allergies: {allergies}
            Dietary restrictions: {restrictions}

            ### INSTRUCTION:
            Based on the nutrient data and the health profile, provide personalized recommendations
            including potential benefits and risks. If relevant, suggest alternatives or usage limitations.
            ### RECOMMENDATION (NO PREAMBLE):
            """
        )
        chain_analysis = prompt_analysis | self.llm
        try:
            res = chain_analysis.invoke({
                "nutrient_data": cleaned_data,
                "allergies": ', '.join(health_profile.allergies),
                "restrictions": ', '.join(health_profile.dietary_restrictions)
            })
            return res.content
        except Exception as e:
            return f"Error generating recommendation: {e}. If this is a 400 error, check https://console.groq.com/docs/deprecations for supported models."

    def handle_user_query(self, cleaned_data, health_profile, user_query):
        prompt_query = PromptTemplate.from_template(
            """
            ### NUTRIENT DATA:
            {nutrient_data}

            ### HEALTH PROFILE:
            Allergies: {allergies}
            Dietary restrictions: {restrictions}

            ### USER QUERY:
            {user_query}

            ### INSTRUCTION:
            Based on the above information, answer the user's query about the product.
            """
        )
        query_analysis = prompt_query | self.llm
        try:
            res = query_analysis.invoke({
                "nutrient_data": cleaned_data,
                "allergies": ', '.join(health_profile.allergies),
                "restrictions": ', '.join(health_profile.dietary_restrictions),
                "user_query": user_query
            })
            return res.content
        except Exception as e:
            return f"Error processing query: {e}. If this is a 400 error, check https://console.groq.com/docs/deprecations for supported models."

# Function to extract nutrient data
def extract_nutrient_data(image):
    try:
        text = pytesseract.image_to_string(image)
        if not text.strip():
            raise ValueError("No text detected in the image. Try a clearer image.")
        print("Extracted Text:", text)  # Debug logging
        return text
    except Exception as e:
        raise ValueError(f"OCR failed: {e}")

# Gradio app logic
def process_inputs(image, user_query):
    try:
        if image is None:
            return "Please upload an image.", ""
        
        # Extract and clean nutrient data
        raw_nutrient_data = extract_nutrient_data(image)
        cleaned_data = clean_text(raw_nutrient_data)

        # Load health profile
        health_profile = HealthProfile()
        health_profile.load_profile()

        # Initialize LLM chain
        chain = Chain()

        # Generate recommendations
        recommendations = chain.analyze_nutrients(cleaned_data, health_profile)

        # Handle user query if provided
        query_response = ""
        if user_query and user_query.strip():
            query_response = chain.handle_user_query(cleaned_data, health_profile, user_query)
        
        return recommendations, query_response
    except Exception as e:
        return f"An Error Occurred: {e}", ""

# Custom CSS for background and styling
custom_css = """
body {
    background-image: url('https://png.pngtree.com/thumb_back/fw800/background/20231228/pngtree-view-from-above-a-delectable-bowl-of-pasta-with-kitchen-tools-image_13855598.png');
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
    min-height: 100vh;
}
.gradio-container {
    max-width: 1200px;
    margin: auto;
    padding: 20px;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 10px;
}
h1 {
    color: #2e7d32;
    text-align: center;
}
"""

# Gradio interface
with gr.Blocks(css=custom_css) as app:
    gr.Markdown("# 🥗 Personalized Health Recommendation Generator")
    
    with gr.Row():
        image_input = gr.Image(type="pil", label="Upload a product nutrient page image (PNG, JPG, JPEG)")
    
    with gr.Row():
        query_input = gr.Textbox(label="Ask a question about the product or share your personal concerns:", placeholder="e.g., Is this product safe for me?")
    
    submit_button = gr.Button("Submit")
    
    with gr.Row():
        recommendations_output = gr.Textbox(label="Personalized Recommendations", lines=10)
        query_output = gr.Textbox(label="Response to Your Query", lines=5)
    
    submit_button.click(
        fn=process_inputs,
        inputs=[image_input, query_input],
        outputs=[recommendations_output, query_output]
    )

# Launch the app
app.launch()