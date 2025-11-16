from flask import Blueprint, jsonify, request
import os
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime, timedelta
import uuid

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
    
    # Print all the information received from the API
    logger.info("=" * 80)
    logger.info("SERVICES API RESPONSE - Full Data")
    logger.info("=" * 80)
    
    if result:
        logger.info(f"Response keys: {list(result.keys())}")
        logger.info(f"Total services received: {len(result.get('Services', []))}")
        logger.info("")
        
        if "Services" in result:
            for idx, service in enumerate(result["Services"], 1):
                logger.info(f"\n--- Service {idx} ---")
                logger.info(f"ID: {service.get('Id')}")
                logger.info(f"Name: {service.get('Name')}")
                logger.info(f"Type: {service.get('Type')}")
                logger.info(f"IsActive: {service.get('IsActive')}")
                logger.info(f"EnterpriseId: {service.get('EnterpriseId')}")
                logger.info(f"Names: {service.get('Names')}")
                logger.info(f"StartTime: {service.get('StartTime')}")
                logger.info(f"EndTime: {service.get('EndTime')}")
                logger.info(f"Options: {service.get('Options')}")
                logger.info(f"Promotions: {service.get('Promotions')}")
                logger.info(f"Ordering: {service.get('Ordering')}")
                logger.info(f"Data: {service.get('Data')}")
                logger.info(f"ExternalIdentifier: {service.get('ExternalIdentifier')}")
                logger.info(f"CreatedUtc: {service.get('CreatedUtc')}")
                logger.info(f"UpdatedUtc: {service.get('UpdatedUtc')}")
            
            logger.info("\n" + "=" * 80)
            
            # Filter to only show NUITEE and JOURNEE services
            services = [s for s in result["Services"] 
                       if s.get("Type") == "Reservable" and 
                       s.get("Id") in [DAY_SERVICE_ID, NIGHT_SERVICE_ID]]
            logger.info(f"Filtered reservable services (NUITEE and JOURNEE only): {len(services)}")
            logger.info("=" * 80)
            
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

@intense_experience_bp.route('/intense_experience-api/availability', methods=['POST'])
def check_availability():
    """Check availability for a date range with cleaning buffers"""
    data = request.json
    service_id = data.get('service_id')
    suite_id = data.get('suite_id')
    start_date = data.get('start_date')  # ISO format
    end_date = data.get('end_date')      # ISO format
    booking_type = data.get('booking_type')  # 'day' or 'night'

    logger.info("=" * 80)
    logger.info("AVAILABILITY CHECK - Starting")
    logger.info("=" * 80)
    logger.info(f"Service ID: {service_id}")
    logger.info(f"Suite ID: {suite_id}")
    logger.info(f"Start Date: {start_date}")
    logger.info(f"End Date: {end_date}")
    logger.info(f"Booking Type: {booking_type}")
    logger.info(f"Cleaning Buffer Hours: {CLEANING_BUFFER_HOURS}")

    if not all([service_id, start_date, end_date]):
        logger.error("Missing required parameters")
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400

    # Add cleaning buffers
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

    logger.info(f"Parsed Start DateTime: {start_dt}")
    logger.info(f"Parsed End DateTime: {end_dt}")

    if booking_type == 'night':
        # For nights: add buffer before and after
        buffered_start = (start_dt - timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        buffered_end = (end_dt + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        logger.info("Night booking - added buffer before and after")
    else:
        # For days: add buffer after
        buffered_start = start_dt.isoformat()
        buffered_end = (end_dt + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        logger.info("Day booking - added buffer after only")

    logger.info(f"Buffered Start: {buffered_start}")
    logger.info(f"Buffered End: {buffered_end}")

    payload = {
        "Client": "Intense Experience Booking",
        "StartUtc": buffered_start,
        "EndUtc": buffered_end
    }

    logger.info(f"Mews API Payload: {payload}")
    logger.info("Calling reservations/getAll API...")

    result = make_mews_request("reservations/getAll", payload)
    if result is None:
        logger.error("Failed to get reservations from Mews API")
        return jsonify({"error": "Failed to check availability", "status": "error"}), 500

    logger.info(f"API Response received. Keys: {list(result.keys()) if result else 'None'}")

    # Check if suite is available (no overlapping reservations)
    is_available = True
    conflicting_reservations = []

    if "Reservations" in result:
        total_reservations = len(result["Reservations"])
        logger.info(f"Found {total_reservations} reservations in the date range")

        for idx, reservation in enumerate(result["Reservations"], 1):
            res_id = reservation.get('Id', 'Unknown')
            res_start = reservation.get('StartUtc', 'Unknown')
            res_end = reservation.get('EndUtc', 'Unknown')
            res_state = reservation.get('State', 'Unknown')
            res_requested_category = reservation.get('RequestedCategoryId', 'Unknown')
            res_assigned_resource = reservation.get('AssignedResourceId', 'Unknown')
            res_assigned_space = reservation.get('AssignedSpaceId', 'Unknown')

            logger.info(f"\n--- Reservation {idx}/{total_reservations} ---")
            logger.info(f"ID: {res_id}")
            logger.info(f"Start: {res_start}")
            logger.info(f"End: {res_end}")
            logger.info(f"State: {res_state}")
            logger.info(f"RequestedCategoryId (Suite Type): {res_requested_category}")
            logger.info(f"AssignedResourceId (Physical Space): {res_assigned_resource}")
            logger.info(f"AssignedSpaceId: {res_assigned_space}")

            if suite_id:
                # Check specific suite availability
                # The suite_id parameter is a ResourceCategory ID (the suite type/category)
                # We check if this reservation uses that category by comparing RequestedCategoryId
                # 
                # Note: In Mews, a ResourceCategory (suite type) may have multiple physical 
                # Resources (rooms) assigned to it. This check tells us if ANY room of this
                # suite type is booked. The AssignedResourceId shows WHICH specific physical
                # room is being used.
                #
                # For more sophisticated availability (checking if ALL rooms of a type are booked),
                # we would need to fetch Resources and their category assignments.
                logger.info(f"Checking if reservation conflicts with suite category {suite_id}")
                
                category_match = res_requested_category == suite_id
                logger.info(f"RequestedCategoryId matches suite_id: {category_match}")

                if category_match:
                    logger.warning(f"CONFLICT FOUND: Reservation {res_id} conflicts with suite {suite_id}")
                    logger.warning(f"  Requested Category: {res_requested_category}")
                    logger.warning(f"  Assigned to physical resource/space: {res_assigned_resource}")
                    conflicting_reservations.append(reservation)
                    is_available = False
                else:
                    logger.info(f"No conflict with suite {suite_id}")
            else:
                # General availability check - any reservation blocks the time
                logger.warning("GENERAL CHECK: Any reservation blocks the time")
                conflicting_reservations.append(reservation)
                is_available = False

        logger.info(f"\nSUMMARY:")
        logger.info(f"Total reservations checked: {total_reservations}")
        logger.info(f"Conflicting reservations: {len(conflicting_reservations)}")
        logger.info(f"Final availability: {is_available}")

    else:
        logger.info("No 'Reservations' key in API response")
        if result:
            logger.info(f"Available keys: {list(result.keys())}")

    logger.info("=" * 80)
    logger.info("AVAILABILITY CHECK - Complete")
    logger.info("=" * 80)

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

    if not all([rate_id, start_date, end_date]):
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400

    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "Client": "Intense Experience Booking",
        "RateId": rate_id,
        "FirstTimeUnitStartUtc": start_date,
        "LastTimeUnitStartUtc": end_date
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

@intense_experience_bp.route('/intense_experience-api/create-customer', methods=['POST'])
def create_customer():
    """Create a new customer"""
    data = request.json
    
    logger.info("=" * 80)
    logger.info("CREATE CUSTOMER - Request received")
    logger.info("=" * 80)
    logger.info(f"Raw request data: {data}")
    
    # Support both snake_case and camelCase for frontend compatibility
    first_name = data.get('first_name') or data.get('firstName')
    last_name = data.get('last_name') or data.get('lastName')
    email = data.get('email')
    phone = data.get('phone')

    logger.info(f"Parsed fields:")
    logger.info(f"  First Name: {first_name}")
    logger.info(f"  Last Name: {last_name}")
    logger.info(f"  Email: {email}")
    logger.info(f"  Phone: {phone}")

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

    logger.info(f"Mews API Payload: {payload}")
    logger.info("Calling customers/add API...")

    result = make_mews_request("customers/add", payload)
    
    logger.info(f"Mews API Response: {result}")
    
    if result:
        # Mews API returns the customer object directly, not wrapped in an array
        if "Id" in result:
            customer = result
            logger.info(f"Customer created/updated successfully: {customer.get('Id')}")
            logger.info("=" * 80)
            return jsonify({"customer": customer, "status": "success"})
        # Some endpoints may return as array
        elif "Customers" in result and result["Customers"]:
            customer = result["Customers"][0]
            logger.info(f"Customer created/updated successfully: {customer.get('Id')}")
            logger.info("=" * 80)
            return jsonify({"customer": customer, "status": "success"})
    
    logger.error("Failed to create customer - no valid customer in response")
    logger.info("=" * 80)
    return jsonify({"error": "Failed to create customer", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/create-reservation', methods=['POST'])
def create_reservation():
    """Create a reservation"""
    data = request.json
    
    logger.info("=" * 80)
    logger.info("CREATE RESERVATION - Request received")
    logger.info("=" * 80)
    logger.info(f"Raw request data: {data}")
    
    service_id = data.get('service_id')
    customer_id = data.get('customer_id')
    suite_id = data.get('suite_id')
    rate_id = data.get('rate_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    person_count = data.get('person_count', 2)
    options = data.get('options', [])

    logger.info(f"Parsed reservation fields:")
    logger.info(f"  Service ID: {service_id}")
    logger.info(f"  Customer ID: {customer_id}")
    logger.info(f"  Suite ID: {suite_id}")
    logger.info(f"  Rate ID: {rate_id}")
    logger.info(f"  Start Date: {start_date}")
    logger.info(f"  End Date: {end_date}")
    logger.info(f"  Person Count: {person_count}")
    logger.info(f"  Options: {options}")

    if not all([service_id, customer_id, suite_id, rate_id, start_date, end_date]):
        logger.error("Missing required reservation parameters")
        logger.error(f"  service_id present: {bool(service_id)}")
        logger.error(f"  customer_id present: {bool(customer_id)}")
        logger.error(f"  suite_id present: {bool(suite_id)}")
        logger.error(f"  rate_id present: {bool(rate_id)}")
        logger.error(f"  start_date present: {bool(start_date)}")
        logger.error(f"  end_date present: {bool(end_date)}")
        return jsonify({"error": "Missing required reservation parameters", "status": "error"}), 400

    reservation_identifier = f"IE-{uuid.uuid4().hex[:8].upper()}"
    logger.info(f"Generated reservation identifier: {reservation_identifier}")

    reservation_data = {
        "Identifier": reservation_identifier,
        "State": "Confirmed",
        "StartUtc": start_date,
        "EndUtc": end_date,
        "CustomerId": customer_id,
        "BookerId": customer_id,
        "PersonCounts": [{"AgeCategoryId": "6cef9c83-4199-4b40-972b-b3850108b8a6", "Count": person_count}],
        "RequestedCategoryId": suite_id,
        "RateId": rate_id
    }

    # Add options/upsells if provided
    if options:
        reservation_data["ProductOrders"] = options
        logger.info(f"Added {len(options)} product orders to reservation")

    payload = {
        "Client": "Intense Experience Booking",
        "ServiceId": service_id,
        "Reservations": [reservation_data]
    }

    logger.info(f"Mews API Payload: {payload}")
    logger.info("Calling reservations/add API...")

    result = make_mews_request("reservations/add", payload)
    
    logger.info(f"Mews API Response: {result}")
    
    if result and "Reservations" in result and result["Reservations"]:
        # Mews returns: {"Reservations": [{"Identifier": "...", "Reservation": {...}}]}
        reservation_wrapper = result["Reservations"][0]
        reservation = reservation_wrapper.get("Reservation", reservation_wrapper)
        reservation_id = reservation.get('Id')
        identifier = reservation_wrapper.get('Identifier')
        
        logger.info(f"Reservation created successfully:")
        logger.info(f"  Identifier: {identifier}")
        logger.info(f"  Reservation ID: {reservation_id}")
        logger.info("=" * 80)
        
        return jsonify({
            "reservation": reservation,
            "identifier": identifier,
            "status": "success"
        })
    
    logger.error("Failed to create reservation - no reservation in response")
    if result:
        logger.error(f"Response keys: {list(result.keys())}")
    logger.info("=" * 80)
    return jsonify({"error": "Failed to create reservation", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/create-payment-request', methods=['POST'])
def create_payment_request():
    """Create a payment request for the reservation"""
    data = request.json
    customer_id = data.get('customer_id')
    amount = data.get('amount')
    reservation_id = data.get('reservation_id')
    description = data.get('description', 'Prepayment for reservation')

    if not all([customer_id, amount, reservation_id]):
        return jsonify({"error": "Missing required payment parameters", "status": "error"}), 400

    # Expiration in 24 hours
    expiration = (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'

    payload = {
        "Client": "Intense Experience Booking",
        "PaymentRequests": [{
            "AccountId": customer_id,
            "Amount": {
                "Currency": "EUR",
                "Value": float(amount)
            },
            "Type": "Payment",
            "Reason": "PaymentCardMissing",
            "ExpirationUtc": expiration,
            "Description": description,
            "ReservationId": reservation_id
        }]
    }

    result = make_mews_request("paymentRequests/add", payload)
    if result and "PaymentRequests" in result and result["PaymentRequests"]:
        payment_request = result["PaymentRequests"][0]
        payment_url = f"https://app.mews.com/navigator/payment-requests/detail/{payment_request['Id']}?ccy=EUR&language=fr-FR"
        return jsonify({
            "payment_request": payment_request,
            "payment_url": payment_url,
            "status": "success"
        })
    return jsonify({"error": "Failed to create payment request", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/test', methods=['GET'])
def dummy_route():
    """Dummy route for testing purposes"""
    return jsonify({'message': 'This is a dummy route', 'status': 'success'})



