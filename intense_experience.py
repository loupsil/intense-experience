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

@intense_experience_bp.route('/intense_experience-api/bulk-availability-journee', methods=['POST'])
def check_bulk_availability_journee():
    """Check availability for day bookings (journée) - shows date as unavailable if no valid time slots remain"""
    data = request.json
    service_id = data.get('service_id')
    dates = data.get('dates')  # List of ISO date strings
    suite_id = data.get('suite_id')  # Optional: filter by specific suite

    if not all([service_id, dates]) or len(dates) == 0:
        logger.error("Missing required parameters")
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400
    
    # Only apply bulk availability logic for DAY service
    if service_id != DAY_SERVICE_ID:
        logger.info(f"Bulk availability not supported for service {service_id}, only for JOURNEE ({DAY_SERVICE_ID})")
        return jsonify({"error": "Bulk availability only supported for day bookings", "status": "error"}), 400
    
    # Get all suite categories for this service
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "ServiceIds": [service_id],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    suites_result = make_mews_request("resourceCategories/getAll", payload)
    if not suites_result or "ResourceCategories" not in suites_result:
        logger.error("Failed to fetch suites")
        return jsonify({"error": "Failed to fetch suites", "status": "error"}), 500

    all_suites = [cat for cat in suites_result["ResourceCategories"]
                  if cat.get("Type") in ["Suite", "Room"] and cat.get("IsActive")]

    # If a specific suite is selected, filter to only that suite
    if suite_id:
        all_suites = [suite for suite in all_suites if suite["Id"] == suite_id]
        if not all_suites:
            logger.warning(f"Selected suite {suite_id} not found in available suites")
            return jsonify({"error": f"Selected suite {suite_id} not available", "status": "error"}), 400

    suite_ids = [suite["Id"] for suite in all_suites]
    
    logger.info(f"Found {len(suite_ids)} active suites: {suite_ids}")
    
    # Sort dates
    sorted_dates = sorted(set(dates))
    availability_results = {}
    
    # Process dates in chunks
    CHUNK_SIZE_DAYS = 4
    MAX_HOURS_PER_CHUNK = 96
    MAX_CONCURRENT_REQUESTS = 15
    
    def process_chunk(chunk_index, chunk_dates):
        """Process a single chunk of dates for day bookings"""
        chunk_start = datetime.fromisoformat(chunk_dates[0].replace('Z', '+00:00'))
        chunk_end = datetime.fromisoformat(chunk_dates[-1].replace('Z', '+00:00'))
        chunk_end = chunk_end + timedelta(days=1)
        
        chunk_hours = (chunk_end - chunk_start).total_seconds() / 3600
        if chunk_hours > MAX_HOURS_PER_CHUNK:
            chunk_end = chunk_start + timedelta(hours=MAX_HOURS_PER_CHUNK)
        
        # For day bookings: add buffer after
        buffered_start = chunk_start.isoformat()
        buffered_end = (chunk_end + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        
        logger.info(f"Processing chunk {chunk_index + 1}: {len(chunk_dates)} dates")
        logger.info(f"Date range: {chunk_start.date()} to {chunk_end.date()}")
        
        payload = {
            "Client": "Intense Experience Booking",
            "StartUtc": buffered_start,
            "EndUtc": buffered_end
        }
        
        result = make_mews_request("reservations/getAll", payload)
        if result is None:
            logger.error(f"Failed to get reservations for chunk starting {chunk_start.date()}")
            return {}
        
        chunk_availability = {}
        
        # Get reservations (empty list if no reservations found)
        reservations = result.get("Reservations", [])
        logger.info(f"Found {len(reservations)} reservations in chunk {chunk_index + 1}")
        
        # Check each date (process all dates, even if no reservations)
        for date_str in chunk_dates:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            
            # For each suite, check which time slots are available
            suite_availability = {}
            
            for suite_id in suite_ids:
                # Generate all possible time slot combinations
                available_slots = []
                
                for arrival_time in ARRIVAL_TIMES:
                    for departure_time in DEPARTURE_TIMES:
                        # Calculate duration
                        arr_hour = int(arrival_time.split(':')[0])
                        dep_hour = int(departure_time.split(':')[0])
                        duration = dep_hour - arr_hour
                        
                        # Check if duration is within limits
                        if duration < DAY_MIN_HOURS or duration > DAY_MAX_HOURS:
                            continue
                        
                        # Create datetime objects for this slot (timezone-aware to match reservations)
                        belgian_tz = pytz.timezone('Europe/Brussels')
                        slot_start = belgian_tz.localize(datetime.combine(date_obj, datetime.strptime(arrival_time, '%H:%M').time()))
                        slot_end = belgian_tz.localize(datetime.combine(date_obj, datetime.strptime(departure_time, '%H:%M').time()))
                        slot_end_buffered = slot_end + timedelta(hours=CLEANING_BUFFER_HOURS)
                        
                        # Check if this slot conflicts with any reservation
                        is_available = True
                        for reservation in reservations:
                            if reservation.get('RequestedCategoryId') != suite_id:
                                continue
                            
                            res_start = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                            res_end = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
                            
                            # Check for overlap (including buffer)
                            if not (slot_end_buffered <= res_start or slot_start >= res_end):
                                is_available = False
                                break
                        
                        if is_available:
                            available_slots.append({
                                'arrival': arrival_time,
                                'departure': departure_time,
                                'duration': duration
                            })
                
                suite_availability[suite_id] = available_slots
            
            # Date is available if at least one suite has at least one available slot
            has_available_slot = any(len(slots) > 0 for slots in suite_availability.values())
            total_available_slots = sum(len(slots) for slots in suite_availability.values())
            
            chunk_availability[date_str] = {
                "available": has_available_slot,
                "total_suites": len(suite_ids),
                "suite_availability": suite_availability,
                "total_available_slots": total_available_slots
            }
            
            # Log availability decision for every date
            logger.info(f"📅 Date {date_obj.strftime('%Y-%m-%d')} - {'✅ AVAILABLE' if has_available_slot else '❌ UNAVAILABLE'}")
            logger.info(f"   Total suites checked: {len(suite_ids)}")
            logger.info(f"   Total available time slots: {total_available_slots}")
            
            # Show suite-level breakdown
            for suite_id, slots in suite_availability.items():
                suite_short = suite_id[:8] if len(suite_id) > 8 else suite_id
                if len(slots) > 0:
                    logger.info(f"   ✓ Suite {suite_short}: {len(slots)} available slots")
                else:
                    logger.info(f"   ✗ Suite {suite_short}: 0 available slots (fully booked)")
            
            logger.info(f"   → Decision: {'Date marked AVAILABLE' if has_available_slot else 'Date marked UNAVAILABLE'}")
            logger.info("")  # Empty line for readability
            
            # Only provide detailed conflict analysis when date is NOT available
            if not has_available_slot:
                logger.warning(f"🔍 DETAILED CONFLICT ANALYSIS for {date_obj.strftime('%Y-%m-%d')}:")
                
                # Explain why each suite has no available slots
                for suite_id, slots in suite_availability.items():
                    if len(slots) == 0:
                        suite_short = suite_id[:8] if len(suite_id) > 8 else suite_id
                        logger.warning(f"   Suite {suite_short}: Analyzing blocked time slots...")
                        
                        # Check which time slots are blocked and why
                        blocked_slots = []
                        for arrival_time in ARRIVAL_TIMES:
                            for departure_time in DEPARTURE_TIMES:
                                arr_hour = int(arrival_time.split(':')[0])
                                dep_hour = int(departure_time.split(':')[0])
                                duration = dep_hour - arr_hour
                                
                                if duration < DAY_MIN_HOURS or duration > DAY_MAX_HOURS:
                                    continue
                                
                                slot_start = datetime.combine(date_obj, datetime.strptime(arrival_time, '%H:%M').time()).replace(tzinfo=timezone.utc)
                                slot_end = datetime.combine(date_obj, datetime.strptime(departure_time, '%H:%M').time()).replace(tzinfo=timezone.utc)
                                slot_end_buffered = slot_end + timedelta(hours=CLEANING_BUFFER_HOURS)
                                
                                # Find conflicting reservation
                                for reservation in reservations:
                                    if reservation.get('RequestedCategoryId') != suite_id:
                                        continue
                                    
                                    res_start = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                                    res_end = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
                                    
                                    if not (slot_end_buffered <= res_start or slot_start >= res_end):
                                        blocked_slots.append({
                                            'slot': f"{arrival_time}-{departure_time}",
                                            'res_id': reservation.get('Id', 'unknown')[:8],
                                            'res_time': f"{res_start.strftime('%Y-%m-%d %H:%M')}-{res_end.strftime('%H:%M')}"
                                        })
                                        break
                        
                        if blocked_slots:
                            logger.warning(f"      {len(blocked_slots)} time slots blocked by reservations:")
                            for blocked in blocked_slots[:3]:  # Show first 3 conflicts
                                logger.warning(f"        ✗ {blocked['slot']} blocked by reservation {blocked['res_id']} ({blocked['res_time']})")
                            if len(blocked_slots) > 3:
                                logger.warning(f"        ... and {len(blocked_slots) - 3} more blocked slots")
        
        return chunk_availability
    
    # Create chunks
    chunks = []
    for i in range(0, len(sorted_dates), CHUNK_SIZE_DAYS):
        chunk_dates = sorted_dates[i:i + CHUNK_SIZE_DAYS]
        if chunk_dates:
            chunks.append((i // CHUNK_SIZE_DAYS, chunk_dates))
    
    logger.info(f"Created {len(chunks)} chunks to process with up to {MAX_CONCURRENT_REQUESTS} concurrent requests")
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        future_to_chunk = {
            executor.submit(process_chunk, chunk_index, chunk_dates): (chunk_index, chunk_dates)
            for chunk_index, chunk_dates in chunks
        }
        
        for future in as_completed(future_to_chunk):
            chunk_index, chunk_dates = future_to_chunk[future]
            try:
                chunk_availability = future.result()
                availability_results.update(chunk_availability)
                logger.info(f"Completed processing chunk {chunk_index + 1}")
            except Exception as exc:
                logger.error(f"Chunk {chunk_index + 1} generated an exception: {exc}")
    
    logger.info("=" * 80)
    logger.info("BULK AVAILABILITY CHECK (JOURNEE) - Complete")
    logger.info("=" * 80)
    logger.info(f"Processed {len(availability_results)} dates")
    
    return jsonify({
        "availability": availability_results,
        "status": "success"
    })

@intense_experience_bp.route('/intense_experience-api/bulk-availability-nuitee', methods=['POST'])
def check_bulk_availability_nuitee():
    """Check availability for multiple dates displayed in calendar, chunked into 4-day periods"""
    data = request.json
    service_id = data.get('service_id')
    dates = data.get('dates')  # List of ISO date strings
    booking_type = data.get('booking_type', 'day')  # 'day' or 'night'
    suite_id = data.get('suite_id')  # Optional: filter by specific suite

    if not all([service_id, dates]) or len(dates) == 0:
        logger.error("Missing required parameters")
        return jsonify({"error": "Missing required parameters", "status": "error"}), 400

    # Only apply bulk availability logic for NUITEE service
    if service_id != NIGHT_SERVICE_ID:
        logger.info(f"Bulk availability not supported for service {service_id}, only for NUITEE ({NIGHT_SERVICE_ID})")
        return jsonify({"error": "Bulk availability only supported for night bookings", "status": "error"}), 400

    # Get all suite categories for this service
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "ServiceIds": [service_id],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    suites_result = make_mews_request("resourceCategories/getAll", payload)
    if not suites_result or "ResourceCategories" not in suites_result:
        logger.error("Failed to fetch suites")
        return jsonify({"error": "Failed to fetch suites", "status": "error"}), 500

    # Filter to only show suites (not buildings/floors)
    all_suites = [cat for cat in suites_result["ResourceCategories"]
                  if cat.get("Type") in ["Suite", "Room"] and cat.get("IsActive")]

    # If a specific suite is selected, filter to only that suite
    if suite_id:
        all_suites = [suite for suite in all_suites if suite["Id"] == suite_id]
        if not all_suites:
            logger.warning(f"Selected suite {suite_id} not found in available suites")
            return jsonify({"error": f"Selected suite {suite_id} not available", "status": "error"}), 400

    suite_ids = [suite["Id"] for suite in all_suites]

    logger.info(f"Found {len(suite_ids)} active suites: {suite_ids}")

    # Sort dates to ensure proper chunking
    sorted_dates = sorted(set(dates))  # Remove duplicates and sort
    availability_results = {}

    # Process dates in chunks with parallel execution to speed up fetching
    CHUNK_SIZE_DAYS = 4  # Mews API limitation: max 4 days per chunk
    MAX_HOURS_PER_CHUNK = 96
    MAX_CONCURRENT_REQUESTS = 15

    def process_chunk(chunk_index, chunk_dates):
        """Process a single chunk of dates - returns availability data for all dates in chunk"""
        chunk_start = datetime.fromisoformat(chunk_dates[0].replace('Z', '+00:00'))
        chunk_end = datetime.fromisoformat(chunk_dates[-1].replace('Z', '+00:00'))

        # Add one day to include the end date fully
        chunk_end = chunk_end + timedelta(days=1)

        # Calculate total hours for this chunk
        chunk_hours = (chunk_end - chunk_start).total_seconds() / 3600
        if chunk_hours > MAX_HOURS_PER_CHUNK:
            logger.warning(f"Chunk hours ({chunk_hours}) exceeds limit ({MAX_HOURS_PER_CHUNK}), truncating")
            chunk_end = chunk_start + timedelta(hours=MAX_HOURS_PER_CHUNK)

        # Add cleaning buffers based on booking type
        if booking_type == 'night':
            # For nights: add buffer before and after the entire chunk
            buffered_start = (chunk_start - timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
            buffered_end = (chunk_end + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()
        else:
            # For days: add buffer after
            buffered_start = chunk_start.isoformat()
            buffered_end = (chunk_end + timedelta(hours=CLEANING_BUFFER_HOURS)).isoformat()

        logger.info(f"Processing chunk {chunk_index + 1}: {len(chunk_dates)} dates")
        logger.info(f"Date range: {chunk_start.date()} to {chunk_end.date()}")
        logger.info(f"Buffered range: {buffered_start} to {buffered_end}")

        payload = {
            "Client": "Intense Experience Booking",
            "StartUtc": buffered_start,
            "EndUtc": buffered_end
        }

        result = make_mews_request("reservations/getAll", payload)
        if result is None:
            logger.error(f"Failed to get reservations for chunk starting {chunk_start.date()}")
            return {}

        chunk_availability = {}

        if "Reservations" in result:
            reservations = result["Reservations"]
            logger.info(f"Found {len(reservations)} reservations in chunk {chunk_index + 1}")

            # Group reservations by date with timezone-aware comparisons
            belgian_tz = pytz.timezone('Europe/Brussels')
            reservations_by_date = {}
            for date_str in chunk_dates:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                reservations_by_date[date_str] = []

                # Create date boundaries in Belgian timezone for accurate comparison
                date_start = belgian_tz.localize(datetime.combine(date_obj, datetime.min.time()))
                date_end = belgian_tz.localize(datetime.combine(date_obj + timedelta(days=1), datetime.min.time()))

                # Filter reservations that overlap with this specific date
                for reservation in reservations:
                    res_start = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                    res_end = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))

                    # Check if reservation overlaps with this date (timezone-aware)
                    # A reservation overlaps if it starts before the date ends AND ends after the date starts
                    if res_start < date_end and res_end > date_start:
                        reservations_by_date[date_str].append(reservation)

            # Check availability for each date in this chunk
            for date_str in chunk_dates:
                date_reservations = reservations_by_date[date_str]
                booked_suites = set()

                # Find which suites are booked on this date
                for reservation in date_reservations:
                    res_requested_category = reservation.get('RequestedCategoryId')
                    if res_requested_category in suite_ids:
                        booked_suites.add(res_requested_category)

                # A date is available if at least one suite is free
                available_suites = len(suite_ids) - len(booked_suites)
                is_available = available_suites > 0

                chunk_availability[date_str] = {
                    "available": is_available,
                    "total_suites": len(suite_ids),
                    "booked_suites": len(booked_suites),
                    "available_suites": available_suites,
                    "booked_suite_ids": list(booked_suites)
                }

                logger.info(f"Date {date_str}: {available_suites}/{len(suite_ids)} suites available - {'AVAILABLE' if is_available else 'FULLY BOOKED'}")

        return chunk_availability

    # Create chunks
    chunks = []
    for i in range(0, len(sorted_dates), CHUNK_SIZE_DAYS):
        chunk_dates = sorted_dates[i:i + CHUNK_SIZE_DAYS]
        if chunk_dates:
            chunks.append((i // CHUNK_SIZE_DAYS, chunk_dates))

    logger.info(f"Created {len(chunks)} chunks to process with up to {MAX_CONCURRENT_REQUESTS} concurrent requests")

    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        # Submit all chunk processing tasks
        future_to_chunk = {
            executor.submit(process_chunk, chunk_index, chunk_dates): (chunk_index, chunk_dates)
            for chunk_index, chunk_dates in chunks
        }

        # Process results as they complete
        for future in as_completed(future_to_chunk):
            chunk_index, chunk_dates = future_to_chunk[future]
            try:
                chunk_availability = future.result()
                availability_results.update(chunk_availability)
                logger.info(f"Completed processing chunk {chunk_index + 1}")
            except Exception as exc:
                logger.error(f"Chunk {chunk_index + 1} generated an exception: {exc}")
                # Continue with other chunks even if one fails

    logger.info("=" * 80)
    logger.info("BULK AVAILABILITY CHECK - Complete")
    logger.info("=" * 80)
    logger.info(f"Processed {len(availability_results)} dates")

    return jsonify({
        "availability": availability_results,
        "status": "success"
    })


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
    logger.info(f"Using age category ID: {age_category_id} for service {service_id}")

    reservation_identifier = f"IE-{uuid.uuid4().hex[:8].upper()}"
    logger.info(f"Generated reservation identifier: {reservation_identifier}")

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
        'status': 'success'
    })

