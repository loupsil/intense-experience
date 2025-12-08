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
import unicodedata
from bulk_availability import (
    check_bulk_availability_journee, 
    check_bulk_availability_nuitee,
    get_resource_ids_for_suites,
    get_resource_blocks,
    check_resource_block_conflict
)

# Import all configuration from shared config file
from config import (
    MEWS_API_BASE_URL,
    MEWS_PAYMENT_BASE_URL,
    ENTERPRISE_ID,
    CLIENT_NAME,
    DAY_SERVICE_ID,
    NIGHT_SERVICE_ID,
    RATE_ID_NUITEE,
    RATE_ID_JOURNEE_SEMAINE,
    RATE_ID_JOURNEE_WEEKEND,
    AGE_CATEGORY_ADULT_DAY,
    AGE_CATEGORY_ADULT_NIGHT,
    CLEANING_BUFFER_HOURS,
    DAY_MIN_HOURS,
    DAY_MAX_HOURS,
    NIGHT_MAX_NIGHTS,
    DEFAULT_PERSON_COUNT,
    DEFAULT_CURRENCY,
    PAYMENT_EXPIRATION_DAYS,
    TIMEZONE,
    SPECIAL_MIN_DURATION_SUITES,
    SPECIAL_MIN_HOURS,
    ARRIVAL_TIMES,
    DEPARTURE_TIMES,
    NIGHT_CHECK_IN_HOUR,
    NIGHT_CHECK_OUT_HOUR,
    EARLY_CHECK_IN_HOUR,
    LATE_CHECK_OUT_HOUR,
    SUITE_ID_MAPPING,
    SUITE_ID_MAPPING_REVERSE
)

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

# Mews API configuration (base URL comes from config.py)
CLIENT_TOKEN = os.getenv('ClientToken')
ACCESS_TOKEN = os.getenv('AccessToken')

def make_mews_request(endpoint, payload):
    """Make a request to Mews API"""
    url = f"{MEWS_API_BASE_URL}/{endpoint}"
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
        # Helper to check category name (case- and accent-insensitive)
        def is_excluded_category(cat):
            raw_name = cat.get("Name") or cat.get("Names") or ""
            if isinstance(raw_name, dict):
                raw_name = raw_name.get("fr-FR") or raw_name.get("en-US") or next(iter(raw_name.values()), "")
            name_ascii = unicodedata.normalize("NFKD", str(raw_name)).encode("ascii", "ignore").decode("ascii").lower()
            return name_ascii in {"etage", "batiment"}
        
        # Filter to only show suites (not buildings/floors)
        # For journée: include Suite, Room, Other, and PrivateSpaces classified as Other,
        # but exclude "Etage" and "Batiment"
        def is_included_category(cat, is_day_service):
            cat_type = cat.get("Type")
            classification = cat.get("Classification")
            if cat_type in ["Suite", "Room", "Other"]:
                return True
            if is_day_service and cat_type == "PrivateSpaces" and classification == "Other":
                return True
            return False

        if service_id == DAY_SERVICE_ID:
            suites = [cat for cat in result["ResourceCategories"]
                     if cat.get("IsActive")
                     and is_included_category(cat, True)
                     and not is_excluded_category(cat)]
        else:
            suites = [cat for cat in result["ResourceCategories"]
                     if cat.get("IsActive")
                     and is_included_category(cat, False)]
        return jsonify({"suites": suites, "status": "success"})
    return jsonify({"error": "Failed to fetch suites", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/suite-id-mapping', methods=['GET'])
def get_suite_id_mapping():
    """Get suite ID mapping between day and night services"""
    return jsonify({
        "mapping": SUITE_ID_MAPPING,
        "reverse_mapping": SUITE_ID_MAPPING_REVERSE,
        "status": "success"
    })

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
    """Check availability for a date range with cleaning buffers - considers both services for cross-service suite matching"""
    data = request.json
    service_id = data.get('service_id')
    suite_id = data.get('suite_id')
    start_date = data.get('start_date')  # ISO format
    end_date = data.get('end_date')      # ISO format
    booking_type = data.get('booking_type')  # 'day' or 'night'

    if not all([service_id, start_date, end_date]):
        logger.error("Missing required parameters")
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400

    # Brussels timezone for consistent time comparisons
    brussels_tz = pytz.timezone(TIMEZONE)
    
    # Add cleaning buffers
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    # Convert to Brussels timezone
    start_dt_brussels = start_dt.astimezone(brussels_tz)
    end_dt_brussels = end_dt.astimezone(brussels_tz)

    if booking_type == 'night':
        # For nights: add buffer before and after
        buffered_start = (start_dt - timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        buffered_end = (end_dt + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
    else:
        # For days: add buffer after
        buffered_start = start_dt.isoformat()
        buffered_end = (end_dt + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()

    # Fetch reservations from both services to handle cross-service suite matching
    payload = {
        "Client": "Intense Experience Booking",
        "StartUtc": buffered_start,
        "EndUtc": buffered_end,
        "ServiceIds": [DAY_SERVICE_ID, NIGHT_SERVICE_ID]
    }

    result = make_mews_request("reservations/getAll", payload)
    if result is None:
        logger.error("Failed to get reservations from Mews API")
        return jsonify({"error": "Failed to check availability", "status": "error"}), 500

    # Check if suite is available (no overlapping reservations)
    is_available = True
    conflicting_reservations = []

    # Determine which suite IDs to check based on mapping (AND rule for day bookings)
    suite_ids_to_check = []
    if suite_id:
        suite_ids_to_check.append(suite_id)
        
        # For day bookings with a mapped suite, check BOTH day and night IDs (AND rule)
        if booking_type == 'day':
            # Check if this suite has a corresponding night suite ID
            night_suite_id = SUITE_ID_MAPPING.get(suite_id)
            if night_suite_id:
                suite_ids_to_check.append(night_suite_id)
                logger.info(f"Day booking for mapped suite - checking both IDs: {suite_id} and {night_suite_id}")

    if "Reservations" in result:
        for reservation in result["Reservations"]:
            res_requested_category = reservation.get('RequestedCategoryId')

            if suite_ids_to_check:
                # Check if reservation conflicts with any of the suite IDs we need to check
                if res_requested_category in suite_ids_to_check:
                    # Apply buffer to existing reservation times (1 hour before and 1 hour after)
                    res_start_utc = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                    res_end_utc = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
                    
                    # Convert to Brussels timezone for comparison
                    res_start = res_start_utc.astimezone(brussels_tz)
                    res_end = res_end_utc.astimezone(brussels_tz)
                    
                    # Apply buffer to existing reservations (1 hour before and 1 hour after)
                    res_start_buffered = res_start - timedelta(hours=CLEANING_BUFFER_HOURS)
                    res_end_buffered = res_end + timedelta(hours=CLEANING_BUFFER_HOURS)
                    
                    # Check for overlap: new booking WITHOUT buffer vs existing reservation WITH buffer
                    if not (end_dt_brussels <= res_start_buffered or start_dt_brussels >= res_end_buffered):
                        conflicting_reservations.append(reservation)
                        is_available = False
            else:
                # General availability check - any reservation blocks the time
                conflicting_reservations.append(reservation)
                is_available = False

    # Also check for resource block conflicts (if still available after reservation check)
    has_resource_block_conflict = False
    if is_available and suite_ids_to_check:
        # Fetch resource blocks with a wide range to catch multi-day blocks
        # Use 7 days before/after to ensure we catch any blocks that extend into our time slot
        blocks_query_start = (start_dt - timedelta(days=7)).isoformat()
        blocks_query_end = (end_dt + timedelta(days=7)).isoformat()
        resource_blocks = get_resource_blocks(make_mews_request, blocks_query_start, blocks_query_end)
        
        # Get all resource IDs for the suite categories we need to check (using static mapping)
        resource_ids_to_check = get_resource_ids_for_suites(suite_ids_to_check)
        
        # Check for resource block conflicts
        if check_resource_block_conflict(start_dt_brussels, end_dt_brussels, resource_ids_to_check, resource_blocks):
            is_available = False
            has_resource_block_conflict = True
            logger.info(f"Resource block conflict detected for suite {suite_id}")

    logger.info(f"Availability check completed - available: {is_available}, reservation conflicts: {len(conflicting_reservations)}, resource_block_conflict: {has_resource_block_conflict}")

    return jsonify({
        "available": is_available,
        "conflicting_reservations": conflicting_reservations,
        "has_resource_block_conflict": has_resource_block_conflict,
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
    if rate_id == RATE_ID_NUITEE:
        # Extract date part, subtract 1 day, and append 23:00:00.000Z for night bookings
        # This is how Mews API works - not sure why, but this -1 makes it work
        start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Subtract 1 day to get the correct pricing dates
        adjusted_start_date = start_date_obj - timedelta(days=1)
        adjusted_end_date = end_date_obj - timedelta(days=1)

        first_time_unit = adjusted_start_date.strftime('%Y-%m-%d') + 'T23:00:00.000Z'
        last_time_unit = adjusted_end_date.strftime('%Y-%m-%d') + 'T23:00:00.000Z'

        logger.info(f"PRICING: Nuitée detected - adjusting time units to 23:00:00.000Z with -1 day offset")
        logger.info(f"PRICING: Original start_date: {start_date}, adjusted: {first_time_unit} (yesterday)")
        logger.info(f"PRICING: Original end_date: {end_date}, adjusted: {last_time_unit} (yesterday)")
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

    def has_extra_name(product):
        names = [product.get("Name", "")]
        names.extend(product.get("Names", {}).values())
        return any(str(name).strip().lower() == "extra" for name in names if name is not None)

    payload = {
        "ServiceIds": service_ids,
        "EnterpriseIds": [ENTERPRISE_ID],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("products/getAll", payload)
    if result and "Products" in result:
        products = [
            product for product in result["Products"]
            if not has_extra_name(product)
        ]
        return jsonify({"products": products, "status": "success"})
    return jsonify({"error": "Failed to fetch products", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/resource-category-images', methods=['POST'])
def get_resource_category_images():
    """Get image assignments for resource categories"""
    data = request.json
    category_ids = data.get('category_ids', [])

    if not category_ids:
        return jsonify({"error": "No category IDs provided", "status": "error"}), 400

    payload = {
        "Client": "Intense Experience Booking",
        "ResourceCategoryIds": category_ids,
        "EnterpriseIds": [ENTERPRISE_ID],
        "Limitation": {"Count": 100}
    }

    result = make_mews_request("resourceCategoryImageAssignments/getAll", payload)
    if result and "ResourceCategoryImageAssignments" in result:
        return jsonify({"image_assignments": result["ResourceCategoryImageAssignments"], "status": "success"})
    return jsonify({"error": "Failed to fetch image assignments", "status": "error"}), 500

@intense_experience_bp.route('/intense_experience-api/images/get-urls', methods=['POST'])
def get_image_urls():
    """Get image URLs for given image IDs"""
    data = request.json
    image_ids = data.get('image_ids', [])

    if not image_ids:
        return jsonify({"error": "No image IDs provided", "status": "error"}), 400

    # Prepare images array for Mews API
    images = []
    for image_id in image_ids:
        images.append({
            "ImageId": image_id,
            "Width": 400,  # Reasonable size for product cards
            "Height": 300,
            "ResizeMode": "Fit"
        })

    payload = {
        "Client": "Intense Experience Booking",
        "Images": images
    }

    result = make_mews_request("images/getUrls", payload)
    if result and "ImageUrls" in result:
        return jsonify({"image_urls": result["ImageUrls"], "status": "success"})
    return jsonify({"error": "Failed to fetch image URLs", "status": "error"}), 500

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

    # Fallback to config values if API fails
    if service_id == DAY_SERVICE_ID:
        return AGE_CATEGORY_ADULT_DAY
    elif service_id == NIGHT_SERVICE_ID:
        return AGE_CATEGORY_ADULT_NIGHT

    return AGE_CATEGORY_ADULT_NIGHT  # Default fallback

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
    
    # Check if this is a nuitée booking and adjust times based on selected products
    if service_id == NIGHT_SERVICE_ID:
        has_arrivee_anticipee = False
        has_depart_tardif = False
        
        # Check if special products are selected
        for option in options:
            option_name = option.get('Name', {})
            # Handle both dict and string for Name
            if isinstance(option_name, dict):
                # Get French name or fallback to other languages
                name = option_name.get('fr-FR') or option_name.get('en-US') or ''
            else:
                name = str(option_name)
            
            if 'Arrivée anticipée' in name or 'arrivée anticipée' in name.lower():
                has_arrivee_anticipee = True
                logger.info(f"Arrivée anticipée product detected: {name}")
            elif 'Départ tardif' in name or 'départ tardif' in name.lower():
                has_depart_tardif = True
                logger.info(f"Départ tardif product detected: {name}")
        
        # Brussels timezone
        brussels_tz = pytz.timezone(TIMEZONE)
        
        # Adjust start_date if Arrivée anticipée is selected (change check-in to 18:00 Brussels time)
        if has_arrivee_anticipee:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            # Convert to Brussels timezone
            start_brussels = start_dt.astimezone(brussels_tz)
            # Set time to early check-in hour Brussels time
            adjusted_start_brussels = start_brussels.replace(hour=EARLY_CHECK_IN_HOUR, minute=0, second=0, microsecond=0)
            # Convert back to UTC
            adjusted_start_utc = adjusted_start_brussels.astimezone(timezone.utc)
            start_date = adjusted_start_utc.isoformat().replace('+00:00', 'Z')
            logger.info(f"Adjusted start time for Arrivée anticipée to 18:00 Brussels time (UTC: {start_date})")
        
        # Adjust end_date if Départ tardif is selected (change check-out to 12:00 Brussels time)
        if has_depart_tardif:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Convert to Brussels timezone
            end_brussels = end_dt.astimezone(brussels_tz)
            # Set time to late check-out hour Brussels time
            adjusted_end_brussels = end_brussels.replace(hour=LATE_CHECK_OUT_HOUR, minute=0, second=0, microsecond=0)
            # Convert back to UTC
            adjusted_end_utc = adjusted_end_brussels.astimezone(timezone.utc)
            end_date = adjusted_end_utc.isoformat().replace('+00:00', 'Z')
            logger.info(f"Adjusted end time for Départ tardif to 12:00 Brussels time (UTC: {end_date})")

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
    suite_id = request.args.get('suite_id')
    
    # Determine minimum hours based on suite
    min_hours = DAY_MIN_HOURS
    if suite_id and suite_id in SPECIAL_MIN_DURATION_SUITES:
        min_hours = SPECIAL_MIN_HOURS
    
    return jsonify({
        'booking_limits': {
            'day_min_hours': min_hours,
            'day_max_hours': DAY_MAX_HOURS
        },
        'arrival_times': ARRIVAL_TIMES,
        'departure_times': DEPARTURE_TIMES,
        'night_check_in_hour': NIGHT_CHECK_IN_HOUR,
        'night_check_out_hour': NIGHT_CHECK_OUT_HOUR,
        'special_min_duration_suites': SPECIAL_MIN_DURATION_SUITES,
        'special_min_hours': SPECIAL_MIN_HOURS,
        'status': 'success'
    })


@intense_experience_bp.route('/intense_experience-api/frontend-config', methods=['GET'])
def get_frontend_config():
    """Get all configuration values needed by the frontend"""
    return jsonify({
        # Service IDs
        'day_service_id': DAY_SERVICE_ID,
        'night_service_id': NIGHT_SERVICE_ID,
        
        # Rate IDs
        'rate_id_nuitee': RATE_ID_NUITEE,
        'rate_id_journee_semaine': RATE_ID_JOURNEE_SEMAINE,
        'rate_id_journee_weekend': RATE_ID_JOURNEE_WEEKEND,
        
        # Booking limits
        'day_min_hours': DAY_MIN_HOURS,
        'day_max_hours': DAY_MAX_HOURS,
        'night_max_nights': NIGHT_MAX_NIGHTS,
        'default_person_count': DEFAULT_PERSON_COUNT,
        
        # Time slots
        'arrival_times': ARRIVAL_TIMES,
        'departure_times': DEPARTURE_TIMES,
        
        # Check-in/Check-out hours
        'night_check_in_hour': NIGHT_CHECK_IN_HOUR,
        'night_check_out_hour': NIGHT_CHECK_OUT_HOUR,
        'early_check_in_hour': EARLY_CHECK_IN_HOUR,
        'late_check_out_hour': LATE_CHECK_OUT_HOUR,
        
        # Special suites
        'special_min_duration_suites': SPECIAL_MIN_DURATION_SUITES,
        'special_min_hours': SPECIAL_MIN_HOURS,
        
        # Payment configuration
        'default_currency': DEFAULT_CURRENCY,
        'payment_expiration_days': PAYMENT_EXPIRATION_DAYS,
        'payment_base_url': MEWS_PAYMENT_BASE_URL,
        
        # Client info
        'client_name': CLIENT_NAME,
        
        'status': 'success'
    })

@intense_experience_bp.route('/intense_experience-api/check-time-options-availability', methods=['POST'])
def check_time_options_availability():
    """Check if early check-in and late check-out options are available for a nuitée booking
    
    Early check-in (Arrivée anticipée) is only available if the corresponding journée suite 
    does not have a booking from 17:00 to 18:00 on the check-in date.
    
    Late check-out (Départ tardif) is only available if the corresponding journée suite 
    does not have a booking from 12:00 to 13:00 on the check-out date.
    """
    data = request.json
    suite_id = data.get('suite_id')  # The nuitée suite ID
    check_in_date = data.get('check_in_date')  # ISO format
    check_out_date = data.get('check_out_date')  # ISO format
    
    if not all([suite_id, check_in_date, check_out_date]):
        logger.error("Missing required parameters for time options availability check")
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400
    
    # Get the corresponding journée suite ID
    journee_suite_id = SUITE_ID_MAPPING_REVERSE.get(suite_id)
    
    if not journee_suite_id:
        logger.warning(f"No journée suite mapping found for nuitée suite {suite_id}")
        # If there's no mapping, assume options are available (fallback behavior)
        return jsonify({
            "early_checkin_available": True,
            "late_checkout_available": True,
            "status": "success"
        })
    
    logger.info(f"Checking time options availability for nuitée suite {suite_id} (journée equivalent: {journee_suite_id})")
    
    # Parse dates
    check_in_dt = datetime.fromisoformat(check_in_date.replace('Z', '+00:00'))
    check_out_dt = datetime.fromisoformat(check_out_date.replace('Z', '+00:00'))
    
    # Brussels timezone
    brussels_tz = pytz.timezone(TIMEZONE)
    
    # Convert to Brussels timezone for date extraction
    check_in_brussels = check_in_dt.astimezone(brussels_tz)
    check_out_brussels = check_out_dt.astimezone(brussels_tz)
    
    # Get the date parts
    check_in_date_only = check_in_brussels.date()
    check_out_date_only = check_out_brussels.date()
    
    # Create time slots to check in Brussels timezone
    # Early check-in: check 17:00-18:00 on check-in date
    early_checkin_start = brussels_tz.localize(datetime.combine(check_in_date_only, datetime.strptime('17:00', '%H:%M').time()))
    early_checkin_end = brussels_tz.localize(datetime.combine(check_in_date_only, datetime.strptime('18:00', '%H:%M').time()))
    
    # Late check-out: check 12:00-13:00 on check-out date
    late_checkout_start = brussels_tz.localize(datetime.combine(check_out_date_only, datetime.strptime('12:00', '%H:%M').time()))
    late_checkout_end = brussels_tz.localize(datetime.combine(check_out_date_only, datetime.strptime('13:00', '%H:%M').time()))
    
    # Query reservations for a range covering both dates
    # Add some buffer to ensure we capture all relevant reservations
    query_start = (early_checkin_start - timedelta(hours=1)).isoformat()
    query_end = (late_checkout_end + timedelta(hours=1)).isoformat()
    
    payload = {
        "Client": "Intense Experience Booking",
        "StartUtc": query_start,
        "EndUtc": query_end,
        "ServiceIds": [DAY_SERVICE_ID]  # Only check journée bookings
    }
    
    result = make_mews_request("reservations/getAll", payload)
    if result is None:
        logger.error("Failed to get reservations from Mews API")
        return jsonify({"error": "Failed to check availability", "status": "error"}), 500
    
    # Check for conflicts
    early_checkin_available = True
    late_checkout_available = True
    
    reservations = result.get("Reservations", [])
    logger.info(f"Found {len(reservations)} journée reservations to check")
    
    for reservation in reservations:
        # Only check reservations for the corresponding journée suite
        if reservation.get('RequestedCategoryId') != journee_suite_id:
            continue
        
        res_start_utc = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
        res_end_utc = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
        
        # Convert to Brussels timezone for comparison
        res_start = res_start_utc.astimezone(brussels_tz)
        res_end = res_end_utc.astimezone(brussels_tz)
        
        # Apply buffer to existing reservations (1 hour before and 1 hour after)
        res_start_buffered = res_start - timedelta(hours=CLEANING_BUFFER_HOURS)
        res_end_buffered = res_end + timedelta(hours=CLEANING_BUFFER_HOURS)
        
        # Check if reservation overlaps with early check-in slot (17:00-18:00 on check-in date)
        if not (res_end_buffered <= early_checkin_start or res_start_buffered >= early_checkin_end):
            early_checkin_available = False
            logger.info(f"Early check-in blocked by reservation from {res_start} to {res_end} (with buffer: {res_start_buffered} to {res_end_buffered})")
        
        # Check if reservation overlaps with late check-out slot (12:00-13:00 on check-out date)
        if not (res_end_buffered <= late_checkout_start or res_start_buffered >= late_checkout_end):
            late_checkout_available = False
            logger.info(f"Late check-out blocked by reservation from {res_start} to {res_end} (with buffer: {res_start_buffered} to {res_end_buffered})")
    
    # Also check for resource block conflicts (if still available after reservation check)
    if early_checkin_available or late_checkout_available:
        # Fetch resource blocks for the date range
        resource_blocks = get_resource_blocks(make_mews_request, query_start, query_end)
        
        # Get resource IDs for the journée suite (using static mapping)
        resource_ids_to_check = get_resource_ids_for_suites([journee_suite_id])
        
        if resource_ids_to_check:
            # Check early check-in slot for resource block conflicts
            if early_checkin_available and check_resource_block_conflict(early_checkin_start, early_checkin_end, resource_ids_to_check, resource_blocks):
                early_checkin_available = False
                logger.info(f"Early check-in blocked by resource block")
            
            # Check late check-out slot for resource block conflicts
            if late_checkout_available and check_resource_block_conflict(late_checkout_start, late_checkout_end, resource_ids_to_check, resource_blocks):
                late_checkout_available = False
                logger.info(f"Late check-out blocked by resource block")
    
    logger.info(f"Time options availability: early_checkin={early_checkin_available}, late_checkout={late_checkout_available}")
    
    return jsonify({
        "early_checkin_available": early_checkin_available,
        "late_checkout_available": late_checkout_available,
        "journee_suite_id": journee_suite_id,
        "status": "success"
    })

