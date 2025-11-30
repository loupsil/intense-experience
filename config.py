"""
Shared configuration file for Intense Experience booking system.
This is the single source of truth for all constants and parameters.
"""

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
ARRIVAL_TIMES = ['12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
DEPARTURE_TIMES = ['13:00', '14:00', '15:00', '16:00', '17:00', '18:00']

# Default check-in and check-out hours for nuitée bookings
NIGHT_CHECK_IN_HOUR = 19  # 19:00 (7:00 PM)
NIGHT_CHECK_OUT_HOUR = 10  # 10:00 (10:00 AM)

# Suite ID mapping: maps day service suite IDs to night service suite IDs
# This is needed because the same physical suite has different IDs in each service
SUITE_ID_MAPPING = {
    # Intense Suite
    "e4706d3a-2a06-4cb7-a449-b3850108c66f": "f867b5c6-f62d-451c-96ec-b3850108c66f",  # journee -> nuitee
    # Gaia Suite
    "f723bd5a-04fe-479c-bab4-b3850108c66f": "3872869e-6278-4c64-aea8-b3850108c66f",  # journee -> nuitee
    # Extase Suite
    "68b87fe5-7b78-4067-b5e7-b3850108c66f": "0d535116-b1db-476e-8bff-b3850108c66f",  # journee -> nuitee
}

# Reverse mapping for convenience
SUITE_ID_MAPPING_REVERSE = {v: k for k, v in SUITE_ID_MAPPING.items()}

