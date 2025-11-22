from flask import Blueprint, jsonify, request
import os
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime, timedelta, timezone
import uuid
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz
from bulk_availability import check_bulk_availability_journee, check_bulk_availability_nuitee

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create blueprint
intense_experience_bp = Blueprint('intense_experience', __name__)

# Mews API configuration
MEWS_BASE_URL = "https://api.mews-demo.com/api/connector/v1"
CLIENT_TOKEN = os.getenv('ClientToken')
ACCESS_TOKEN = os.getenv('AccessToken')
ENTERPRISE_ID = "c390a691-e9a0-4aa0-860c-b3850108ab4c"

# Service IDs
DAY_SERVICE_ID = "86fcc6a7-75ce-457a-a425-b3850108b6bf"  # JOURNEE
NIGHT_SERVICE_ID = "7ba0b732-93cc-477a-861d-b3850108b730"  # NUITEE

# Default cleaning buffer in hours
CLEANING_BUFFER_HOURS = 1

# Booking duration limits for journee bookings
DAY_MIN_HOURS = 3
DAY_MAX_HOURS = 6

# Arrival and departure times for journee bookings
ARRIVAL_TIMES = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
DEPARTURE_TIMES = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']

# Default check-in and check-out hours for nuitée bookings
NIGHT_CHECK_IN_HOUR = 19  # 19:00 (7:00 PM)
NIGHT_CHECK_OUT_HOUR = 10  # 10:00 (10:00 AM)

def make_mews_request(endpoint, payload):
    """Make a request to Mews API"""
    url = f"{MEWS_BASE_URL}/{endpoint}"
    payload.update({
        "ClientToken": CLIENT_TOKEN,
        "AccessToken": ACCESS_TOKEN
    })

    try:
        logger.debug(f"Making request to: {url}")
        logger.debug(f"Request payload: {payload}")
        
        response = requests.post(url, json=payload)
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        # Try to get response body even on error
        try:
            response_json = response.json()
            logger.debug(f"Response body: {response_json}")
        except:
            logger.debug(f"Response text: {response.text}")
            response_json = None
        
        response.raise_for_status()
        return response_json
    except requests.exceptions.HTTPError as e:
        logger.error(f"Mews API HTTP error: {e}")
        logger.error(f"Status code: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Mews API request error: {e}")
        return None

@intense_experience_bp.route('/intense_experience-api/services', methods=['GET'])
def get_services():
    """Get available services (day/night)"""
    result = make_mews_request("services/getAll", {})

    if result and "Services" in result:
        # Filter to only show NUITEE and JOURNEE services
        services = [s for s in result["Services"]
                   if s.get("Type") == "Reservable" and
                   s.get("Id") in [DAY_SERVICE_ID, NIGHT_SERVICE_ID]]

        return jsonify({"services": services, "status": "success"})

    logger.error("Failed to fetch services or no services in response")
    return jsonify({"error": "Failed to fetch services", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/suites', methods=['GET'])
def get_suites():
    """Get available suites for a service"""
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify({"error": "Service ID required", "status": "error"}), 400

    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "ServiceIds": [service_id],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("resourceCategories/getAll", payload)
    if result and "ResourceCategories" in result:
        # Filter to only show suites (not buildings/floors)
        suites = [cat for cat in result["ResourceCategories"]
                 if cat.get("Type") in ["Suite", "Room"] and cat.get("IsActive")]
        return jsonify({"suites": suites, "status": "success"})
    return jsonify({"error": "Failed to fetch suites", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/bulk-availability-journee', methods=['POST'])
def bulk_availability_journee_route():
    """Check availability for day bookings (journée) - shows date as unavailable if no valid time slots remain"""
    data = request.json
    result = check_bulk_availability_journee(make_mews_request, data)
    if isinstance(result, tuple):
        # Error case: (error_dict, status_code)
        return jsonify(result[0]), result[1]
    return jsonify(result)
    

@intense_experience_bp.route('/intense_experience-api/bulk-availability-nuitee', methods=['POST'])
def bulk_availability_nuitee_route():
    """Check availability for multiple dates displayed in calendar, chunked into 4-day periods"""
    data = request.json
    result = check_bulk_availability_nuitee(make_mews_request, data)
    if isinstance(result, tuple):
        # Error case: (error_dict, status_code)
        return jsonify(result[0]), result[1]
    return jsonify(result)
    


@intense_experience_bp.route('/intense_experience-api/availability', methods=['POST'])
def check_availability():
    """Check availability for a date range with cleaning buffers"""
    data = request.json
    service_id = data.get('service_id')
    suite_id = data.get('suite_id')
    start_date = data.get('start_date')  # ISO format
    end_date = data.get('end_date')      # ISO format
    booking_type = data.get('booking_type')  # 'day' or 'night'

    if not all([service_id, start_date, end_date]):
        logger.error("Missing required parameters")
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400

    # Add cleaning buffers
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

    if booking_type == 'night':
        # For nights: add buffer before and after
        buffered_start = (start_dt - timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        buffered_end = (end_dt + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
    else:
        # For days: add buffer after
        buffered_start = start_dt.isoformat()
        buffered_end = (end_dt + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()

    payload = {
        "Client": "Intense Experience Booking",
        "StartUtc": buffered_start,
        "EndUtc": buffered_end
    }

    result = make_mews_request("reservations/getAll", payload)
    if result is None:
        logger.error("Failed to get reservations from Mews API")
        return jsonify({"error": "Failed to check availability", "status": "error"}), 500

    # Check if suite is available (no overlapping reservations)
    is_available = True
    conflicting_reservations = []

    if "Reservations" in result:
        for reservation in result["Reservations"]:
            res_requested_category = reservation.get('RequestedCategoryId')

            if suite_id:
                # Check specific suite availability
                if res_requested_category == suite_id:
                    conflicting_reservations.append(reservation)
                    is_available = False
            else:
                # General availability check - any reservation blocks the time
                conflicting_reservations.append(reservation)
                is_available = False

    logger.info(f"Availability check completed - available: {is_available}, conflicts: {len(conflicting_reservations)}")

    return jsonify({
        "available": is_available,
        "conflicting_reservations": conflicting_reservations,
        "status": "success"
    })

@intense_experience_bp.route('/intense_experience-api/pricing', methods=['POST'])
def get_pricing():
    """Get pricing for a date range"""
    data = request.json
    rate_id = data.get('rate_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    suite_id = data.get('suite_id')

    logger.info("=" * 80)
    logger.info("PRICING REQUEST RECEIVED")
    logger.info("=" * 80)
    logger.info(f"Rate ID: {rate_id}")
    logger.info(f"Start Date: {start_date}")
    logger.info(f"End Date: {end_date}")
    logger.info(f"Suite ID: {suite_id}")

    if not all([rate_id, start_date, end_date]):
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400

    # For night bookings, set time to 23:00:00.000Z
    # Rate ID for nuitée: 'ed9391ac-b184-4876-8cc1-b3850108b8b0'
    if rate_id == 'ed9391ac-b184-4876-8cc1-b3850108b8b0':
        # Extract date part and append 23:00:00.000Z for night bookings
        first_time_unit = start_date.split('T')[0] + 'T23:00:00.000Z'
        last_time_unit = end_date.split('T')[0] + 'T23:00:00.000Z'
        logger.info(f"PRICING: Nuitée detected - adjusting time units to 23:00:00.000Z")
        logger.info(f"PRICING: Original start_date: {start_date}, adjusted: {first_time_unit}")
        logger.info(f"PRICING: Original end_date: {end_date}, adjusted: {last_time_unit}")
    else:
        # For day bookings, keep the original logic
        first_time_unit = start_date
        last_time_unit = end_date
        logger.info(f"PRICING: Journée detected - using original time units")

    logger.info(f"PRICING: Final payload time units - FirstTimeUnitStartUtc: {first_time_unit}, LastTimeUnitStartUtc: {last_time_unit}")

    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "Client": "Intense Experience Booking",
        "RateId": rate_id,
        "FirstTimeUnitStartUtc": first_time_unit,
        "LastTimeUnitStartUtc": last_time_unit
    }

    result = make_mews_request("rates/getPricing", payload)
    if result and "CategoryPrices" in result:
        # Find pricing for specific suite or return all
        if suite_id:
            for category_price in result["CategoryPrices"]:
                if category_price.get("CategoryId") == suite_id:
                    return jsonify({
                        "pricing": category_price,
                        "currency": result.get("Currency"),
                        "status": "success"
                    })
        return jsonify({
            "pricing": result["CategoryPrices"],
            "currency": result.get("Currency"),
            "status": "success"
        })

    return jsonify({"error": "Failed to fetch pricing", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/rates', methods=['GET'])
def get_rates():
    """Get available rates"""
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("rates/getAll", payload)
    if result and "Rates" in result:
        return jsonify({"rates": result["Rates"], "status": "success"})
    return jsonify({"error": "Failed to fetch rates", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/products', methods=['GET'])
def get_products():
    """Get available products (upsells/options)"""
    service_ids = [DAY_SERVICE_ID, NIGHT_SERVICE_ID]

    payload = {
        "ServiceIds": service_ids,
        "EnterpriseIds": [ENTERPRISE_ID],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("products/getAll", payload)
    if result and "Products" in result:
        return jsonify({"products": result["Products"], "status": "success"})
    return jsonify({"error": "Failed to fetch products", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/age-categories', methods=['GET'])
def get_age_categories():
    """Get available age categories for services"""
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("ageCategories/getAll", payload)
    if result and "AgeCategories" in result:
        return jsonify({"age_categories": result["AgeCategories"], "status": "success"})
    return jsonify({"error": "Failed to fetch age categories", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/create-customer', methods=['POST'])
def create_customer():
    """Create a new customer"""
    data = request.json

    # Support both snake_case and camelCase for frontend compatibility
    first_name = data.get('first_name') or data.get('firstName')
    last_name = data.get('last_name') or data.get('lastName')
    email = data.get('email')
    phone = data.get('phone')

    if not all([first_name, last_name, email]):
        logger.error("Missing required customer information")
        logger.error(f"  first_name present: {bool(first_name)}")
        logger.error(f"  last_name present: {bool(last_name)}")
        logger.error(f"  email present: {bool(email)}")
        return jsonify({"error": "Missing required customer information", "status": "error"}), 400

    payload = {
        "Client": "Intense Experience Booking",
        "FirstName": first_name,
        "LastName": last_name,
        "Email": email,
        "Phone": phone,
        "OverwriteExisting": True  # Allow updating existing customer with same email
    }

    result = make_mews_request("customers/add", payload)

    if result:
        # Mews API returns the customer object directly, not wrapped in an array
        if "Id" in result:
            customer = result
            return jsonify({"customer": customer, "status": "success"})
        # Some endpoints may return as array
        elif "Customers" in result and result["Customers"]:
            customer = result["Customers"][0]
            return jsonify({"customer": customer, "status": "success"})

    logger.error("Failed to create customer - no valid customer in response")
    return jsonify({"error": "Failed to create customer", "status": "error"}), 500

def get_adult_age_category_for_service(service_id):
    """Get the adult age category ID for a specific service"""
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("ageCategories/getAll", payload)
    if result and "AgeCategories" in result:
        for category in result["AgeCategories"]:
            if (category.get("ServiceId") == service_id and
                category.get("Classification") == "Adult" and
                category.get("IsActive")):
                return category.get("Id")

    # Fallback to hardcoded values if API fails
    if service_id == DAY_SERVICE_ID:
        return "a78b7aca-fa0b-4199-8b4e-b3850108b8a5"  # Day service adult category
    elif service_id == NIGHT_SERVICE_ID:
        return "6cef9c83-4199-4b40-972b-b3850108b8a6"  # Night service adult category

    return "6cef9c83-4199-4b40-972b-b3850108b8a6"  # Default fallback

@intense_experience_bp.route('/intense_experience-api/create-reservation', methods=['POST'])
def create_reservation():
    """Create a reservation"""
    data = request.json

    service_id = data.get('service_id')
    customer_id = data.get('customer_id')
    suite_id = data.get('suite_id')
    rate_id = data.get('rate_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    person_count = data.get('person_count', 2)
    options = data.get('options', [])

    if not all([service_id, customer_id, suite_id, rate_id, start_date, end_date]):
        logger.error("Missing required reservation parameters")
        logger.error(f"  service_id present: {bool(service_id)}")
        logger.error(f"  customer_id present: {bool(customer_id)}")
        logger.error(f"  suite_id present: {bool(suite_id)}")
        logger.error(f"  rate_id present: {bool(rate_id)}")
        logger.error(f"  start_date present: {bool(start_date)}")
        logger.error(f"  end_date present: {bool(end_date)}")
        return jsonify({"error": "Missing required reservation parameters", "status": "error"}), 400

    # Validate that start_date is before end_date
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if start_dt >= end_dt:
            logger.error(f"Invalid date range: StartUtc ({start_date}) must be before EndUtc ({end_date})")
            return jsonify({
                "error": "Invalid date range: Start date must be before end date",
                "status": "error"
            }), 400
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse dates: {e}")
        return jsonify({"error": "Invalid date format", "status": "error"}), 400

    # Get the correct age category for the service
    age_category_id = get_adult_age_category_for_service(service_id)

    reservation_identifier = f"IE-{uuid.uuid4().hex[:8].upper()}"

    reservation_data = {
        "Identifier": reservation_identifier,
        "State": "Confirmed",
        "StartUtc": start_date,
        "EndUtc": end_date,
        "CustomerId": customer_id,
        "BookerId": customer_id,
        "PersonCounts": [{"AgeCategoryId": age_category_id, "Count": person_count}],
        "RequestedCategoryId": suite_id,
        "RateId": rate_id
    }

    # Add options/upsells if provided
    if options:
        # Transform options to the correct ProductOrders structure expected by Mews API
        reservation_data["ProductOrders"] = [
            {
                "ProductId": option["Id"],
                "Count": 1  # Default quantity of 1 for each selected product
            }
            for option in options
        ]

    payload = {
        "Client": "Intense Experience Booking",
        "ServiceId": service_id,
        "Reservations": [reservation_data]
    }

    result = make_mews_request("reservations/add", payload)

    if result and "Reservations" in result and result["Reservations"]:
        # Mews returns: {"Reservations": [{"Identifier": "...", "Reservation": {...}}]}
        reservation_wrapper = result["Reservations"][0]
        reservation = reservation_wrapper.get("Reservation", reservation_wrapper)
        reservation_id = reservation.get('Id')
        identifier = reservation_wrapper.get('Identifier')

        return jsonify({
            "reservation": reservation,
            "identifier": identifier,
            "status": "success"
        })

    logger.error("Failed to create reservation - no reservation in response")
    if result:
        logger.error(f"Response keys: {list(result.keys())}")
    return jsonify({"error": "Failed to create reservation", "status": "error"}), 500

@intense_experience_bp.route('/api/payment-request', methods=['POST'])
def payment_request():
    """Create a payment request for the reservation"""
    data = request.json

    # Extract data from the request (matching the format sent by PaymentComponent)
    payment_request_data = data.get('PaymentRequests', [{}])[0]
    customer_id = payment_request_data.get('AccountId')
    amount = payment_request_data.get('Amount', {}).get('Value')
    reservation_id = payment_request_data.get('ReservationId')
    description = payment_request_data.get('Description', 'Prepayment for reservation')
    expiration = payment_request_data.get('ExpirationUtc')

    if not all([customer_id, amount, reservation_id]):
        return jsonify({"error": "Missing required payment parameters", "status": "error"}), 400

    payload = {
        "Client": data.get('Client', 'Intense Experience 1.0.0'),
        "PaymentRequests": [{
            "AccountId": customer_id,
            "Amount": {
                "Currency": "EUR",
                "Value": float(amount)
            },
            "Type": "Payment",
            "Reason": "Prepayment",
            "ExpirationUtc": expiration,
            "Description": description,
            "ReservationId": reservation_id
        }]
    }

    result = make_mews_request("paymentRequests/add", payload)
    if result and "PaymentRequests" in result and result["PaymentRequests"]:
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to create payment request", "status": "error"}), 500


@intense_experience_bp.route('/api/payment-request/<payment_request_id>/status', methods=['GET'])
def get_payment_request_status(payment_request_id):
    """Get the status of a payment request"""
    payload = {
        "PaymentRequestIds": [payment_request_id]
    }

    result = make_mews_request("paymentRequests/getAll", payload)
    if result and "PaymentRequests" in result and result["PaymentRequests"]:
        payment_request = result["PaymentRequests"][0]
        return jsonify({
            "id": payment_request.get("Id"),
            "state": payment_request.get("State"),
            "status": payment_request.get("State"),  # For compatibility
            "amount": payment_request.get("Amount"),
            "description": payment_request.get("Description")
        })
    else:
        return jsonify({"error": "Payment request not found", "status": "error"}), 404


@intense_experience_bp.route('/intense_experience-api/booking-limits', methods=['GET'])
def get_booking_limits():
    """Get booking duration limits and available times"""
    return jsonify({
        'booking_limits': {
            'day_min_hours': DAY_MIN_HOURS,
            'day_max_hours': DAY_MAX_HOURS
        },
        'arrival_times': ARRIVAL_TIMES,
        'departure_times': DEPARTURE_TIMES,
        'night_check_in_hour': NIGHT_CHECK_IN_HOUR,
        'night_check_out_hour': NIGHT_CHECK_OUT_HOUR,
        'status': 'success'
    })

