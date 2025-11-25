<template>
  <div class="calendar-selector">
    <div class="calendar-layout">
      <!-- Left Side: Calendar -->
      <div class="calendar-left">
        <div class="date-selection">
          <div v-if="selectedBookingType === 'day'" class="day-booking">
            <!-- Two Month Calendar View -->
            <div class="two-month-calendar">
              <!-- Single loading overlay for entire calendar -->
              <div v-if="availabilityLoading" class="calendar-loading-overlay">
                <div class="spinner"></div>
              </div>

              <!-- Current Month -->
              <div class="month-calendar">
                <div class="month-header">
                  <button @click="previousMonth" class="nav-btn">&larr;</button>
                  <h4>{{ formatMonthYear(currentMonth) }}</h4>
                  <button v-if="isMobile" @click="nextMonth" class="nav-btn">&rarr;</button>
                </div>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <div
                    v-for="date in getDaysInMonth(currentMonth)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateSelected(date),
                      'available': isDateAvailable(date) && !isDatePartiallyAvailable(date),
                      'partially-available': isDatePartiallyAvailable(date),
                      'unavailable': !isDateAvailable(date) && !isDatePartiallyAvailable(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, currentMonth)
                    }"
                    @click="!availabilityLoading && selectDate(date)"
                    :data-debug="(date.getDate() === 5 || date.getDate() === 18) && date.getMonth() === 11 ? JSON.stringify({
                      day: date.getDate(),
                      available: isDateAvailable(date),
                      partiallyAvailable: isDatePartiallyAvailable(date),
                      unavailable: !isDateAvailable(date) && !isDatePartiallyAvailable(date)
                    }) : null"
                  >
                    <span class="date-number">{{ date.getDate() }}</span>
                  </div>
                </div>
              </div>

              <!-- Next Month (hidden on mobile) -->
              <div v-if="!isMobile" class="month-calendar">
                <div class="month-header">
                  <h4>{{ formatMonthYear(nextMonthDate) }}</h4>
                  <button @click="nextMonth" class="nav-btn">&rarr;</button>
                </div>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <div
                    v-for="date in getDaysInMonth(nextMonthDate)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateSelected(date),
                      'available': isDateAvailable(date) && !isDatePartiallyAvailable(date),
                      'partially-available': isDatePartiallyAvailable(date),
                      'unavailable': !isDateAvailable(date) && !isDatePartiallyAvailable(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, nextMonthDate)
                    }"
                    @click="!availabilityLoading && selectDate(date)"
                  >
                    <span class="date-number">{{ date.getDate() }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedBookingType === 'night'" class="night-booking">
            <!-- Two Month Calendar View -->
            <div class="two-month-calendar">
              <!-- Single loading overlay for entire calendar -->
              <div v-if="availabilityLoading" class="calendar-loading-overlay">
                <div class="spinner"></div>
              </div>

              <!-- Current Month -->
              <div class="month-calendar">
                <div class="month-header">
                  <button @click="previousMonth" class="nav-btn">&larr;</button>
                  <h4>{{ formatMonthYear(currentMonth) }}</h4>
                  <button v-if="isMobile" @click="nextMonth" class="nav-btn">&rarr;</button>
                </div>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <div
                    v-for="date in getDaysInMonth(currentMonth)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateInRange(date),
                      'selected-start': isStartDate(date),
                      'selected-end': isEndDate(date),
                      'available': getNightCellAvailabilityClass(date),
                      'unavailable': getNightCellUnavailableClass(date),
                      'other-suite-available': shouldShowOtherSuiteAnyAvailability(date),
                      'other-suite-morning': shouldShowOtherSuiteMorningAvailability(date),
                      'other-suite-night': shouldShowOtherSuiteNightAvailability(date),
                      'morning-availability': hasMorningSlotAvailability(date),
                      'night-availability': hasNightSlotAvailability(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, currentMonth),
                      'diagonal-overlay': getDiagonalOverlayState(date, getDaysInMonth(currentMonth)).normal,
                      'diagonal-overlay-reverse': getDiagonalOverlayState(date, getDaysInMonth(currentMonth)).reverse
                    }"
                    @click="!availabilityLoading && selectNightDate(date)"
                  >
                    <span class="date-number">{{ date.getDate() }}</span>
                  </div>
                </div>
              </div>

              <!-- Next Month (hidden on mobile) -->
              <div v-if="!isMobile" class="month-calendar">
                <div class="month-header">
                  <h4>{{ formatMonthYear(nextMonthDate) }}</h4>
                  <button @click="nextMonth" class="nav-btn">&rarr;</button>
                </div>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <div
                    v-for="date in getDaysInMonth(nextMonthDate)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateInRange(date),
                      'selected-start': isStartDate(date),
                      'selected-end': isEndDate(date),
                      'available': getNightCellAvailabilityClass(date),
                      'unavailable': getNightCellUnavailableClass(date),
                      'other-suite-available': shouldShowOtherSuiteAnyAvailability(date),
                      'other-suite-morning': shouldShowOtherSuiteMorningAvailability(date),
                      'other-suite-night': shouldShowOtherSuiteNightAvailability(date),
                      'morning-availability': hasMorningSlotAvailability(date),
                      'night-availability': hasNightSlotAvailability(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, nextMonthDate),
                      'diagonal-overlay': getDiagonalOverlayState(date, getDaysInMonth(nextMonthDate)).normal,
                      'diagonal-overlay-reverse': getDiagonalOverlayState(date, getDaysInMonth(nextMonthDate)).reverse
                    }"
                    @click="!availabilityLoading && selectNightDate(date)"
                  >
                    <span class="date-number">{{ date.getDate() }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Side: Time Selector -->
      <div class="calendar-right">
        <TimeSelector
          :booking-type="selectedBookingType"
          :selected-date="selectedBookingType === 'day' ? selectedDates.start : null"
          :selected-dates="selectedBookingType === 'night' ? selectedDates : { start: null, end: null }"
          :date-availability="getDateAvailability(selectedDates.start)"
          :service="service"
        :selected-suite="suiteForBooking"
          :suite-pricing="suitePricing"
          @time-selected="handleTimeSelection"
          @book-suite="confirmSelection"
        />
      </div>
    </div>

    <!-- Calendar Legend -->
    <div class="calendar-legend">
      <div class="legend-item">
        <span class="legend-color legend-available"></span>
        <span class="legend-label">Available</span>
      </div>
      <div class="legend-item">
        <span class="legend-color legend-unavailable"></span>
        <span class="legend-label">Unavailable</span>
      </div>
      <div v-if="selectedSuite" class="legend-item">
        <span class="legend-color legend-other-suites"></span>
        <span class="legend-label">Other suites available</span>
      </div>
    </div>

    <div class="calendar-footer">
      <button v-if="selectedDates.start" @click="clearDates" class="clear-dates-link">Clear dates</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CalendarSelector',
  components: {
    'TimeSelector': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/TimeSelector.vue', window.vueOptions))
  },
  props: {
    service: {
      type: Object,
      required: true
    },
    bookingType: {
      type: String,
      default: 'day'
    },
    selectedSuite: {
      type: Object,
      default: null
    },
    suitePricing: {
      type: Object,
      default: () => ({})
    },
    suiteForBooking: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      selectedBookingType: this.bookingType,
      selectedDates: { start: null, end: null },
      selectedTimeSlot: null,
      checkInDate: '',
      checkOutDate: '',
      availableDates: [],
      availabilityLoading: false,
      currentAvailability: {}, // Current availability data (replaced on each fetch)
      selectedSuiteAvailability: {}, // Availability scoped to selected suite (night bookings)
      currentRequestId: null, // Track current request to prevent stale responses
      minDate: new Date().toISOString().split('T')[0],
      currentMonth: new Date(),
      weekDays: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
      selectionMode: 'start', // 'start' or 'end'
      nightCheckInHour: null,
      nightCheckOutHour: null,
      bookingLimitsLoaded: false
    }
  },
  computed: {
    selectionComplete() {
      if (this.selectedBookingType === 'day') {
        // For day bookings, we just need the dates (times are handled in TimeSelector)
        return this.selectedDates.start && this.selectedDates.end
      } else {
        return this.selectedDates.start && this.selectedDates.end
      }
    },
    nextMonthDate() {
      const next = new Date(this.currentMonth)
      next.setMonth(next.getMonth() + 1)
      return next
    },
    isMobile() {
      return window.innerWidth <= 768
    }
  },
  watch: {
    bookingType: {
      immediate: true,
      handler(newType) {
        this.selectedBookingType = newType
        this.resetSelection()
        // Clear current availability when booking type changes
        this.currentAvailability = {}
        this.selectedSuiteAvailability = {}
        // Calendar is now always displayed for both booking types
      }
    },
    selectedSuite: {
      handler(newSuite, oldSuite) {
        // Clear current availability when suite selection changes
        // This ensures we fetch fresh availability data for the selected suite
        if (newSuite !== oldSuite) {
          this.currentAvailability = {}
          this.selectedSuiteAvailability = {}
          // Refetch availability for currently displayed dates
          this.fetchAvailabilityForDisplayedDates()
        }
      }
    }
  },
  async mounted() {
    // Calendar is now always displayed for both day and night bookings
    // Fetch booking limits and availability in parallel since availability doesn't depend on limits
    await Promise.all([
      this.fetchBookingLimits(),
      this.fetchAvailabilityForDisplayedDates()
    ])
  },
  methods: {

    async fetchBookingLimits() {
      try {
        const response = await fetch('/intense_experience-api/booking-limits')
        const data = await response.json()
        if (data.status === 'success') {
          // Update night booking hours from backend
          this.nightCheckInHour = data.night_check_in_hour
          this.nightCheckOutHour = data.night_check_out_hour
          this.bookingLimitsLoaded = true
        }
      } catch (error) {
        console.error('Failed to fetch booking limits from backend:', error)
        this.bookingLimitsLoaded = true // Still mark as loaded to prevent infinite loading
      }
    },

    async fetchBulkAvailability(dates) {
      if (!this.service || !dates || dates.length === 0) return

      // Generate a unique request ID for this request
      const requestId = Date.now() + Math.random()
      this.currentRequestId = requestId

      this.availabilityLoading = true

      // Determine which endpoint to use based on booking type
      const endpoint = this.selectedBookingType === 'night'
        ? '/intense_experience-api/bulk-availability-nuitee'
        : '/intense_experience-api/bulk-availability-journee'

      const baseRequestData = {
        service_id: this.service.Id,
        dates,
        booking_type: this.selectedBookingType,
        suite_id: null
      }

      const aggregatedRequest = this.performBulkAvailabilityRequest(
        endpoint,
        baseRequestData,
        dates,
        { fallbackOnError: true }
      )

      const shouldFetchSuiteSpecific = this.selectedBookingType === 'night' && this.selectedSuite
      let suiteSpecificRequest = null

      if (shouldFetchSuiteSpecific) {
        const suiteRequestData = {
          ...baseRequestData,
          suite_id: this.selectedSuite.Id
        }
        // Clear suite-specific data while loading to avoid stale highlights
        this.selectedSuiteAvailability = {}
        suiteSpecificRequest = this.performBulkAvailabilityRequest(
          endpoint,
          suiteRequestData,
          dates,
          { fallbackOnError: false }
        )
      } else {
        this.selectedSuiteAvailability = {}
      }

      try {
        const aggregatedAvailability = await aggregatedRequest
        if (this.currentRequestId !== requestId) {
          return
        }

        if (aggregatedAvailability) {
          this.currentAvailability = aggregatedAvailability
        }

        if (suiteSpecificRequest) {
          const suiteAvailability = await suiteSpecificRequest
          if (this.currentRequestId !== requestId) {
            return
          }
          this.selectedSuiteAvailability = suiteAvailability || {}
        }

        // Use nextTick to ensure DOM updates happen atomically once both requests resolve
        await this.$nextTick()
      } catch (error) {
        console.error('Failed to process availability:', error)
      } finally {
        // Only update loading state if this is still the current request
        if (this.currentRequestId === requestId) {
          this.availabilityLoading = false
        }
      }
    },

    async performBulkAvailabilityRequest(endpoint, payload, dates, { fallbackOnError = true } = {}) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()

        if (data.status === 'success' && data.availability) {
          return data.availability
        }

        console.error('Bulk availability failed:', data.error)
      } catch (error) {
        console.error('Failed to fetch availability:', error)
      }

      return fallbackOnError ? this.buildAvailabilityErrorMap(dates) : null
    },

    buildAvailabilityErrorMap(dates) {
      const fallback = {}
      dates.forEach(dateStr => {
        fallback[dateStr] = {
          available: false,
          available_morning: false,
          available_night: false,
          total_suites: 0,
          booked_suites: 0,
          available_suites: 0,
          booked_suite_ids: [],
          error: true
        }
      })
      return fallback
    },

    async fetchAvailabilityForDisplayedDates() {
      // Get all dates currently displayed in the calendar
      const displayedDates = []
      const currentMonthDates = this.getDaysInMonth(this.currentMonth)
      const nextMonthDates = this.getDaysInMonth(this.nextMonthDate)

      // Collect all visible dates (normalize to UTC midnight)
      currentMonthDates.forEach(date => {
        if (!this.isDateInPast(date)) {
          // Create UTC date at midnight to avoid timezone issues
          const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
          displayedDates.push(utcDate.toISOString())
        }
      })
      nextMonthDates.forEach(date => {
        if (!this.isDateInPast(date)) {
          // Create UTC date at midnight to avoid timezone issues
          const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
          displayedDates.push(utcDate.toISOString())
        }
      })

      // Fetch availability for all displayed dates
      if (displayedDates.length > 0) {
        await this.fetchBulkAvailability(displayedDates)
      }
    },

    isDateAvailable(date) {
      if (this.isDateInPast(date)) return false

      if (this.selectedBookingType === 'night') {
        return this.getNightAvailabilityFlags(date).any
      }

      // Use getDateAvailability which handles suite filtering
      const availability = this.getDateAvailability(date)

      if (!availability) {
        // If we don't have availability data yet, show as unavailable (will load)
        return false
      }

      // Date is available if at least one suite has at least one time slot free
      return availability.available
    },

    shouldUseSuiteSpecificAvailability() {
      return this.selectedBookingType === 'night' &&
        !!this.selectedSuite &&
        Object.keys(this.selectedSuiteAvailability || {}).length > 0
    },

    getNightAvailabilityData(date) {
      const overall = this.getDateAvailability(date)
      const suiteSpecific = this.shouldUseSuiteSpecificAvailability()
        ? this.getDateAvailability(date, this.selectedSuiteAvailability)
        : null

      return {
        overall,
        suiteSpecific
      }
    },

    getNightFlagsFromAvailability(availability) {
      if (!availability) {
        return { morning: false, night: false, any: false }
      }

      const hasMorningField = Object.prototype.hasOwnProperty.call(availability, 'available_morning')
      const hasNightField = Object.prototype.hasOwnProperty.call(availability, 'available_night')
      const fallback = !!availability.available

      const morning = hasMorningField ? !!availability.available_morning : fallback
      const night = hasNightField ? !!availability.available_night : fallback

      return {
        morning,
        night,
        any: morning || night
      }
    },

    getNightAvailabilityFlags(date) {
      const { suiteSpecific, overall } = this.getNightAvailabilityData(date)
      const availability = suiteSpecific || overall
      return this.getNightFlagsFromAvailability(availability)
    },

    getOtherSuitesNightFlags(date) {
      if (!this.shouldUseSuiteSpecificAvailability()) {
        return { morning: false, night: false, any: false }
      }

      const { suiteSpecific, overall } = this.getNightAvailabilityData(date)
      if (!suiteSpecific || !overall) {
        return { morning: false, night: false, any: false }
      }

      const overallFlags = this.getNightFlagsFromAvailability(overall)
      const suiteFlags = this.getNightFlagsFromAvailability(suiteSpecific)

      return {
        morning: overallFlags.morning && !suiteFlags.morning,
        night: overallFlags.night && !suiteFlags.night,
        any: overallFlags.any && !suiteFlags.any
      }
    },

    shouldShowOtherSuiteAnyAvailability(date) {
      return this.getOtherSuitesNightFlags(date).any
    },

    shouldShowOtherSuiteMorningAvailability(date) {
      return this.getOtherSuitesNightFlags(date).morning
    },

    shouldShowOtherSuiteNightAvailability(date) {
      return this.getOtherSuitesNightFlags(date).night
    },

    hasMorningSlotAvailability(date) {
      if (this.selectedBookingType !== 'night') {
        return this.isDateAvailable(date)
      }
      return this.getNightAvailabilityFlags(date).morning
    },

    hasNightSlotAvailability(date) {
      if (this.selectedBookingType !== 'night') {
        return this.isDateAvailable(date)
      }
      return this.getNightAvailabilityFlags(date).night
    },

    hasAnyNightSlotAvailability(date) {
      if (this.selectedBookingType !== 'night') {
        return this.isDateAvailable(date)
      }
      // For night bookings, check if ANY suite has availability (overall availability)
      // not just the selected suite - this allows selection of golden cells
      const { overall } = this.getNightAvailabilityData(date)
      const overallFlags = this.getNightFlagsFromAvailability(overall)
      return overallFlags.any
    },

    getNightCellAvailabilityClass(date) {
      if (this.selectedBookingType !== 'night') {
        return this.isDateAvailable(date)
      }
      // For color coding, use suite-specific availability (shows golden cells as unavailable)
      const availabilityFlags = this.getNightAvailabilityFlags(date)
      return availabilityFlags.any
    },

    getNightCellUnavailableClass(date) {
      if (this.selectedBookingType !== 'night') {
        return !this.isDateAvailable(date)
      }
      // For color coding, use suite-specific availability (shows golden cells as unavailable)
      const availabilityFlags = this.getNightAvailabilityFlags(date)
      return !availabilityFlags.any
    },

    isDateRangeFullyAvailable(startDate, endDate) {
      // Check all dates from start (inclusive) to end (inclusive) for availability
      const currentDate = new Date(startDate)
      const end = new Date(endDate)

      while (currentDate <= end) {
        const availabilityFlags = this.getNightAvailabilityFlags(currentDate)

        // Start date needs night availability for check-in
        // End date needs morning availability for check-out
        // Dates in between need both morning and night availability
        const isStartDate = currentDate.toDateString() === startDate.toDateString()
        const isEndDate = currentDate.toDateString() === endDate.toDateString()

        if (isStartDate) {
          // Start date: needs night availability
          if (!availabilityFlags.night) {
            return false
          }
        } else if (isEndDate) {
          // End date: needs morning availability
          if (!availabilityFlags.morning) {
            return false
          }
        } else {
          // Dates in between: need both morning and night availability
          if (!availabilityFlags.morning || !availabilityFlags.night) {
            return false
          }
        }

        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1)
      }

      return true
    },

    isDateRangePartiallyAvailable(startDate, endDate) {
      // Check if the range contains any dates where selected suite is unavailable but others are available
      const currentDate = new Date(startDate)
      const end = new Date(endDate)

      while (currentDate <= end) {
        // Check if this date has any availability but the selected suite slot is not available
        const hasAnyAvailability = this.hasAnyNightSlotAvailability(currentDate)
        const availabilityFlags = this.getNightAvailabilityFlags(currentDate)

        const isStartDate = currentDate.toDateString() === startDate.toDateString()
        const isEndDate = currentDate.toDateString() === endDate.toDateString()

        let slotAvailable = false
        if (isStartDate) {
          slotAvailable = availabilityFlags.night
        } else if (isEndDate) {
          slotAvailable = availabilityFlags.morning
        } else {
          slotAvailable = availabilityFlags.morning && availabilityFlags.night
        }

        // If date has any availability but the specific slot for selected suite is not available
        if (hasAnyAvailability && !slotAvailable) {
          return true
        }

        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1)
      }

      return false
    },

    isDatePartiallyAvailable(date) {
      // Only applies to day bookings with a specific suite selected
      if (this.selectedBookingType !== 'day' || !this.selectedSuite) {
        return false
      }

      if (this.isDateInPast(date)) return false

      const availability = this.getDateAvailability(date)
      if (!availability) return false

      // Check if the selected suite is unavailable
      const selectedSuiteId = this.selectedSuite.Id
      const suiteAvailability = availability.suite_availability || {}
      const selectedSuiteSlots = suiteAvailability[selectedSuiteId] || []
      const selectedSuiteAvailable = selectedSuiteSlots.length > 0

      // Check if other suites are available
      const otherSuitesAvailable = Object.keys(suiteAvailability).some(suiteId => {
        return suiteId !== selectedSuiteId && suiteAvailability[suiteId].length > 0
      })

      // Partial availability: selected suite unavailable BUT other suites available
      return !selectedSuiteAvailable && otherSuitesAvailable
    },

    isDateSelected(date) {
      if (!this.selectedDates.start) return false

      if (this.selectedBookingType === 'day') {
        return date.toDateString() === this.selectedDates.start.toDateString()
      } else {
        if (!this.selectedDates.end) return false
        return date >= this.selectedDates.start && date <= this.selectedDates.end
      }
    },

    async selectDate(date) {
      if (this.selectedBookingType === 'day') {
        // For day bookings, select a single day
        this.selectedDates = {
          start: new Date(date),
          end: new Date(date)
        }
        // Note: Don't set default times here - TimeSelector will handle time selection

        // Check if this is a partially available date (selected suite unavailable, but other suites available)
        // If so, we need to clear the suite selection
        if (this.isDatePartiallyAvailable(date)) {
          console.log('CalendarSelector: Partially available date selected, clearing suite selection')
          this.$emit('suite-deselected')
        } else if (this.isDateAvailable(date)) {
          // If this is a fully available date and we previously cleared suite selection, reset it
          console.log('CalendarSelector: Fully available date selected, resetting suite selection')
          this.$emit('suite-reselected')
        }

        // Ensure availability data is loaded for this date (normalize to UTC midnight)
        const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
        const dateStr = utcDate.toISOString()
        if (!this.currentAvailability[dateStr]) {
          await this.fetchBulkAvailability([dateStr])
        }

        // For day bookings, don't emit date-selected until times are selected
        // This prevents premature pricing calculation
      }
    },

    selectNightDate(date) {
      if (this.isDateInPast(date)) return

      const selectedDate = new Date(date)
      let isSelectingStart = this.selectionMode === 'start' || !this.selectedDates.start

      if (!isSelectingStart && this.selectedDates.start && selectedDate <= this.selectedDates.start) {
        isSelectingStart = true
      }

      // For night bookings with a selected suite, allow selection of dates with any availability
      // (including golden cells where selected suite is unavailable but others are available)
      const hasAnyAvailability = this.hasAnyNightSlotAvailability(date)
      if (!hasAnyAvailability) return

      const availabilityFlags = this.getNightAvailabilityFlags(date)
      const slotAvailable = isSelectingStart ? availabilityFlags.night : availabilityFlags.morning

      // If the specific slot for selected suite is not available, but other slots/suites are,
      // allow selection but mark that suite selection needs to be cleared
      const needsSuiteClearing = !slotAvailable && hasAnyAvailability

      if (isSelectingStart) {
        // Selecting start date
        this.selectedDates.start = new Date(selectedDate)
        this.selectedDates.start.setHours(this.nightCheckInHour, 0, 0, 0)
        this.selectedDates.end = null
        this.selectionMode = 'end'

        // If this date needs suite clearing (golden cell), emit the event
        if (needsSuiteClearing) {
          console.log('CalendarSelector: Golden start date selected for night booking, clearing suite selection')
          this.$emit('suite-deselected')
        } else if (slotAvailable) {
          // If this date is fully available for the selected suite, reset suite selection if it was previously cleared
          console.log('CalendarSelector: Fully available start date selected for night booking, resetting suite selection')
          this.$emit('suite-reselected')
        }
      } else {
        // Selecting end date - check if all dates in range are available
        if (selectedDate <= this.selectedDates.start) {
          // If selected date is before or same as start, reset start date
          this.selectedDates.start = new Date(selectedDate)
          this.selectedDates.start.setHours(this.nightCheckInHour, 0, 0, 0)
          this.selectedDates.end = null
          this.selectionMode = 'end'

          // If this reset start date needs suite clearing (golden cell), emit the event
          if (needsSuiteClearing) {
            console.log('CalendarSelector: Golden reset start date selected for night booking, clearing suite selection')
            this.$emit('suite-deselected')
          } else if (slotAvailable) {
            // If this reset start date is fully available for the selected suite, reset suite selection if it was previously cleared
            console.log('CalendarSelector: Fully available reset start date selected for night booking, resetting suite selection')
            this.$emit('suite-reselected')
          }
        } else {
          // For night bookings with suite selection, allow ranges that include golden dates
          // but clear suite selection if any date in range needs it
          const rangeNeedsSuiteClearing = this.isDateRangePartiallyAvailable(this.selectedDates.start, selectedDate)

          if (!this.isDateRangeFullyAvailable(this.selectedDates.start, selectedDate) && !rangeNeedsSuiteClearing) {
            this.resetSelection() // Reset selection when invalid range is selected
            return
          }

          // Set end date
          this.selectedDates.end = new Date(selectedDate)
          this.selectedDates.end.setHours(this.nightCheckOutHour, 0, 0, 0)
          this.selectionMode = 'start'

          // If this date or range needs suite clearing (includes golden cells), emit the event
          if (needsSuiteClearing || rangeNeedsSuiteClearing) {
            console.log('CalendarSelector: Golden end date or range selected for night booking, clearing suite selection')
            this.$emit('suite-deselected')
          } else {
            // If the end date and range are fully available for the selected suite, reset suite selection if it was previously cleared
            console.log('CalendarSelector: Fully available end date and range selected for night booking, resetting suite selection')
            this.$emit('suite-reselected')
          }

          // Emit date selection when both dates are selected for pricing calculation
          console.log('CalendarSelector emitting preliminary date-selected for night booking')
          this.$emit('date-selected', {
            start: this.selectedDates.start.toISOString(),
            end: this.selectedDates.end.toISOString(),
            type: this.selectedBookingType
          })
        }
      }
    },

    resetSelection() {
      this.selectedDates = { start: null, end: null }
      this.checkInDate = ''
      this.checkOutDate = ''
      this.selectionMode = 'start'
    },

    clearDates() {
      this.resetSelection()
    },

    async previousMonth() {
      this.currentMonth.setMonth(this.currentMonth.getMonth() - 2)
      this.currentMonth = new Date(this.currentMonth)
      // Fetch availability for newly displayed dates
      await this.fetchAvailabilityForDisplayedDates()
    },

    async nextMonth() {
      this.currentMonth.setMonth(this.currentMonth.getMonth() + 2)
      this.currentMonth = new Date(this.currentMonth)
      // Fetch availability for newly displayed dates
      await this.fetchAvailabilityForDisplayedDates()
    },

    getDaysInMonth(month) {
      const year = month.getFullYear()
      const monthIndex = month.getMonth()
      const firstDay = new Date(year, monthIndex, 1)
      const lastDay = new Date(year, monthIndex + 1, 0)
      const daysInMonth = lastDay.getDate()

      // Get the day of the week for the first day (0 = Sunday, 1 = Monday, etc.)
      // Adjust to make Monday = 0
      let startDayOfWeek = firstDay.getDay() - 1
      if (startDayOfWeek < 0) startDayOfWeek = 6

      const days = []

      // Add empty cells for days before the first day of the month
      for (let i = startDayOfWeek - 1; i >= 0; i--) {
        const prevMonth = new Date(year, monthIndex, -i)
        days.push(new Date(prevMonth))
      }

      // Add all days of the current month
      for (let day = 1; day <= daysInMonth; day++) {
        days.push(new Date(year, monthIndex, day))
      }

      // Add empty cells for days after the last day of the month to fill the grid
      const remainingCells = 42 - days.length // 6 weeks * 7 days = 42 cells
      for (let i = 1; i <= remainingCells; i++) {
        days.push(new Date(year, monthIndex + 1, i))
      }

      return days
    },

    isDateInCurrentMonth(date, month) {
      return date.getMonth() === month.getMonth() && date.getFullYear() === month.getFullYear()
    },

    isDateInRange(date) {
      if (!this.selectedDates.start || !this.selectedDates.end) return false
      return date >= this.selectedDates.start && date <= this.selectedDates.end
    },

    isStartDate(date) {
      return this.selectedDates.start && date.toDateString() === this.selectedDates.start.toDateString()
    },

    isEndDate(date) {
      return this.selectedDates.end && date.toDateString() === this.selectedDates.end.toDateString()
    },

    isDateInPast(date) {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const compareDate = new Date(date)
      compareDate.setHours(0, 0, 0, 0)
      return compareDate < today
    },

    formatMonthYear(date) {
      return date.toLocaleDateString('en-US', { month: 'long' })
    },

    handleTimeSelection(timeData) {
      console.log('Time selection received in CalendarSelector:', timeData)
      // For day bookings, update both start and end times based on selected arrival/departure times
      if (this.selectedBookingType === 'day' && this.selectedDates.start) {
        // Get the base date (date only, without time)
        const baseDate = new Date(this.selectedDates.start)
        baseDate.setHours(0, 0, 0, 0)

        // Update start time with arrival time
        if (timeData.arrival) {
          const startDate = new Date(baseDate)
          const [arrHours, arrMinutes] = timeData.arrival.split(':')
          startDate.setHours(parseInt(arrHours), parseInt(arrMinutes), 0, 0)
          this.selectedDates.start = startDate
        }

        // Update end time with departure time
        if (timeData.departure) {
          const endDate = new Date(baseDate)
          const [depHours, depMinutes] = timeData.departure.split(':')
          endDate.setHours(parseInt(depHours), parseInt(depMinutes), 0, 0)
          this.selectedDates.end = endDate
        }

        // Emit date update for pricing recalculation
        console.log('CalendarSelector emitting time-updated date-selected for day booking')
        this.$emit('date-selected', {
          start: this.selectedDates.start.toISOString(),
          end: this.selectedDates.end.toISOString(),
          type: this.selectedBookingType
        })
      }
    },

    confirmSelection() {
      if (this.selectionComplete) {
        const selectionData = {
          start: this.selectedDates.start.toISOString(),
          end: this.selectedDates.end.toISOString(),
          type: this.selectedBookingType
        }

        // Add time slot data for day bookings
        if (this.selectedBookingType === 'day' && this.selectedTimeSlot) {
          selectionData.timeSlot = this.selectedTimeSlot
        }

        this.$emit('date-selected', selectionData)
        // Also emit dates-confirmed to automatically proceed to next step
        this.$emit('dates-confirmed')
      }
    },

    getDayName(date) {
      const days = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam']
      return days[date.getDay()]
    },

    formatDate(date) {
      return new Date(date).toLocaleDateString('fr-FR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    },

    calculateNights() {
      if (!this.selectedDates.start || !this.selectedDates.end) return 0
      const diffTime = Math.abs(this.selectedDates.end - this.selectedDates.start)
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    },

    getDateAvailability(date, source = null) {
      if (!date) return null
      // Normalize to UTC midnight to match availability keys
      const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
      const dateStr = utcDate.toISOString()
      const availabilitySource = source || this.currentAvailability
      if (!availabilitySource) {
        return null
      }
      const availability = availabilitySource[dateStr] || null

      return availability
    },

    getDiagonalOverlayState(date, datesArray) {
      // Only apply for night bookings
      if (this.selectedBookingType !== 'night') {
        return { normal: false, reverse: false }
      }

      // Only apply if current date is available
      if (!this.isDateAvailable(date)) {
        return { normal: false, reverse: false }
      }

      // Find the index of this date in the dates array
      const dateIndex = datesArray.findIndex(d => d.toDateString() === date.toDateString())
      if (dateIndex === -1) {
        return { normal: false, reverse: false }
      }

      let normal = false
      let reverse = false

      // Check for normal overlay (left unavailable, right available)
      if (dateIndex % 7 !== 0) {
        const previousDate = datesArray[dateIndex - 1]
        if (previousDate && !this.isDateAvailable(previousDate)) {
          normal = true
        }
      }

      // Check for reverse overlay (right unavailable, left available)
      if (dateIndex % 7 !== 6) {
        const nextDate = datesArray[dateIndex + 1]
        if (nextDate && !this.isDateAvailable(nextDate)) {
          reverse = true
        }
      }

      return { normal, reverse }
    }
  }
}
</script>

<style scoped>
.calendar-selector {
  max-width: 1000px;
  margin: 0 auto;
}

.calendar-layout {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 30px;
  align-items: center;
}

.calendar-left {
  flex: 1;
}

.calendar-right {
  width: 350px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin: 20px 0;
}

.calendar-day {
  aspect-ratio: 1;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.calendar-day:hover:not(.unavailable) {
  border-color: #007bff;
  transform: scale(1.05);
}

.calendar-day.selected {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.calendar-day.available {
  background: #f8fff9;
}

.calendar-day.unavailable {
  background: #fff5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

.day-number {
  font-size: 18px;
  font-weight: bold;
}

.day-name {
  font-size: 12px;
  margin-top: 2px;
}

.availability-indicator {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  display: inline-block;
  margin-right: 8px;
}

.available-color {
  background: #d4edda;
  border: 2px solid #219672;
}

.unavailable-color {
  background: #f8d7da;
  border: 2px solid #B33D43;
}

/* Month Header with Navigation */
.month-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-bottom: 15px;
}

.month-header h4 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 500;
  text-align: center;
  text-transform: capitalize;
  flex: 1;
}

.nav-btn {
  background: transparent;
  border: none;
  width: 30px;
  height: 30px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #333;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.nav-btn:hover {
  color: #007bff;
}

/* Two Month Calendar View */
.two-month-calendar {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin: 20px 0;
  position: relative;
}

.month-calendar {
  background: transparent;
  border-radius: 0;
  padding: 0;
}

.calendar-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.calendar-header-day {
  text-align: center;
  font-weight: 600;
  color: #666;
  font-size: 12px;
  padding: 8px 0;
}

.calendar-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  position: relative;
}

.calendar-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
  border: none;
}

.calendar-cell:hover:not(.past):not(.unavailable) {
  background: #e9ecef;
  transform: scale(1.1);
}

.day-booking .calendar-cell.selected {
  background: #000000;
  color: white;
}

.night-booking .calendar-cell.available {
  background: #219672;
  color: white;
}

.night-booking .calendar-cell.available.morning-availability:not(.night-availability) {
  background: linear-gradient(to bottom right, #219672 0%, #219672 50%, #B33D43 50%, #B33D43 100%);
}

.night-booking .calendar-cell.available.night-availability:not(.morning-availability) {
  background: linear-gradient(to bottom right, #B33D43 0%, #B33D43 50%, #219672 50%, #219672 100%);
}

.night-booking .calendar-cell.available.morning-availability:not(.night-availability).other-suite-night {
  background: linear-gradient(to bottom right, #219672 0%, #219672 50%, #AD8E62 50%, #AD8E62 100%);
}

.night-booking .calendar-cell.available.night-availability:not(.morning-availability).other-suite-morning {
  background: linear-gradient(to bottom right, #AD8E62 0%, #AD8E62 50%, #219672 50%, #219672 100%);
}

.night-booking .calendar-cell.unavailable.other-suite-morning:not(.other-suite-night) {
  background: linear-gradient(to bottom right, #AD8E62 0%, #AD8E62 50%, #B33D43 50%, #B33D43 100%);
  cursor: pointer; /* Ensure night booking golden cells are clickable */
}

.night-booking .calendar-cell.unavailable.other-suite-night:not(.other-suite-morning) {
  background: linear-gradient(to bottom right, #B33D43 0%, #B33D43 50%, #AD8E62 50%, #AD8E62 100%);
  cursor: pointer; /* Ensure night booking golden cells are clickable */
}


.night-booking .calendar-cell.available.morning-availability,
.night-booking .calendar-cell.available.night-availability {
  color: white;
}

.night-booking .calendar-cell.selected,
.night-booking .calendar-cell.selected-start,
.night-booking .calendar-cell.selected-end {
  background: #ffffff !important;
  color: #000000 !important;
}

.night-booking .calendar-cell.selected .date-number,
.night-booking .calendar-cell.selected-start .date-number,
.night-booking .calendar-cell.selected-end .date-number {
  color: #000000 !important;
}



.calendar-cell.past,
.calendar-cell.unavailable {
  background: #f8f9fa;
  color: #ccc;
  cursor: not-allowed;
}

.calendar-cell.other-month {
  opacity: 0.4;
}

.calendar-cell.available {
  background: #219672; /* Green background */
  color: white; /* White text */
  border-color: #219672; /* Green border */
}


.calendar-cell.partially-available {
  background: #AD8E62; /* Tan/beige background for suite-specific unavailability */
  color: white; /* White text */
  border-color: #AD8E62; /* Tan/beige border */
  cursor: pointer; /* Ensure golden cells are clickable */
}

.calendar-cell.unavailable {
  background: #B33D43; /* Red background */
  border-color: #f5c6cb; /* Red border */
}

.night-booking .calendar-cell.unavailable.other-suite-available {
  background: #AD8E62;
  border-color: #AD8E62;
  color: white;
  cursor: pointer; /* Ensure night booking golden cells are clickable */
}

.calendar-cell.unavailable .date-number {
  color: white;
  opacity: 0.50;
}

.night-booking .calendar-cell.unavailable.other-suite-available .date-number {
  color: white;
  opacity: 1;
}



/* Loading overlay covers entire two-month calendar */
.two-month-calendar > .calendar-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 8px;
  backdrop-filter: blur(2px);
}

/* Make cells transparent/neutral when loading */
.two-month-calendar:has(.calendar-loading-overlay) .calendar-cell.available,
.two-month-calendar:has(.calendar-loading-overlay) .calendar-cell.unavailable {
  background: transparent !important;
  color: #666 !important;
  border-color: transparent !important;
}


.date-number {
  font-size: 14px;
  font-weight: 500;
  color: white;
  position: relative;
  z-index: 2;
}

.selection-summary {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.selection-summary p {
  margin: 8px 0;
  color: #666;
}

/* Calendar Legend */
.calendar-legend {
  display: flex;
  justify-content: flex-start;
  gap: 24px;
  margin-top: 20px;
  padding: 12px 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  flex-shrink: 0;
}

.legend-available {
  background: #219672;
}

.legend-unavailable {
  background: #B33D43;
}

.legend-other-suites {
  background: #AD8E62;
}

.legend-label {
  font-size: 13px;
  color: #555;
}

.calendar-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.clear-dates-link {
  background: none;
  border: none;
  color: #333;
  text-decoration: underline;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  transition: color 0.3s ease;
}

.clear-dates-link:hover {
  color: #007bff;
}

.confirm-dates-btn {
  background: #219672;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s ease;
}

.confirm-dates-btn:hover:not(:disabled) {
  background: #1a7559;
}

.confirm-dates-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .calendar-selector {
    max-width: 100%;
  }

  .calendar-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .calendar-right {
    width: 100%;
  }

  .calendar-grid {
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
  }

  .calendar-day {
    padding: 8px;
  }

  .day-number {
    font-size: 14px;
  }

  .day-name {
    font-size: 10px;
  }

  .date-inputs {
    flex-direction: column;
    gap: 15px;
  }

  .calendar-footer {
    flex-direction: column;
    gap: 20px;
    align-items: center;
  }

  .legend {
    justify-content: center;
  }

  .calendar-legend {
    flex-wrap: wrap;
    gap: 12px 20px;
  }

  .legend-label {
    font-size: 12px;
  }

  /* Responsive calendar */
  .two-month-calendar {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .month-header {
    gap: 10px;
  }

  .month-header h4 {
    font-size: 14px;
  }

  .month-calendar {
    padding: 15px;
  }

  .calendar-cell {
    min-height: 35px;
  }

  .date-number {
    font-size: 12px;
  }

  .nav-btn {
    width: 25px;
    height: 25px;
    font-size: 18px;
  }
}
</style>
