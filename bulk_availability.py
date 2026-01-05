import logging
import unicodedata
from datetime import datetime, timedelta, time
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all configuration from shared config file
from config import (
    ENTERPRISE_ID,
    DAY_SERVICE_ID,
    NIGHT_SERVICE_ID,
    CLEANING_BUFFER_HOURS,
    DAY_MIN_HOURS,
    DAY_MAX_HOURS,
    TIMEZONE,
    SPECIAL_MIN_DURATION_SUITES,
    SPECIAL_MIN_HOURS,
    ARRIVAL_TIMES,
    DEPARTURE_TIMES,
    NIGHT_CHECK_IN_HOUR,
    NIGHT_CHECK_OUT_HOUR, 
    SUITE_ID_MAPPING,
    SUITE_ID_MAPPING_REVERSE,
    SUITE_TO_RESOURCE_ID,
    BUILDING_RESOURCE_ID
)

# Configure logging
logger = logging.getLogger(__name__)
# Reuse timezone object in hot paths
BELGIAN_TZ = pytz.timezone(TIMEZONE)

# Global cache for precomputed time slots per date - avoids repeated datetime creation
GLOBAL_SLOTS = {}

# Pre-generate valid slots per minimum-hour rule (module-level cache)
_VALID_SLOTS_BY_MIN_HOURS = {}

def _get_valid_slots(min_hours):
    """Get valid arrival/departure slot combinations for given minimum hours."""
    if min_hours in _VALID_SLOTS_BY_MIN_HOURS:
        return _VALID_SLOTS_BY_MIN_HOURS[min_hours]

    slots = []
    for arrival_time in ARRIVAL_TIMES:
        arr_hour = int(arrival_time.split(':')[0])
        for departure_time in DEPARTURE_TIMES:
            dep_hour = int(departure_time.split(':')[0])
            duration = dep_hour - arr_hour
            if duration < min_hours or duration > DAY_MAX_HOURS:
                continue
            slots.append((arrival_time, departure_time, duration))

    _VALID_SLOTS_BY_MIN_HOURS[min_hours] = slots
    return slots


def get_precomputed_slots(date_obj):
    """
    Get precomputed time slots for a given date from global cache.
    Creates and caches slots if not already present.
    
    Args:
        date_obj: date object for the day to compute slots for
        
    Returns:
        dict: {min_hours: [(slot_start, slot_end, arrival_str, departure_str, duration), ...]}
    """
    if date_obj in GLOBAL_SLOTS:
        return GLOBAL_SLOTS[date_obj]

    result = {}
    for min_h in (DAY_MIN_HOURS, SPECIAL_MIN_HOURS):
        result[min_h] = [
            (
                BELGIAN_TZ.localize(datetime.combine(date_obj, time.fromisoformat(arr))),
                BELGIAN_TZ.localize(datetime.combine(date_obj, time.fromisoformat(dep))),
                arr,
                dep,
                dur
            )
            for arr, dep, dur in _get_valid_slots(min_h)
        ]
    GLOBAL_SLOTS[date_obj] = result
    return result


def get_resource_ids_for_suites(suite_ids):
    """
    Get the physical resource IDs for the given suite category IDs.
    Uses the static SUITE_TO_RESOURCE_ID mapping from config.
    
    Args:
        suite_ids: list of suite category IDs
    
    Returns:
        list: List of physical resource IDs
    """
    resource_ids = []
    for suite_id in suite_ids:
        resource_id = SUITE_TO_RESOURCE_ID.get(suite_id)
        if resource_id and resource_id not in resource_ids:
            resource_ids.append(resource_id)
    return resource_ids


def get_resource_blocks(make_mews_request_func, start_utc, end_utc):
    """
    Fetch resource blocks for a given time range.
    
    Returns:
        list: List of resource block objects with StartUtc, EndUtc, AssignedResourceId
    """
    payload = {
        "Client": "Intense Experience Booking",
        "CollidingUtc": {
            "StartUtc": start_utc,
            "EndUtc": end_utc
        },
        "Limitation": {"Count": 1000}
    }
    
    result = make_mews_request_func("resourceBlocks/getAll", payload)
    if not result or "ResourceBlocks" not in result:
        logger.warning("Failed to fetch resource blocks or no blocks found")
        return []
    
    # Filter to only active blocks
    active_blocks = [block for block in result["ResourceBlocks"] if block.get("IsActive")]
    logger.info(f"Found {len(active_blocks)} active resource blocks in range {start_utc} to {end_utc}")
    return active_blocks


def check_resource_block_conflict(slot_start, slot_end, resource_ids, resource_blocks, timezone_str=TIMEZONE):
    """
    Check if a time slot conflicts with any resource block for the given resources.
    Also checks for building-level blocks that affect ALL suites.
    
    Args:
        slot_start: datetime object (timezone-aware) for slot start
        slot_end: datetime object (timezone-aware) for slot end
        resource_ids: list of resource IDs to check against
        resource_blocks: list of resource block objects
        timezone_str: timezone string for conversions
    
    Returns:
        bool: True if there's a conflict, False otherwise
    """
    if not resource_blocks:
        return False
    
    belgian_tz = pytz.timezone(timezone_str)
    
    for block in resource_blocks:
        block_resource_id = block.get("AssignedResourceId")
        
        # Check if this is a building-level block (affects ALL suites)
        is_building_block = BUILDING_RESOURCE_ID and block_resource_id == BUILDING_RESOURCE_ID
        
        # Skip blocks not assigned to our resources (unless it's a building block)
        if not is_building_block and (not resource_ids or block_resource_id not in resource_ids):
            continue
        
        # Parse block times
        block_start_utc = datetime.fromisoformat(block.get("StartUtc", "").replace("Z", "+00:00"))
        block_end_utc = datetime.fromisoformat(block.get("EndUtc", "").replace("Z", "+00:00"))
        
        # Convert to local timezone for comparison
        block_start = block_start_utc.astimezone(belgian_tz)
        block_end = block_end_utc.astimezone(belgian_tz)
        
        # Check for overlap (slot vs block - no buffer applied to blocks)
        # Overlap exists if: NOT (slot_end <= block_start OR slot_start >= block_end)
        if not (slot_end <= block_start or slot_start >= block_end):
            return True
    
    return False

def check_bulk_availability_journee(make_mews_request_func, data):
    """Check availability for day bookings (journée) - considers reservations from both day and night services - shows date as unavailable if no valid time slots remain"""
    service_id = data.get('service_id')
    dates = data.get('dates')  # List of ISO date strings
    selected_suite_id = data.get('suite_id')  # Optional: used to determine minimum duration and for early-exit optimization

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

    # For journée: include Suite, Room, and Other types
    # But exclude resources named "Etage" or "Batiment"
    def is_excluded_category(cat):
        """Return True if category name matches Etage/Batiment (case- and accent-insensitive)."""
        raw_name = cat.get("Name") or cat.get("Names") or ""
        if isinstance(raw_name, dict):
            raw_name = raw_name.get("fr-FR") or raw_name.get("en-US") or next(iter(raw_name.values()), "")
        name_ascii = unicodedata.normalize("NFKD", str(raw_name)).encode("ascii", "ignore").decode("ascii").lower()
        return name_ascii in {"etage", "batiment"}

    def is_included_category(cat):
        """Include Suites, Rooms, Other, and PrivateSpaces classified as Other."""
        cat_type = cat.get("Type")
        classification = cat.get("Classification")
        if cat_type in ["Suite", "Room", "Other"]:
            return True
        if cat_type == "PrivateSpaces" and classification == "Other":
            return True
        return False

    all_suites = [cat for cat in suites_result["ResourceCategories"]
                  if cat.get("IsActive")
                  and is_included_category(cat)
                  and not is_excluded_category(cat)]

    suite_ids = [suite["Id"] for suite in all_suites]
    
    # Optimization: reorder suite_ids to check selected suite first when specified
    # Also get the night mapping for the selected suite if it exists
    selected_night_suite_id = SUITE_ID_MAPPING.get(selected_suite_id) if selected_suite_id else None
    
    if selected_suite_id and selected_suite_id in suite_ids:
        # Move selected suite to front, followed by its night mapping if exists
        suite_ids = [sid for sid in suite_ids if sid != selected_suite_id and sid != selected_night_suite_id]
        if selected_night_suite_id and selected_night_suite_id in [s["Id"] for s in all_suites]:
            suite_ids = [selected_suite_id, selected_night_suite_id] + suite_ids
        else:
            suite_ids = [selected_suite_id] + suite_ids
    
    # Cache resource IDs per suite to avoid recomputing in the hot loop
    resource_ids_cache = {
        suite_id: get_resource_ids_for_suites([suite_id])
        for suite_id in suite_ids
    }

    logger.info(f"Found {len(suite_ids)} active suites (selected_suite_id: {selected_suite_id})")

    # Sort dates
    sorted_dates = sorted(set(dates))
    availability_results = {}

    # Fetch resource blocks for the entire date range
    # Use a wide buffer (2 days before/after) to catch multi-day blocks that might extend into our range
    if sorted_dates:
        range_start = datetime.fromisoformat(sorted_dates[0].replace('Z', '+00:00'))
        range_end = datetime.fromisoformat(sorted_dates[-1].replace('Z', '+00:00')) + timedelta(days=1)
        # Add generous buffer to catch multi-day blocks that start before or end after our range
        blocks_start = (range_start - timedelta(days=2)).isoformat()
        blocks_end = (range_end + timedelta(days=2)).isoformat()
        resource_blocks = get_resource_blocks(make_mews_request_func, blocks_start, blocks_end)
    else:
        resource_blocks = []

    # Process dates in chunks
    CHUNK_SIZE_DAYS = 4
    MAX_HOURS_PER_CHUNK = 96
    MAX_CONCURRENT_REQUESTS = 20

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
        # Group reservations by suite once per chunk to avoid scanning all reservations per slot
        reservations_by_suite = {}
        for reservation in reservations:
            suite_id = reservation.get('RequestedCategoryId')
            if not suite_id:
                continue
            start_raw = reservation.get('StartUtc', '')
            end_raw = reservation.get('EndUtc', '')
            if not start_raw or not end_raw:
                continue
            res_start_utc = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            res_end_utc = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))
            reservations_by_suite.setdefault(suite_id, []).append({
                "start": res_start_utc.astimezone(BELGIAN_TZ),
                "end": res_end_utc.astimezone(BELGIAN_TZ),
            })

        # Check each date (process all dates, even if no reservations)
        for date_str in chunk_dates:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()

            # Get precomputed time slots from global cache (huge speedup - datetime creation removed from inner loops)
            precomputed_slots = get_precomputed_slots(date_obj)

            # Pre-filter reservations by date: only keep reservations that could affect this date
            # A reservation affects this date if its buffered time overlaps with the day's time range
            day_start = BELGIAN_TZ.localize(datetime.combine(date_obj, datetime.min.time()))
            day_end = BELGIAN_TZ.localize(datetime.combine(date_obj, datetime.max.time()))
            
            reservations_by_suite_for_date = {}
            for suite_id, suite_reservations in reservations_by_suite.items():
                filtered_reservations = []
                for res in suite_reservations:
                    # Pre-compute buffered times
                    res_start_buffered = res["start"] - timedelta(hours=CLEANING_BUFFER_HOURS)
                    res_end_buffered = res["end"] + timedelta(hours=CLEANING_BUFFER_HOURS)
                    # Check if buffered reservation overlaps with this date
                    if res_end_buffered > day_start and res_start_buffered < day_end:
                        # Store as timestamps (INTs) for ~3-5x faster comparisons
                        filtered_reservations.append({
                            "start_ts": int(res_start_buffered.timestamp()),
                            "end_ts": int(res_end_buffered.timestamp()),
                        })
                if filtered_reservations:
                    reservations_by_suite_for_date[suite_id] = filtered_reservations

            # For each suite, check which time slots are available
            suite_availability = {}
            has_available_slot = False
            selected_suite_available = False

            for suite_id in suite_ids:
                # Optimization: Early exit logic
                # - If suite_id is selected and is available (along with its night mapping), skip remaining suites
                # - Note: When no suite is selected (aggregated request), we CANNOT exit early because
                #   the frontend uses suite_availability to check ANY suite the user might have selected
                
                if selected_suite_id and selected_suite_available:
                    # Selected suite is available - skip remaining suites (no golden cells needed)
                    break
                
                # Determine minimum hours based on the suite being checked:
                # - Each suite uses its inherent minimum (2h for special Chambres, 3h for others)
                # - UNLESS no suite is selected (golden cell scenario), then force 3h minimum for ALL
                if selected_suite_id is None:
                    # No suite selected (golden cell): use 3-hour minimum for all suites
                    min_hours = DAY_MIN_HOURS
                elif suite_id in SPECIAL_MIN_DURATION_SUITES:
                    # This suite is a special Chambre: use 2-hour minimum
                    min_hours = SPECIAL_MIN_HOURS
                else:
                    # Regular suite: use 3-hour minimum
                    min_hours = DAY_MIN_HOURS
                
                # Check if this suite has a corresponding mapped suite ID (compute once per suite)
                suite_ids_to_check = [suite_id]
                mapped_suite_id = SUITE_ID_MAPPING.get(suite_id)
                if mapped_suite_id:
                    suite_ids_to_check.append(mapped_suite_id)

                # Collect relevant reservations for the suite(s) involved (pre-filtered by date)
                suite_reservations_for_date = []
                for sid in suite_ids_to_check:
                    suite_reservations_for_date.extend(reservations_by_suite_for_date.get(sid, []))

                # Generate all possible time slot combinations
                available_slots = []

                for slot_start, slot_end, arrival_time, departure_time, duration in precomputed_slots[min_hours]:
                    # Convert slot times to timestamps once per slot (not per reservation)
                    slot_start_ts = int(slot_start.timestamp())
                    slot_end_ts = int(slot_end.timestamp())

                    is_available = True
                    for reservation in suite_reservations_for_date:
                        # Check for overlap using integer timestamps (~3-5x faster than datetime comparison)
                        if not (slot_end_ts <= reservation["start_ts"] or slot_start_ts >= reservation["end_ts"]):
                            is_available = False
                            break

                    # Also check for resource block conflicts (if still available after reservation check)
                    if is_available:
                        # Get resource IDs for all suite categories we need to check (cached)
                        resource_ids_to_check = []
                        for sid in suite_ids_to_check:
                            resource_ids_to_check.extend(resource_ids_cache.get(sid, []))
                        
                        if check_resource_block_conflict(slot_start, slot_end, resource_ids_to_check, resource_blocks):
                            is_available = False

                    if is_available:
                        available_slots.append({
                            'arrival': arrival_time,
                            'departure': departure_time,
                            'duration': duration
                        })

                suite_availability[suite_id] = available_slots
                
                # Track if we found any available slot
                if len(available_slots) > 0:
                    has_available_slot = True
                    
                    # Check if selected suite (and its night mapping) is now confirmed available
                    if selected_suite_id and suite_id == selected_suite_id:
                        # Check if night mapping also needs to be verified
                        if selected_night_suite_id and selected_night_suite_id in suite_ids:
                            # Need to also check night suite - will be done in next iteration
                            # (since we reordered suite_ids to have night suite right after selected)
                            pass
                        else:
                            # No night mapping needed, selected suite is available
                            selected_suite_available = True
                    elif selected_suite_id and suite_id == selected_night_suite_id:
                        # Just checked night suite - verify if selected suite was also available
                        if selected_suite_id in suite_availability and len(suite_availability[selected_suite_id]) > 0:
                            selected_suite_available = True

            # Apply AND logic for mapped suites: if either suite in a pair has 0 availability, both must have 0
            for suite_id in list(suite_availability.keys()):
                # Check if this suite has a mapped counterpart
                mapped_suite_id = SUITE_ID_MAPPING.get(suite_id) or SUITE_ID_MAPPING_REVERSE.get(suite_id)
                
                if mapped_suite_id and mapped_suite_id in suite_availability:
                    # If either suite has 0 availability, set both to 0
                    if len(suite_availability[suite_id]) == 0 or len(suite_availability[mapped_suite_id]) == 0:
                        suite_availability[suite_id] = []
                        suite_availability[mapped_suite_id] = []

            # Recompute has_available_slot after AND logic application
            has_available_slot = any(len(slots) > 0 for slots in suite_availability.values())

            chunk_availability[date_str] = {
                "available": has_available_slot,
                "suite_availability": suite_availability
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

    # Fetch resource blocks for the entire date range
    # Use a wide buffer (2 days before/after) to catch multi-day blocks that might extend into our range
    if sorted_dates:
        range_start = datetime.fromisoformat(sorted_dates[0].replace('Z', '+00:00'))
        range_end = datetime.fromisoformat(sorted_dates[-1].replace('Z', '+00:00')) + timedelta(days=2)  # +2 for night checkout next day
        # Add generous buffer to catch multi-day blocks that start before or end after our range
        blocks_start = (range_start - timedelta(days=2)).isoformat()
        blocks_end = (range_end + timedelta(days=2)).isoformat()
        resource_blocks = get_resource_blocks(make_mews_request_func, blocks_start, blocks_end)
    else:
        resource_blocks = []

    # Process dates in chunks with parallel execution to speed up fetching
    CHUNK_SIZE_DAYS = 4  # Mews API limitation: max 4 days per chunk
    MAX_HOURS_PER_CHUNK = 96
    MAX_CONCURRENT_REQUESTS = 2
    
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
            belgian_tz = pytz.timezone(TIMEZONE)
            
            # Pre-compute timezone conversions for all reservations (outside the date loop)
            reservation_times = {}
            for reservation in reservations:
                res_id = id(reservation)
                res_start_utc = datetime.fromisoformat(reservation.get('StartUtc', '').replace('Z', '+00:00'))
                res_end_utc = datetime.fromisoformat(reservation.get('EndUtc', '').replace('Z', '+00:00'))
                # Convert to Brussels timezone for comparison with date boundaries
                reservation_times[res_id] = {
                    'start': res_start_utc.astimezone(belgian_tz),
                    'end': res_end_utc.astimezone(belgian_tz)
                }
            
            reservations_by_date = {}
            for date_str in chunk_dates:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                reservations_by_date[date_str] = []

                # Create date boundaries in Belgian timezone for accurate comparison
                date_start = belgian_tz.localize(datetime.combine(date_obj, datetime.min.time()))
                date_end = belgian_tz.localize(datetime.combine(date_obj + timedelta(days=1), datetime.min.time()))

                # Filter reservations that overlap with this specific date
                for reservation in reservations:
                    res_times = reservation_times[id(reservation)]
                    res_start = res_times['start']
                    res_end = res_times['end']

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

            def is_slot_available_for_suite(slot_start, slot_end, suite_reservations, suite_id_for_blocks=None):
                """Check if a suite has no reservation conflicts and no resource block conflicts for the provided slot."""
                # Convert slot times to timestamps once (not per reservation)
                slot_start_ts = int(slot_start.timestamp())
                slot_end_ts = int(slot_end.timestamp())
                
                # First check reservation conflicts using integer timestamps (~3-5x faster)
                for reservation in suite_reservations:
                    # Use pre-computed buffered timestamps
                    if not (slot_end_ts <= reservation["start_ts"] or slot_start_ts >= reservation["end_ts"]):
                        return False
                
                # Then check resource block conflicts
                if suite_id_for_blocks:
                    resource_ids_to_check = get_resource_ids_for_suites([suite_id_for_blocks])
                    if check_resource_block_conflict(slot_start, slot_end, resource_ids_to_check, resource_blocks):
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
                    # Pre-compute buffered timestamps for ~3-5x faster comparisons
                    res_start_buffered = res_start_local - timedelta(hours=CLEANING_BUFFER_HOURS)
                    res_end_buffered = res_end_local + timedelta(hours=CLEANING_BUFFER_HOURS)
                    suite_reservations_map[res_suite_id].append({
                        "start": res_start_local,
                        "end": res_end_local,
                        "start_ts": int(res_start_buffered.timestamp()),
                        "end_ts": int(res_end_buffered.timestamp())
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
                    if is_slot_available_for_suite(morning_start, morning_end, suite_reservations, suite_id):
                        morning_available_suite_ids.add(suite_id)
                    if is_slot_available_for_suite(night_start, night_end, suite_reservations, suite_id):
                        night_available_suite_ids.add(suite_id)

                available_morning = len(morning_available_suite_ids) > 0
                available_night = len(night_available_suite_ids) > 0
                # For backward compatibility, keep "available" aligned with night availability (check-in)
                chunk_availability[date_str] = {
                    "available": available_night,
                    "available_morning": available_morning,
                    "available_night": available_night,
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
