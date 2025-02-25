from flask import Flask, request, jsonify
import openai
import base64
import json
import os
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from io import BytesIO
app = Flask(__name__)

# Configure upload folder

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(file_stream):
    try:
        # Encode image from in-memory file
        encoded_image = base64.b64encode(file_stream.read()).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{encoded_image}"
        
        # Reset the file stream pointer
        file_stream.seek(0)

        # Make OpenAI API call
        response = openai.ChatCompletion.create(
            model='gpt-4-turbo',
            messages=[
                {
                    
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Return expiry date of the product in JSON format as product_expdate..."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ],
                }
            ],
            max_tokens=500,
        )

        # Process response
        json_string = response.choices[0].message["content"]
        json_string = json_string.replace("```json\n", "").replace("\n```", "")
        return json.loads(json_string)
    
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

@app.route('/process-image', methods=['GET', 'POST'])
def process_image_endpoint():
    try:
        # Check if image file is present in request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Check if a file was actually selected
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg'}), 400
        
        # Process the file in memory
        file_stream = BytesIO(file.read())
        file_stream.seek(0)

        # Process the image (pass the in-memory stream to your function)
        result = process_image(file_stream)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    # Ensure OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    app.run(debug=True, port=5000)