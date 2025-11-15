from flask import Flask, send_from_directory, Response, render_template, redirect, jsonify, request
from dotenv import load_dotenv
import os
from intense_experience import intense_experience_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(intense_experience_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)