from flask import Flask, send_from_directory, Response, render_template, redirect, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from intense_experience import intense_experience_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(intense_experience_bp)

@app.route('/')
def index():
    # Parse URL parameters for different entry points
    suite_id = request.args.get('suite_id')
    service_id = request.args.get('service_id')
    
    # If service_id is not provided, redirect with default service_id
    if not service_id:
        service_id = '7ba0b732-93cc-477a-861d-b3850108b730'
        params = {'service_id': service_id}
        if suite_id:
            params['suite_id'] = suite_id
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return redirect(f'/?{query_string}')

    # Pass parameters to template for JavaScript access
    return render_template('index.html', suite_id=suite_id, service_id=service_id)

    # Example URL parameters for different entry points:
    # Gaia Journée: ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=f723bd5a-04fe-479c-bab4-b3850108c66f
    # Gaia Nuitée: ?service_id=7ba0b732-93cc-477a-861d-b3850108b730&suite_id=3872869e-6278-4c64-aea8-b3850108c66f
    # Intense Journée: ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=e4706d3a-2a06-4cb7-a449-b3850108c66f
    # Intense Nuitée: ?service_id=7ba0b732-93cc-477a-861d-b3850108b730&suite_id=f867b5c6-f62d-451c-96ec-b3850108c66f
    # Ignis Journée: ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=78a614b1-199d-4608-ab89-b3850108c66f
    # Extase Journée: ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=68b87fe5-7b78-4067-b5e7-b3850108c66f
    # Extase Nuitée: ?service_id=7ba0b732-93cc-477a-861d-b3850108b730&suite_id=0d535116-b1db-476e-8bff-b3850108c66f
    

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)
    
#dummy comment for deploy testing