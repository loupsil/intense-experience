"""
Shared configuration file for Intense Experience booking system.
This is the single source of truth for all constants and parameters.
"""

# Demo environment flag
is_demo = False

if is_demo:
    # =============================================================================
    # MEWS API CONFIGURATION
    # =============================================================================

    # API endpoints
    MEWS_API_BASE_URL = "https://api.mews-demo.com/api/connector/v1"
    MEWS_PAYMENT_BASE_URL = "https://app.mews-demo.com/navigator/payment-requests/detail"

    # Enterprise configuration
    ENTERPRISE_ID = "c390a691-e9a0-4aa0-860c-b3850108ab4c"
    CLIENT_NAME = "Intense Experience DEMO - 1.0.0"

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
    EARLY_CHECK_IN_HOUR = 17  # 17:00 (5:00 PM)
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

    # =============================================================================
    # BUILDING RESOURCE ID (blocks all suites when blocked) - DEMO
    # =============================================================================
    # TODO: Add demo building resource ID when available
    BUILDING_RESOURCE_ID = None

    # =============================================================================
    # SUITE TO PHYSICAL RESOURCE MAPPING (for resource blocks) - DEMO
    # =============================================================================
    # TODO: Add demo resource IDs when available
    SUITE_TO_RESOURCE_ID = {}
else:
    # =============================================================================
    # MEWS API CONFIGURATION
    # =============================================================================

    # API endpoints
    MEWS_API_BASE_URL = "https://api.mews.com/api/connector/v1" #done
    MEWS_PAYMENT_BASE_URL = "https://app.mews.com/navigator/payment-requests/detail" #done

    # Enterprise configuration
    ENTERPRISE_ID = "28d11caf-bb59-42c1-9ec6-b1e30088afec" #done
    CLIENT_NAME = "Intense Experience PROD - 1.0.0" #done 

    # =============================================================================
    # SERVICE IDS
    # =============================================================================

    DAY_SERVICE_ID = "7664a134-ac16-464c-80c0-b2b5006f292d"  # JOURNEE #done
    NIGHT_SERVICE_ID = "86f73626-4488-4cb2-887b-b1e30088b6f4"  # NUITEE #done

    # =============================================================================
    # RATE IDS
    # =============================================================================

    # Night rate
    RATE_ID_NUITEE = "dac2dd73-d7e1-4d4f-ae97-b2b501111aa2"  # Tarif Suites nuitée #done

    # Day rates
    RATE_ID_JOURNEE_SEMAINE = "f389ce4e-07ee-4118-a9d9-b2b5014cce78"  # TARIF JOURNEE EN SEMAINE #done
    RATE_ID_JOURNEE_WEEKEND = "e1848543-0026-4197-b534-b2c200ac005d"  # TARIF JOURNEE LE WEEKEND #done

    # =============================================================================
    # AGE CATEGORY IDS (fallback values if API call fails)
    # =============================================================================

    AGE_CATEGORY_ADULT_DAY = "a967fef1-6d40-4506-99a6-b2b5006f2bbe"  # Day service adult category #done
    AGE_CATEGORY_ADULT_NIGHT = "927b3b7e-8d0f-4c4e-8eb9-b1e30088b911"  # Night service adult category #done

    # =============================================================================
    # BOOKING CONFIGURATION
    # =============================================================================

    # Default cleaning buffer in hours
    CLEANING_BUFFER_HOURS = 1 #done

    # Booking duration limits for journee bookings
    DAY_MIN_HOURS = 3 #done
    DAY_MAX_HOURS = 6 #done

    # Maximum nights for nuitée bookings
    NIGHT_MAX_NIGHTS = 2 #done

    # Default number of persons per booking
    DEFAULT_PERSON_COUNT = 2 #done

    # Timezone for all Brussels-based time calculations
    TIMEZONE = "Europe/Brussels" #done

    # =============================================================================
    # SPECIAL MINIMUM DURATION SUITES
    # =============================================================================

    # Chambres with 2-hour minimum instead of 3
    SPECIAL_MIN_DURATION_SUITES = [
        "7cb2802a-6404-41b2-80a3-b2b50146ae6f",  # Chambre EUPHORYA #done
        "15b14722-8aa0-482b-897c-b2b501457cac",  # Chambre IGNIS #done
        "4b5a16dd-3ac1-40a0-a7ff-b2b5014701e7",  # Chambre KAIROS #done
        "9465a9fe-3295-476c-a7f2-b2b50145d659",  # Chambre AETHER #done
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
    EARLY_CHECK_IN_HOUR = 17  # 17:00 (5:00 PM)
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
        "57ac61e2-cd46-47d1-a032-b2b501448106": "0f596098-93aa-432a-9bf2-b1e30088bcdb",  # journee -> nuitee #done  
        # Gaia Suite
        "f9f1b450-f6b8-40ba-93fe-b2b501453c7a": "66f622d5-7632-4e23-8e16-b2b50129835e",  # journee -> nuitee #done
        # Extase Suite
        "6bf55cbf-67a3-4a25-b7a8-b2b50144ecf5": "dcb31253-17bd-47d5-8c2b-b2b50129b921",  # journee -> nuitee #done
    }

    # Reverse mapping for convenience
    SUITE_ID_MAPPING_REVERSE = {v: k for k, v in SUITE_ID_MAPPING.items()}

    # =============================================================================
    # BUILDING RESOURCE ID (blocks all suites when blocked)
    # =============================================================================
    # When a resource block is assigned to this ID, it means the entire building is blocked
    BUILDING_RESOURCE_ID = "c29fb2fc-76e1-44ec-8cc2-b2dc009a8aec"

    # =============================================================================
    # SUITE TO PHYSICAL RESOURCE MAPPING (for resource blocks)
    # =============================================================================
    # Maps suite category IDs to physical resource IDs used in resource blocks
    # Physical rooms are numbered 1-9 in Mews
    # Room 1: INTENSE, Room 2: NAIADES, Room 3: AETHER, Room 4: IGNIS, Room 5: GAIA
    # Room 6: KAIROS, Room 7: HEDONE, Room 8: EUPHORYA, Room 9: EXTASE

    SUITE_TO_RESOURCE_ID = {
        # INTENSE (Room 1) - has both journée and nuitée
        "57ac61e2-cd46-47d1-a032-b2b501448106": "7461f9b1-34d5-41ee-9dc9-b1e30088bceb",  # INTENSE Journée
        "0f596098-93aa-432a-9bf2-b1e30088bcdb": "7461f9b1-34d5-41ee-9dc9-b1e30088bceb",  # INTENSE Nuitée
        # GAIA (Room 5) - has both journée and nuitée
        "f9f1b450-f6b8-40ba-93fe-b2b501453c7a": "fb18ffc9-0ba9-4f39-b0fe-b1e30088bceb",  # GAIA Journée
        "66f622d5-7632-4e23-8e16-b2b50129835e": "fb18ffc9-0ba9-4f39-b0fe-b1e30088bceb",  # GAIA Nuitée
        # EXTASE (Room 9) - has both journée and nuitée
        "6bf55cbf-67a3-4a25-b7a8-b2b50144ecf5": "600bfd6a-4226-4dbb-897c-b1e30088bceb",  # EXTASE Journée
        "dcb31253-17bd-47d5-8c2b-b2b50129b921": "600bfd6a-4226-4dbb-897c-b1e30088bceb",  # EXTASE Nuitée
        # AETHER (Room 3) - journée only
        "9465a9fe-3295-476c-a7f2-b2b50145d659": "183fdd1e-480a-44a3-b315-b1e30088bceb",  # AETHER Journée
        # IGNIS (Room 4) - journée only
        "15b14722-8aa0-482b-897c-b2b501457cac": "f5007af3-61da-450c-a5c0-b1e30088bceb",  # IGNIS Journée
        # KAIROS (Room 6) - journée only
        "4b5a16dd-3ac1-40a0-a7ff-b2b5014701e7": "6e1aa05b-6a8b-4bb4-87b7-b1e30088bceb",  # KAIROS Journée
        # EUPHORYA (Room 8) - journée only
        "7cb2802a-6404-41b2-80a3-b2b50146ae6f": "5b60745c-e2ca-4ce7-9261-b1e30088bceb",  # EUPHORYA Journée
    }

