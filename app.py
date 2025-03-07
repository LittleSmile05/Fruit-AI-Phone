import streamlit as st
import numpy as np
from PIL import Image
import base64
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions

# Set page config for better mobile experience
st.set_page_config(
    page_title="FruitScan-AI", 
    page_icon="🍎",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Custom CSS for better mobile appearance and camera access
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    h1, h2, h3 {
        margin-bottom: 0.5rem;
    }
    #camera-container {
        margin-bottom: 1rem;
        text-align: center;
    }
    #camera-container video {
        width: 100%;
        max-width: 400px;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    #snapshot-button {
        background-color: #ff4b4b;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        margin-bottom: 10px;
    }
    #snapshot-button:hover {
        background-color: #ff2424;
    }
    .camera-guide {
        border: 2px dashed #aaa;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.title("🍎 FruitScan-AI")
st.subheader("Identify fruits with your camera")

# Load pre-trained model (MobileNet V2)
@st.cache_resource
def load_model():
    model = tf.keras.applications.MobileNetV2(weights='imagenet')
    return model

# Load model with progress indicator
with st.spinner("Loading AI model... (first run may take a moment)"):
    model = load_model()
    st.success("Model loaded successfully!")

# Define fruit categories with their WordNet IDs in ImageNet
fruit_categories = {
    'banana': 'n07753592',
    'apple': 'n07739125',
    'orange': 'n07747607',
    'lemon': 'n07749582',
    'pineapple': 'n07753275',
    'strawberry': 'n07745940',
    'pear': 'n07767847',
    'grape': 'n07758680',
    'pomegranate': 'n07768694',
    'mango': 'n07750100'
}

# Reverse mapping from ImageNet IDs to fruit names
fruit_id_map = {}
for fruit_name, fruit_id in fruit_categories.items():
    fruit_id_map[fruit_id] = fruit_name.capitalize()

# Image preprocessing function
def preprocess_image(image):
    img = image.resize((224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# Create a function to predict fruit
def predict_fruit(image, confidence_threshold=0.2):
    img = Image.fromarray(image) if isinstance(image, np.ndarray) else image
    img = img.convert('RGB')
    
    # Preprocess the image
    img_array = preprocess_image(img)
    
    # Make predictions
    predictions = model.predict(img_array)
    decoded_predictions = decode_predictions(predictions, top=10)[0]
    
    # Filter and process results
    all_fruit_results = []
    
    # Extract all fruit predictions
    for pred_id, pred_name, pred_score in decoded_predictions:
        # Check if the prediction is in our fruit categories
        for fruit_name, fruit_id in fruit_categories.items():
            # Check if the prediction ID contains our fruit ID or if names match
            if pred_id.startswith(fruit_id.split('n')[1]) or fruit_name.lower() in pred_name.lower():
                all_fruit_results.append((fruit_name.capitalize(), float(pred_score)))
                break
    
    # Add any missing fruits with 0 probability
    found_fruits = [item[0].lower() for item in all_fruit_results]
    for fruit_name in fruit_categories.keys():
        if fruit_name not in found_fruits:
            all_fruit_results.append((fruit_name.capitalize(), 0.0))
    
    # Sort by probability
    all_fruit_results.sort(key=lambda x: x[1], reverse=True)
    
    # Filter by threshold for display
    fruit_results = [(name, prob) for name, prob in all_fruit_results if prob >= confidence_threshold]
    
    return fruit_results, all_fruit_results

# Direct Camera Access with JavaScript
st.markdown("### 📸 Take a Picture of a Fruit")

# HTML and JavaScript for camera integration
camera_component = """
<div class="camera-guide">
    <p>📱 Position the fruit in the center of the camera view</p>
</div>
<div id="camera-container">
    <video id="video" autoplay playsinline></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <div>
        <button id="snapshot-button">📸 Take Picture</button>
    </div>
    <p id="status">Waiting for camera permission...</p>
    <input type="hidden" id="imageData">
</div>

<script>
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const snapshotButton = document.getElementById('snapshot-button');
    const imageDataInput = document.getElementById('imageData');
    const statusText = document.getElementById('status');
    let streamStarted = false;

    // Request camera permissions
    async function startCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: { ideal: "environment" } // Use back camera on mobile
                },
                audio: false
            };
            
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            streamStarted = true;
            statusText.textContent = "Camera ready! Point at a fruit and take a picture.";
        } catch (err) {
            console.error("Error accessing camera:", err);
            statusText.textContent = "Camera access denied. Please enable camera permissions in your browser.";
        }
    }

    // Take a snapshot when the button is clicked
    snapshotButton.addEventListener('click', function() {
        if (streamStarted) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            // Convert canvas to base64 image data
            const dataUrl = canvas.toDataURL('image/jpeg');
            imageDataInput.value = dataUrl;
            
            // Submit the form
            const parentForm = imageDataInput.closest('form');
            if (parentForm) {
                parentForm.dispatchEvent(new Event('submit', { cancelable: true }));
            }
            
            statusText.textContent = "Picture taken! Processing...";
        } else {
            statusText.textContent = "Camera not ready yet.";
        }
    });

    // Start the camera when the page loads
    document.addEventListener('DOMContentLoaded', startCamera);
    
    // Also try to start camera immediately (for when component is loaded dynamically)
    startCamera();
</script>
"""

# Create a form to handle the image data
with st.form(key="camera_form"):
    st.markdown(camera_component, unsafe_allow_html=True)
    camera_image_data = st.text_input("Image data", key="camera_data", label_visibility="collapsed")
    submit_button = st.form_submit_button("Process Image", use_container_width=True)

# Alternative upload option
st.markdown("### OR")
uploaded_file = st.file_uploader("Upload a fruit photo", type=["jpg", "jpeg", "png"])

# Settings in an expander to save space on mobile
with st.expander("Advanced Settings"):
    confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.2)

# Process camera image
if submit_button and camera_image_data and camera_image_data.startswith('data:image'):
    with st.spinner("Processing camera image..."):
        # Extract the base64 data and convert to image
        base64_data = camera_image_data.split(',')[1]
        image_data = base64.b64decode(base64_data)
        
        # Create a PIL image from the decoded data
        from io import BytesIO
        image = Image.open(BytesIO(image_data))
        
        # Display the captured image
        st.image(image, caption="Captured image", use_column_width=True)
        
        # Convert to RGB (in case it's RGBA)
        image = image.convert("RGB")
        
        # Make prediction
        fruit_results, all_fruit_results = predict_fruit(image, confidence_threshold)
        
        # Display results
        st.markdown("### 🔍 Results")
        
        if fruit_results:
            # Create a more visual result display
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Fruit**")
            with col2:
                st.markdown("**Confidence**")
            
            for fruit_name, prob in fruit_results:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"{fruit_name}")
                with col2:
                    # Create a visual confidence meter
                    progress_color = "green" if prob > 0.7 else "orange" if prob > 0.4 else "red"
                    st.markdown(
                        f"<div style='width:100%;background-color:#ddd;height:20px;border-radius:10px'>"
                        f"<div style='width:{int(prob*100)}%;background-color:{progress_color};height:20px;border-radius:10px'></div>"
                        f"</div>{prob:.1%}",
                        unsafe_allow_html=True
                    )
        else:
            st.warning("No fruits detected with sufficient confidence. Try adjusting the threshold or taking a clearer photo.")

        # Show "Other Possibilities" in an expander
        with st.expander("See all possibilities"):
            for fruit_name, prob in all_fruit_results:
                st.markdown(f"- {fruit_name}: {prob:.1%}")

# Process uploaded image
elif uploaded_file is not None:
    # Add progress indicators for better UX
    with st.spinner("Processing uploaded image..."):
        # Load and display the image
        image = Image.open(uploaded_file)
        st.image(image, caption="Your fruit", use_column_width=True)
        
        # Convert to RGB (in case it's RGBA or other format)
        image = image.convert("RGB")
        
        # Make prediction
        fruit_results, all_fruit_results = predict_fruit(image, confidence_threshold)
        
        # Display results with nicer formatting
        st.markdown("### 🔍 Results")
        
        if fruit_results:
            # Create a more visual result display
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Fruit**")
            with col2:
                st.markdown("**Confidence**")
            
            for fruit_name, prob in fruit_results:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"{fruit_name}")
                with col2:
                    # Create a visual confidence meter
                    progress_color = "green" if prob > 0.7 else "orange" if prob > 0.4 else "red"
                    st.markdown(
                        f"<div style='width:100%;background-color:#ddd;height:20px;border-radius:10px'>"
                        f"<div style='width:{int(prob*100)}%;background-color:{progress_color};height:20px;border-radius:10px'></div>"
                        f"</div>{prob:.1%}",
                        unsafe_allow_html=True
                    )
        else:
            st.warning("No fruits detected with sufficient confidence. Try adjusting the threshold or taking a clearer photo.")

        # Show "Other Possibilities" in an expander
        with st.expander("See all possibilities"):
            for fruit_name, prob in all_fruit_results:
                st.markdown(f"- {fruit_name}: {prob:.1%}")

# Information section
st.markdown("---")
st.markdown("""
### 📱 About FruitScan-AI
This app uses a pre-trained AI model to identify fruits from photos. 
It works best with common fruits like apples, bananas, oranges, and strawberries.

**Supported Fruits**:
""")

# Show supported fruits in a nicer grid layout
fruit_cols = st.columns(2)
for i, fruit in enumerate([f.capitalize() for f in fruit_categories.keys()]):
    fruit_cols[i % 2].markdown(f"- {fruit}")

# Troubleshooting section
st.markdown("---")
with st.expander("📋 Camera Troubleshooting"):
    st.markdown("""
    If you're having camera issues:
    
    1. **Camera Permission**: Make sure you've allowed camera access when prompted
    2. **Try a different browser**: Chrome and Safari work best
    3. **Use good lighting**: Make sure your fruit is well-lit
    4. **Alternative**: You can always use the upload option instead
    
    Note: The camera feature requires HTTPS for security reasons.
    """)

# Feedback mechanism 
with st.expander("❓ Having issues or want to give feedback?"):
    st.markdown("If the app isn't working as expected, try these troubleshooting steps:")
    st.markdown("1. Make sure your photo is clear and well-lit")
    st.markdown("2. Try a different fruit or angle")
    st.markdown("3. Adjust the confidence threshold")
    feedback = st.text_area("Share your feedback or issues here:")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! We'll use it to improve the app.")
