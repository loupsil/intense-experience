import logging
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logger = logging.getLogger(__name__)

# Mews API configuration
ENTERPRISE_ID = "c390a691-e9a0-4aa0-860c-b3850108ab4c"

# Service IDs
DAY_SERVICE_ID = "86fcc6a7-75ce-457a-a425-b3850108b6bf"  # JOURNEE
NIGHT_SERVICE_ID = "7ba0b732-93cc-477a-861d-b3850108b730"  # NUITEE

# Default cleaning buffer in hours
CLEANING_BUFFER_HOURS = 1

# Booking duration limits for journee bookings
DAY_MIN_HOURS = 3
DAY_MAX_HOURS = 6

# Special minimum duration suites (Chambres with 2-hour minimum instead of 3)
SPECIAL_MIN_DURATION_SUITES = [
    "f5539e51-9db0-4082-b87e-b3850108c66f",  # Chambre EUPHORYA
    "78a614b1-199d-4608-ab89-b3850108c66f",  # Chambre IGNIS
    "67ece5a2-65e2-43c5-9079-b3850108c66f",  # Chambre KAIROS
    "1113bcbe-ad5f-49c7-8dc0-b3850108c66f",  # Chambre AETHER
]
SPECIAL_MIN_HOURS = 2

# Arrival and departure times for journee bookings
ARRIVAL_TIMES = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
DEPARTURE_TIMES = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']

# Default check-in and check-out hours for nuitée bookings
NIGHT_CHECK_IN_HOUR = 19  # 19:00 (7:00 PM)
NIGHT_CHECK_OUT_HOUR = 10  # 10:00 (10:00 AM)

def check_bulk_availability_journee(make_mews_request_func, data):
    """Check availability for day bookings (journée) - considers reservations from both day and night services - shows date as unavailable if no valid time slots remain"""
    service_id = data.get('service_id')
    dates = data.get('dates')  # List of ISO date strings
    suite_id = data.get('suite_id')  # Optional: filter by specific suite

    if not all([service_id, dates]) or len(dates) == 0:
        logger.error("Missing required parameters")
        return {"error": "Missing required parameters", "status": "error"}, 400

    # Get all suite categories for both day and night services
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "ServiceIds": [DAY_SERVICE_ID, NIGHT_SERVICE_ID],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    suites_result = make_mews_request_func("resourceCategories/getAll", payload)
    if not suites_result or "ResourceCategories" not in suites_result:
        logger.error("Failed to fetch suites")
        return {"error": "Failed to fetch suites", "status": "error"}, 500

    all_suites = [cat for cat in suites_result["ResourceCategories"]
                  if cat.get("Type") in ["Suite", "Room"] and cat.get("IsActive")]

    # If a specific suite is selected, filter to only that suite
    if suite_id:
        all_suites = [suite for suite in all_suites if suite["Id"] == suite_id]
        if not all_suites:
            logger.warning(f"Selected suite {suite_id} not found in available suites")
            return {"error": f"Selected suite {suite_id} not available", "status": "error"}, 400

    suite_ids = [suite["Id"] for suite in all_suites]

    logger.info(f"Found {len(suite_ids)} active suites")

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

        payload = {
            "Client": "Intense Experience Booking",
            "StartUtc": buffered_start,
            "EndUtc": buffered_end,
            "ServiceIds": [DAY_SERVICE_ID, NIGHT_SERVICE_ID]
        }

        result = make_mews_request_func("reservations/getAll", payload)
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
                # Determine minimum hours based on suite
                min_hours = SPECIAL_MIN_HOURS if suite_id in SPECIAL_MIN_DURATION_SUITES else DAY_MIN_HOURS
                
                # Generate all possible time slot combinations
                available_slots = []

                for arrival_time in ARRIVAL_TIMES:
                    for departure_time in DEPARTURE_TIMES:
                        # Calculate duration
                        arr_hour = int(arrival_time.split(':')[0])
                        dep_hour = int(departure_time.split(':')[0])
                        duration = dep_hour - arr_hour

                        # Check if duration meets minimum and maximum requirements
                        if duration < min_hours or duration > DAY_MAX_HOURS:
                            continue

                        # Create datetime objects for this slot (timezone-aware to match reservations)
                        belgian_tz = pytz.timezone('Europe/Brussels')
                        slot_start = belgian_tz.localize(datetime.combine(date_obj, datetime.strptime(arrival_time, '%H:%M').time()))
                        slot_end = belgian_tz.localize(datetime.combine(date_obj, datetime.strptime(departure_time, '%H:%M').time()))

                        # Check if this slot conflicts with any reservation
                        is_available = True
                        for reservation in reservations:
                            if reservation.get('RequestedCategoryId') != suite_id:
                                continue

                            res_start_utc = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                            res_end_utc = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
                            
                            # Convert to Brussels timezone for comparison
                            res_start = res_start_utc.astimezone(belgian_tz)
                            res_end = res_end_utc.astimezone(belgian_tz)
                            
                            # Apply buffer to existing reservations (1 hour before and 1 hour after)
                            res_start_buffered = res_start - timedelta(hours=CLEANING_BUFFER_HOURS)
                            res_end_buffered = res_end + timedelta(hours=CLEANING_BUFFER_HOURS)

                            # Check for overlap (new slot WITHOUT buffer vs existing reservation WITH buffer)
                            if not (slot_end <= res_start_buffered or slot_start >= res_end_buffered):
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

        return chunk_availability

    # Create chunks
    chunks = []
    for i in range(0, len(sorted_dates), CHUNK_SIZE_DAYS):
        chunk_dates = sorted_dates[i:i + CHUNK_SIZE_DAYS]
        if chunk_dates:
            chunks.append((i // CHUNK_SIZE_DAYS, chunk_dates))

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
            except Exception as exc:
                logger.error(f"Chunk {chunk_index + 1} generated an exception: {exc}")

    logger.info(f"Bulk availability check (journée) completed - processed {len(availability_results)} dates")

    return {
        "availability": availability_results,
        "status": "success"
    }


def check_bulk_availability_nuitee(make_mews_request_func, data):
    """Check availability for multiple dates displayed in calendar, chunked into 4-day periods"""
    service_id = data.get('service_id')
    dates = data.get('dates')  # List of ISO date strings
    booking_type = data.get('booking_type', 'day')  # 'day' or 'night'
    suite_id = data.get('suite_id')  # Optional: filter by specific suite

    if not all([service_id, dates]) or len(dates) == 0:
        logger.error("Missing required parameters")
        return {"error": "Missing required parameters", "status": "error"}, 400

    # Only apply bulk availability logic for NUITEE service
    if service_id != NIGHT_SERVICE_ID:
        logger.info(f"Bulk availability not supported for service {service_id}, only for NUITEE ({NIGHT_SERVICE_ID})")
        return {"error": "Bulk availability only supported for night bookings", "status": "error"}, 400

    # Get all suite categories for this service
    payload = {
        "EnterpriseIds": [ENTERPRISE_ID],
        "ServiceIds": [service_id],
        "IncludeDefault": False,
        "Limitation": {"Count": 100}
    }

    suites_result = make_mews_request_func("resourceCategories/getAll", payload)
    if not suites_result or "ResourceCategories" not in suites_result:
        logger.error("Failed to fetch suites")
        return {"error": "Failed to fetch suites", "status": "error"}, 500

    # Filter to only show suites (not buildings/floors)
    all_suites = [cat for cat in suites_result["ResourceCategories"]
                  if cat.get("Type") in ["Suite", "Room"] and cat.get("IsActive")]

    # If a specific suite is selected, filter to only that suite
    if suite_id:
        all_suites = [suite for suite in all_suites if suite["Id"] == suite_id]
        if not all_suites:
            logger.warning(f"Selected suite {suite_id} not found in available suites")
            return {"error": f"Selected suite {suite_id} not available", "status": "error"}, 400

    suite_ids = [suite["Id"] for suite in all_suites]

    logger.info(f"Found {len(suite_ids)} active suites")

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

        payload = {
            "Client": "Intense Experience Booking",
            "StartUtc": buffered_start,
            "EndUtc": buffered_end
        }

        result = make_mews_request_func("reservations/getAll", payload)
        if result is None:
            logger.error(f"Failed to get reservations for chunk starting {chunk_start.date()}")
            return {}

        chunk_availability = {}

        if "Reservations" in result:
            reservations = result["Reservations"]

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
                    res_start_utc = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                    res_end_utc = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
                    
                    # Convert to Brussels timezone for comparison with date boundaries
                    res_start = res_start_utc.astimezone(belgian_tz)
                    res_end = res_end_utc.astimezone(belgian_tz)

                    # Check if reservation overlaps with this date (timezone-aware)
                    # A reservation overlaps if it starts before the date ends AND ends after the date starts
                    if res_start <= date_end and res_end >= date_start:
                        reservations_by_date[date_str].append(reservation)

            def reservation_to_local_range(reservation):
                """Convert reservation start/end to Brussels timezone."""
                start_raw = reservation.get('StartUtc')
                end_raw = reservation.get('EndUtc')
                if not start_raw or not end_raw:
                    return None, None

                res_start = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
                res_end = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))

                return res_start.astimezone(belgian_tz), res_end.astimezone(belgian_tz)

            def is_slot_available_for_suite(slot_start, slot_end, suite_reservations):
                """Check if a suite has no reservation conflicts for the provided slot."""
                for reservation in suite_reservations:
                    res_start = reservation["start"]
                    res_end = reservation["end"]
                    
                    # Apply buffer to existing reservations (1 hour before and 1 hour after)
                    res_start_buffered = res_start - timedelta(hours=CLEANING_BUFFER_HOURS)
                    res_end_buffered = res_end + timedelta(hours=CLEANING_BUFFER_HOURS)
                    
                    # Check for overlap (new slot WITHOUT buffer vs existing reservation WITH buffer)
                    if not (slot_end <= res_start_buffered or slot_start >= res_end_buffered):
                        return False
                return True

            # Check availability for each date in this chunk with morning/night granularity
            for date_str in chunk_dates:
                date_reservations = reservations_by_date[date_str]

                # Map reservations per suite with localized times for accurate comparisons
                suite_reservations_map = {suite_id: [] for suite_id in suite_ids}
                for reservation in date_reservations:
                    res_suite_id = reservation.get('RequestedCategoryId')
                    if res_suite_id not in suite_reservations_map:
                        continue
                    res_start_local, res_end_local = reservation_to_local_range(reservation)
                    if not res_start_local or not res_end_local:
                        continue
                    suite_reservations_map[res_suite_id].append({
                        "start": res_start_local,
                        "end": res_end_local
                    })

                booked_suites = {suite_id for suite_id, res in suite_reservations_map.items() if res}

                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                morning_start = belgian_tz.localize(datetime.combine(date_obj, datetime.min.time()))
                morning_end = morning_start + timedelta(hours=NIGHT_CHECK_OUT_HOUR)
                night_start = morning_start + timedelta(hours=NIGHT_CHECK_IN_HOUR)
                next_day_start = belgian_tz.localize(datetime.combine(date_obj + timedelta(days=1), datetime.min.time()))
                night_end = next_day_start + timedelta(hours=NIGHT_CHECK_OUT_HOUR)

                morning_available_suite_ids = set()
                night_available_suite_ids = set()

                for suite_id, suite_reservations in suite_reservations_map.items():
                    if is_slot_available_for_suite(morning_start, morning_end, suite_reservations):
                        morning_available_suite_ids.add(suite_id)
                    if is_slot_available_for_suite(night_start, night_end, suite_reservations):
                        night_available_suite_ids.add(suite_id)

                available_morning = len(morning_available_suite_ids) > 0
                available_night = len(night_available_suite_ids) > 0
                # For backward compatibility, keep "available" aligned with night availability (check-in)
                chunk_availability[date_str] = {
                    "available": available_night,
                    "available_morning": available_morning,
                    "available_night": available_night,
                    "total_suites": len(suite_ids),
                    "booked_suites": len(booked_suites),
                    "available_suites": len(night_available_suite_ids),
                    "booked_suite_ids": list(booked_suites)
                }

        return chunk_availability

    # Create chunks
    chunks = []
    for i in range(0, len(sorted_dates), CHUNK_SIZE_DAYS):
        chunk_dates = sorted_dates[i:i + CHUNK_SIZE_DAYS]
        if chunk_dates:
            chunks.append((i // CHUNK_SIZE_DAYS, chunk_dates))

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
            except Exception as exc:
                logger.error(f"Chunk {chunk_index + 1} generated an exception: {exc}")

    logger.info(f"Bulk availability check (nuitée) completed - processed {len(availability_results)} dates")

    return {
        "availability": availability_results,
        "status": "success"
    }
