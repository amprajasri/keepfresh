from flask import Flask, request, jsonify
from openai import OpenAI
import base64
import json
import os
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image(image_path):
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Encode image
        image_url = f"data:image/jpeg;base64,{encode_image(image_path)}"
        
        # Make OpenAI API call
        response = client.chat.completions.create(
            model='gpt-4-turbo',
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Return manucature date and expiry date and name of the product in json format as item_name,item_mfd,item_exp, the expiry date and manufacture date can also be given using other similar terms but in json it should only be given in 'YYYY-MM-DD' as item_mfd and item_exp , the format should be as 'YYYY-MM-DD' if any of 3 fields are not available and predictable then give as 'not found'in respective field and for some product mfg and best before will be given based on that exp should be calculated. if only single date is given and it is beyond todays date"
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
        json_string = response.choices[0].message.content
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
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the image
        result = process_image(filepath)
        
        # Clean up - remove the uploaded file
        os.remove(filepath)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    app.run(debug=True, port=5000)