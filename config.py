"""
Shared configuration file for Intense Experience booking system.
This is the single source of truth for all constants and parameters.
"""

# =============================================================================
# MEWS API CONFIGURATION
# =============================================================================

# API endpoints
MEWS_API_BASE_URL = "https://api.mews-demo.com/api/connector/v1"
MEWS_PAYMENT_BASE_URL = "https://app.mews-demo.com/navigator/payment-requests/detail"

# Enterprise configuration
ENTERPRISE_ID = "c390a691-e9a0-4aa0-860c-b3850108ab4c"
CLIENT_NAME = "Intense Experience 1.0.0"

# =============================================================================
# SERVICE IDS
# =============================================================================

DAY_SERVICE_ID = "86fcc6a7-75ce-457a-a425-b3850108b6bf"  # JOURNEE
NIGHT_SERVICE_ID = "7ba0b732-93cc-477a-861d-b3850108b730"  # NUITEE

# =============================================================================
# RATE IDS
# =============================================================================

# Night rate
RATE_ID_NUITEE = "ed9391ac-b184-4876-8cc1-b3850108b8b0"  # Tarif Suites nuitée

# Day rates
RATE_ID_JOURNEE_SEMAINE = "c3c2109d-984a-4ad4-978e-b3850108b8ad"  # TARIF JOURNEE EN SEMAINE
RATE_ID_JOURNEE_WEEKEND = "d0496fa0-6686-4614-8847-b3850108c537"  # TARIF JOURNEE LE WEEKEND

# =============================================================================
# AGE CATEGORY IDS (fallback values if API call fails)
# =============================================================================

AGE_CATEGORY_ADULT_DAY = "a78b7aca-fa0b-4199-8b4e-b3850108b8a5"  # Day service adult category
AGE_CATEGORY_ADULT_NIGHT = "6cef9c83-4199-4b40-972b-b3850108b8a6"  # Night service adult category

# =============================================================================
# BOOKING CONFIGURATION
# =============================================================================

# Default cleaning buffer in hours
CLEANING_BUFFER_HOURS = 1

# Booking duration limits for journee bookings
DAY_MIN_HOURS = 3
DAY_MAX_HOURS = 6

# Maximum nights for nuitée bookings
NIGHT_MAX_NIGHTS = 2

# Default number of persons per booking
DEFAULT_PERSON_COUNT = 2

# Timezone for all Brussels-based time calculations
TIMEZONE = "Europe/Brussels"

# =============================================================================
# SPECIAL MINIMUM DURATION SUITES
# =============================================================================

# Chambres with 2-hour minimum instead of 3
SPECIAL_MIN_DURATION_SUITES = [
    "f5539e51-9db0-4082-b87e-b3850108c66f",  # Chambre EUPHORYA
    "78a614b1-199d-4608-ab89-b3850108c66f",  # Chambre IGNIS
    "67ece5a2-65e2-43c5-9079-b3850108c66f",  # Chambre KAIROS
    "1113bcbe-ad5f-49c7-8dc0-b3850108c66f",  # Chambre AETHER
]
SPECIAL_MIN_HOURS = 2

# =============================================================================
# TIME SLOTS FOR JOURNEE BOOKINGS
# =============================================================================

ARRIVAL_TIMES = ['12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
DEPARTURE_TIMES = ['13:00', '14:00', '15:00', '16:00', '17:00', '18:00']

# =============================================================================
# CHECK-IN/CHECK-OUT HOURS FOR NUITEE BOOKINGS
# =============================================================================

NIGHT_CHECK_IN_HOUR = 19  # 19:00 (7:00 PM)
NIGHT_CHECK_OUT_HOUR = 10  # 10:00 (10:00 AM)

# Early check-in and late check-out hours (for options)
EARLY_CHECK_IN_HOUR = 18  # 18:00 (6:00 PM)
LATE_CHECK_OUT_HOUR = 12  # 12:00 (12:00 PM)

# =============================================================================
# PAYMENT CONFIGURATION
# =============================================================================

DEFAULT_CURRENCY = "EUR"
PAYMENT_EXPIRATION_DAYS = 7

# =============================================================================
# SUITE ID MAPPING
# =============================================================================

# Maps day service suite IDs to night service suite IDs
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

