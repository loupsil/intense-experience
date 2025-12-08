from flask import Flask, send_from_directory, Response, render_template, redirect, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from intense_experience import intense_experience_bp
from config import NIGHT_SERVICE_ID

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
    
    # If service_id is not provided, redirect with default service_id (nuitée)
    if not service_id:
        service_id = NIGHT_SERVICE_ID
        params = {'service_id': service_id}
        if suite_id:
            params['suite_id'] = suite_id
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return redirect(f'/?{query_string}')

    # Pass parameters to template for JavaScript access
    return render_template('index.html', suite_id=suite_id, service_id=service_id)

    # Example URL parameters for different entry points:

    # =============================================================================
    # DEMO ENVIRONMENT URLS
    # =============================================================================

    # Service-only URLs (no specific suite selected):
    # Journée Service (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf
    # Nuitée Service (DEMO): ?service_id=7ba0b732-93cc-477a-861d-b3850108b730

    # Suites with both Journée and Nuitée services:
    # Gaia Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=f723bd5a-04fe-479c-bab4-b3850108c66f
    # Gaia Nuitée (DEMO): ?service_id=7ba0b732-93cc-477a-861d-b3850108b730&suite_id=3872869e-6278-4c64-aea8-b3850108c66f
    # Intense Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=e4706d3a-2a06-4cb7-a449-b3850108c66f
    # Intense Nuitée (DEMO): ?service_id=7ba0b732-93cc-477a-861d-b3850108b730&suite_id=f867b5c6-f62d-451c-96ec-b3850108c66f
    # Extase Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=68b87fe5-7b78-4067-b5e7-b3850108c66f
    # Extase Nuitée (DEMO): ?service_id=7ba0b732-93cc-477a-861d-b3850108b730&suite_id=0d535116-b1db-476e-8bff-b3850108c66f

    # Suites with Journée service only:
    # Chambre EUPHORYA Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=f5539e51-9db0-4082-b87e-b3850108c66f
    # Chambre IGNIS Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=78a614b1-199d-4608-ab89-b3850108c66f
    # Chambre KAIROS Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=67ece5a2-65e2-43c5-9079-b3850108c66f
    # Chambre AETHER Journée (DEMO): ?service_id=86fcc6a7-75ce-457a-a425-b3850108b6bf&suite_id=1113bcbe-ad5f-49c7-8dc0-b3850108c66f

    # =============================================================================
    # PRODUCTION ENVIRONMENT URLS
    # =============================================================================

    # Service-only URLs (no specific suite selected):
    # Journée Service (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d
    # Nuitée Service (PROD): ?service_id=86f73626-4488-4cb2-887b-b1e30088b6f4

    # Suites with both Journée and Nuitée services:
    # Gaia Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=f9f1b450-f6b8-40ba-93fe-b2b501453c7a
    # Gaia Nuitée (PROD): ?service_id=86f73626-4488-4cb2-887b-b1e30088b6f4&suite_id=66f622d5-7632-4e23-8e16-b2b50129835e
    # Intense Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=57ac61e2-cd46-47d1-a032-b2b501448106
    # Intense Nuitée (PROD): ?service_id=86f73626-4488-4cb2-887b-b1e30088b6f4&suite_id=0f596098-93aa-432a-9bf2-b1e30088bcdb
    # Extase Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=6bf55cbf-67a3-4a25-b7a8-b2b50144ecf5
    # Extase Nuitée (PROD): ?service_id=86f73626-4488-4cb2-887b-b1e30088b6f4&suite_id=dcb31253-17bd-47d5-8c2b-b2b50129b921

    # Suites with Journée service only:
    # Chambre EUPHORYA Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=7cb2802a-6404-41b2-80a3-b2b50146ae6f
    # Chambre IGNIS Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=15b14722-8aa0-482b-897c-b2b501457cac
    # Chambre KAIROS Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=4b5a16dd-3ac1-40a0-a7ff-b2b5014701e7
    # Chambre AETHER Journée (PROD): ?service_id=7664a134-ac16-464c-80c0-b2b5006f292d&suite_id=9465a9fe-3295-476c-a7f2-b2b50145d659
    

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)
    
#dummy comment for deploy testing