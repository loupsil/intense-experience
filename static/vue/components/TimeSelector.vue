<template>
  <div class="time-selector">
    <!-- Pricing display for preselected suite -->
    <div v-if="selectedSuite" class="pricing-display">
      <div class="pricing-header">TOTAL</div>
      <div v-if="pricingLoading" class="pricing-loading">
        <div class="pricing-spinner"></div>
      </div>
      <div v-else-if="canBook && pricingInfo && pricingInfo.total !== 'N/A'" class="pricing-details">{{ pricingInfo.total }}€ <span v-if="pricingInfo.calculation" class="pricing-calculation">({{ pricingInfo.calculation }})</span></div>
      <div v-else-if="!canBook" class="pricing-details pricing-details-italic">Select dates & times</div>
      <div v-else class="pricing-details">Pricing unavailable</div>
    </div>
    <!-- Message when no suite is selected -->
    <div v-else class="pricing-display no-suite-message">
      <div class="pricing-header">SUITE</div>
      <div class="pricing-details pricing-details-italic">You'll choose a suite in the next steps</div>
    </div>

    <!-- Day Booking: Time Selection -->
    <div v-if="bookingType === 'day'" class="time-selection">
      <div class="summary-box">
        <div class="details-section">
          <div class="detail-row">
            <div class="detail-label">DATE</div>
            <div class="detail-value">{{ formatDateShort(selectedDate) }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">ARRIVAL</div>
            <select v-model="selectedArrival" class="time-select">
              <option value="">Select</option>
              <option
                v-for="time in availableArrivalTimes"
                :key="time"
                :value="time"
              >
                {{ time }}
              </option>
            </select>
          </div>
          <div class="detail-row">
            <div class="detail-label">DEPARTURE</div>
            <select v-model="selectedDeparture" class="time-select">
              <option value="">Select</option>
              <option
                v-for="time in availableDepartureTimes"
                :key="time"
                :value="time"
              >
                {{ time }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="validationMessage" class="validation-message">
          {{ validationMessage }}
        </div>

        <button class="book-btn" :disabled="!canBook" @click="bookSuite">BOOK A SUITE</button>
        <div class="no-charge-text">You won't be charged yet</div>
      </div>
    </div>

    <!-- Night Booking: Date Confirmation -->
    <div v-if="bookingType === 'night'" class="date-confirmation">
      <div class="summary-box">
        <div class="details-section">
          <div class="detail-row">
            <div class="detail-label">CHECK IN</div>
            <div class="detail-value">{{ formatDateShort(selectedDates.start) || 'Select date' }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">CHECK OUT</div>
            <div class="detail-value">{{ formatDateShort(selectedDates.end) || 'Select date' }}</div>
          </div>
        </div>

        <div v-if="validationMessage" class="validation-message">
          {{ validationMessage }}
        </div>

        <button class="book-btn" :disabled="!canBook" @click="bookSuite">BOOK A SUITE</button>
        <div class="no-charge-text">You won't be charged yet</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TimeSelector',
  props: {
    bookingType: {
      type: String,
      required: true,
      validator: value => ['day', 'night'].includes(value)
    },
    selectedDate: {
      type: [Date, Object],
      default: null
    },
    selectedDates: {
      type: Object,
      default: () => ({ start: null, end: null })
    },
    dateAvailability: {
      type: Object,
      default: null
    },
    service: {
      type: Object,
      default: null
    },
    selectedSuite: {
      type: Object,
      default: null
    },
    suitePricing: {
      type: Object,
      default: () => ({})
    },
    priceDisplayCalculator: {
      type: Function,
      default: null
    }
  },
  data() {
    return {
      selectedArrival: '',
      selectedDeparture: '',
      arrivalTimes: [],
      departureTimes: [],
      bookingLimits: {
        day_min_hours: null,
        day_max_hours: null
      },
      specialMinDurationSuites: [],
      specialMinHours: null,
      limitsLoaded: false,
      pricingLoading: false
    }
  },
  computed: {
    effectiveMinHours() {
      // Use special minimum hours if the selected suite is in the special list
      if (this.selectedSuite && this.specialMinDurationSuites.includes(this.selectedSuite.Id)) {
        return this.specialMinHours || this.bookingLimits.day_min_hours
      }
      return this.bookingLimits.day_min_hours
    },
    
    canBook() {
      if (this.bookingType === 'day') {
        const hasSelection = this.selectedDate && this.selectedArrival && this.selectedDeparture && this.limitsLoaded
        const duration = this.calculateHours()
        const isValidDuration = duration >= this.effectiveMinHours && duration <= this.bookingLimits.day_max_hours
        return hasSelection && isValidDuration
      } else {
        // For night bookings, check that dates are selected and number of nights doesn't exceed 2
        const hasDates = this.selectedDates.start && this.selectedDates.end
        const isValidNights = this.calculateNights() <= 2
        return hasDates && isValidNights
      }
    },

    availableArrivalTimes() {
      return this.arrivalTimes.filter(time => !this.isArrivalTimeDisabled(time))
    },

    availableDepartureTimes() {
      return this.departureTimes.filter(time => !this.isDepartureTimeDisabled(time))
    },
    validationMessage() {
      if (this.bookingType === 'day' && this.selectedArrival && this.selectedDeparture && this.limitsLoaded) {
        const duration = this.calculateHours()
        if (duration < this.effectiveMinHours) {
          return `Minimum duration: ${this.effectiveMinHours} hours`
        } else if (duration > this.bookingLimits.day_max_hours) {
          return `Maximum duration: ${this.bookingLimits.day_max_hours} hours`
        }
      } else if (this.bookingType === 'night' && this.selectedDates.start && this.selectedDates.end) {
        const nights = this.calculateNights()
        if (nights > 2) {
          return `Maximum 2 nights`
        }
      }
      return null
    },
    pricingInfo() {
      console.log('TimeSelector pricingInfo computed:', {
        selectedSuite: this.selectedSuite,
        suitePricing: this.suitePricing,
        bookingType: this.bookingType,
        selectedDate: this.selectedDate,
        selectedDates: this.selectedDates,
        selectedArrival: this.selectedArrival,
        selectedDeparture: this.selectedDeparture
      })

      if (!this.selectedSuite || !this.suitePricing) {
        console.log('TimeSelector: Missing selectedSuite or suitePricing, returning null')
        return null
      }

      let startDate, endDate

      if (this.bookingType === 'day') {
        // For day bookings, only calculate pricing when date and times are selected
        if (!this.selectedDate || !this.selectedArrival || !this.selectedDeparture) {
          console.log('TimeSelector: Missing date or times for day booking, returning null')
          return null
        }

        // Create Date objects with the selected times
        const baseDate = new Date(this.selectedDate)
        baseDate.setHours(0, 0, 0, 0)

        const [arrHours, arrMinutes] = this.selectedArrival.split(':')
        startDate = new Date(baseDate)
        startDate.setHours(parseInt(arrHours), parseInt(arrMinutes), 0, 0)

        const [depHours, depMinutes] = this.selectedDeparture.split(':')
        endDate = new Date(baseDate)
        endDate.setHours(parseInt(depHours), parseInt(depMinutes), 0, 0)
      } else {
        // For night bookings, use the selectedDates
        startDate = this.selectedDates.start
        endDate = this.selectedDates.end

        if (!startDate || !endDate) {
          console.log('TimeSelector: Missing startDate or endDate for night booking, returning null')
          return null
        }
      }

      console.log('TimeSelector: calculated startDate and endDate:', { startDate, endDate })

      const result = this.calculateSuitePricingFromData(this.suitePricing, startDate, endDate)
      console.log('TimeSelector: calculateSuitePricingFromData result:', result)

      // Update loading state based on result
      this.pricingLoading = result.total === 'N/A'

      return result
    }
  },
  mounted() {
    console.log('TimeSelector mounted with props:', {
      selectedSuite: this.selectedSuite,
      suitePricing: this.suitePricing,
      bookingType: this.bookingType,
      service: this.service
    })
    this.fetchBookingLimits()
    this.$nextTick(() => {
      this.updateBackgroundColors()
    })
  },
  watch: {
    bookingType() {
      this.$nextTick(() => {
        this.updateBackgroundColors()
      })
    },
    selectedArrival() {
      this.emitTimeSelection()
    },
    selectedDeparture() {
      this.emitTimeSelection()
    },
    selectedDate: {
      handler(newVal) {
        console.log('TimeSelector selectedDate watcher:', { 
          newVal, 
          selectedSuite: this.selectedSuite,
          dateAvailability: this.dateAvailability
        })
        
        // Reset selections if currently selected times are now unavailable
        if (this.selectedArrival && this.isArrivalTimeDisabled(this.selectedArrival)) {
          this.selectedArrival = ''
        }
        if (this.selectedDeparture && this.isDepartureTimeDisabled(this.selectedDeparture)) {
          this.selectedDeparture = ''
        }
      },
      immediate: true
    },
      dateAvailability: {
      handler() {
        // Reset selections if currently selected times are now unavailable
        if (this.selectedArrival && this.isArrivalTimeDisabled(this.selectedArrival)) {
          this.selectedArrival = ''
        }
        if (this.selectedDeparture && this.isDepartureTimeDisabled(this.selectedDeparture)) {
          this.selectedDeparture = ''
        }
      },
      deep: true,
      immediate: true
    },
    suitePricing: {
      handler(newVal, oldVal) {
        console.log('TimeSelector suitePricing changed:', { newVal, oldVal })
        // Only set loading to false when pricing data becomes available
        // Loading state is managed by pricingInfo computed property
        if (Object.keys(newVal || {}).length > 0) {
          this.pricingLoading = false
        }
      },
      deep: true,
      immediate: true
    },
    selectedSuite: {
      handler(newVal, oldVal) {
        console.log('TimeSelector selectedSuite changed:', { newVal, oldVal })
        // Refetch booking limits when suite changes to get suite-specific minimum duration
        if (newVal && newVal.Id !== oldVal?.Id) {
          this.fetchBookingLimits()
        }
      },
      immediate: true
    },
    selectedDates: {
      handler(newVal, oldVal) {
        console.log('TimeSelector selectedDates changed:', { newVal, oldVal })
      },
      deep: true,
      immediate: true
    },
    selectedDate: {
      handler(newVal, oldVal) {
        console.log('TimeSelector selectedDate changed:', { newVal, oldVal })
      },
      immediate: true
    }
  },
  methods: {
    updateBackgroundColors() {
      // Check if component is mounted and $el exists
      if (!this.$el || !this.$el.style) {
        return
      }
      
      if (this.bookingType === 'night') {
        // Sets the CSS custom property (CSS variable) '--timeselector-background' to a dark color (#161616)
        this.$el.style.setProperty('--timeselector-background', '#161616')
      } else if (this.bookingType === 'day') {
        this.$el.style.setProperty('--timeselector-background', '#E9E9DF')
      }
    },

    async fetchBookingLimits() {
      try {
        // Include suite_id in the request if available
        let url = '/intense_experience-api/booking-limits'
        if (this.selectedSuite && this.selectedSuite.Id) {
          url += `?suite_id=${encodeURIComponent(this.selectedSuite.Id)}`
        }

        const response = await fetch(url)
        const data = await response.json()

        if (data.status === 'success' && data.booking_limits) {
          this.bookingLimits = data.booking_limits
          this.arrivalTimes = data.arrival_times || []
          this.departureTimes = data.departure_times || []
          this.specialMinDurationSuites = data.special_min_duration_suites || []
          this.specialMinHours = data.special_min_hours || null
          this.limitsLoaded = true
        }
      } catch (error) {
        console.error('Failed to fetch booking limits from backend:', error)
        this.limitsLoaded = false
      }
    },
    emitTimeSelection() {
      if (this.selectedArrival && this.selectedDeparture) {
        this.$emit('time-selected', {
          arrival: this.selectedArrival,
          departure: this.selectedDeparture,
          date: this.selectedDate
        })
      }
    },

    formatDateShort(date) {
      if (!date) return ''
      const d = new Date(date)
      return d.toLocaleDateString('en-GB', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
      })
    },

    calculateNights() {
      if (!this.selectedDates.start || !this.selectedDates.end) return 0
      const diffTime = Math.abs(new Date(this.selectedDates.end) - new Date(this.selectedDates.start))
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    },

    calculateHours() {
      if (!this.selectedArrival || !this.selectedDeparture) return 0
      const [arrHour] = this.selectedArrival.split(':').map(Number)
      const [depHour] = this.selectedDeparture.split(':').map(Number)
      return Math.max(0, depHour - arrHour)
    },

    bookSuite() {
      if (!this.canBook) return
      
      this.$emit('book-suite', {
        bookingType: this.bookingType,
        arrival: this.selectedArrival,
        departure: this.selectedDeparture,
        date: this.selectedDate,
        dates: this.selectedDates
      })
    },

    isArrivalTimeDisabled(arrivalTime) {
      if (this.bookingType !== 'day') {
        return false
      }

      if (!this.dateAvailability?.suite_availability) {
        return false
      }

      // If a specific suite is selected, only check that suite
      if (this.selectedSuite) {
        const suiteId = this.selectedSuite.Id
        const slots = this.dateAvailability.suite_availability[suiteId]
        if (!slots) {
          return true
        }
        const hasSlotWithThisArrival = slots.some(slot => slot.arrival === arrivalTime)
        return !hasSlotWithThisArrival
      }

      // If no suite is selected, check if there's at least one suite with at least one available slot starting at this arrival time
      for (const suiteId in this.dateAvailability.suite_availability) {
        const slots = this.dateAvailability.suite_availability[suiteId]
        const hasSlotWithThisArrival = slots.some(slot => slot.arrival === arrivalTime)
        if (hasSlotWithThisArrival) {
          return false // At least one slot available with this arrival time
        }
      }

      return true // No slots available with this arrival time
    },

    isDepartureTimeDisabled(departureTime) {
      if (this.bookingType !== 'day' || !this.dateAvailability || !this.dateAvailability.suite_availability) {
        console.log('isDepartureTimeDisabled early return:', { bookingType: this.bookingType, hasDateAvailability: !!this.dateAvailability })
        return false
      }

      // If a specific suite is selected, only check that suite
      if (this.selectedSuite) {
        const suiteId = this.selectedSuite.Id
        const slots = this.dateAvailability.suite_availability[suiteId]
        
        console.log('isDepartureTimeDisabled for suite:', {
          suiteId,
          departureTime,
          hasSlots: !!slots,
          slotsCount: slots?.length,
          selectedArrival: this.selectedArrival,
          effectiveMinHours: this.effectiveMinHours
        })
        
        if (!slots) {
          return true
        }

        // If no arrival time selected, check if this departure time is used in any available slot for this suite
        if (!this.selectedArrival) {
          const hasSlotWithThisDeparture = slots.some(slot => slot.departure === departureTime)
          console.log('No arrival selected, checking departure:', { departureTime, hasSlotWithThisDeparture })
          return !hasSlotWithThisDeparture
        }

        // If arrival time is selected, check if this combination is available AND meets duration requirements
        const hasMatchingSlot = slots.some(slot =>
          slot.arrival === this.selectedArrival && slot.departure === departureTime
        )
        
        console.log('Checking slot availability:', { 
          arrival: this.selectedArrival, 
          departure: departureTime, 
          hasMatchingSlot,
          allSlots: slots 
        })
        
        if (!hasMatchingSlot) {
          return true // Combination not available
        }

        // Additional duration check when arrival is selected
        if (this.limitsLoaded) {
          const [arrHour] = this.selectedArrival.split(':').map(Number)
          const [depHour] = departureTime.split(':').map(Number)
          const duration = Math.max(0, depHour - arrHour)

          console.log('Duration check:', { duration, effectiveMinHours: this.effectiveMinHours })

          // Disable if duration is less than the effective minimum hours
          if (duration < this.effectiveMinHours) {
            return true
          }
        }

        return false // Combination is available and meets duration requirements
      }

      // If no suite is selected, check across all suites
      console.log('No suite selected, checking across all suites:', {
        availabilitySuites: Object.keys(this.dateAvailability.suite_availability),
        selectedArrival: this.selectedArrival,
        departureTime
      })

      // If no arrival time selected, check if this departure time is used in any available slot
      if (!this.selectedArrival) {
        for (const suiteId in this.dateAvailability.suite_availability) {
          const slots = this.dateAvailability.suite_availability[suiteId]
          const hasSlotWithThisDeparture = slots.some(slot => slot.departure === departureTime)
          console.log('Checking suite for departure:', { suiteId, departureTime, hasSlotWithThisDeparture, slotsCount: slots.length })
          if (hasSlotWithThisDeparture) {
            return false
          }
        }
        console.log('No suite has this departure time available')
        return true
      }

      // If arrival time is selected, check if this combination is available
      for (const suiteId in this.dateAvailability.suite_availability) {
        const slots = this.dateAvailability.suite_availability[suiteId]
        const hasMatchingSlot = slots.some(slot =>
          slot.arrival === this.selectedArrival && slot.departure === departureTime
        )
        if (hasMatchingSlot) {
          return false // This combination is available
        }
      }

      return true // This combination is not available
    },

    calculateSuitePricingFromData(pricing, startDate, endDate, suite = null) {
      console.log('TimeSelector calculateSuitePricingFromData called with:', {
        pricing,
        startDate,
        endDate,
        suite,
        selectedSuite: this.selectedSuite,
        service: this.service
      })

      const targetSuite = suite || this.selectedSuite
      console.log('TimeSelector targetSuite:', targetSuite)

      if (!targetSuite || !pricing) {
        console.log('TimeSelector: No targetSuite or pricing, returning N/A')
        return {
          total: 'N/A',
          calculation: ''
        }
      }

      // Get pricing for the selected suite
      const suitePricing = pricing[targetSuite.Id]
      console.log('TimeSelector suitePricing for targetSuite.Id:', {
        suiteId: targetSuite.Id,
        suitePricing,
        pricingKeys: Object.keys(pricing),
        fullPricingObject: pricing
      })

      // Log all available suite IDs in pricing for comparison
      const availableSuiteIds = Object.keys(pricing)
      console.log('TimeSelector: Available suite IDs in pricing:', availableSuiteIds)
      console.log('TimeSelector: Looking for suite ID match:', targetSuite.Id, 'in', availableSuiteIds)

      if (suitePricing && suitePricing.Prices && suitePricing.Prices.length > 0) {
        const serviceType = this.service?.Id === '86fcc6a7-75ce-457a-a425-b3850108b6bf' ? 'journée' : 'nuitée'
        console.log('TimeSelector serviceType:', serviceType)

        // For journée: sum all hourly prices, for nuitée: take the first (daily) price
        if (serviceType === 'journée') {
          const total = suitePricing.Prices.reduce((sum, price) => sum + price, 0)
          const hours = suitePricing.Prices.length
          const hourlyRate = suitePricing.Prices[0]

          // For time-based bookings, the number of hours should be hours - 1
          // because the API includes both start and end boundaries
          const actualHours = hours - 1
          const correctedTotal = actualHours * hourlyRate

          console.log('TimeSelector journée calculation:', {
            total,
            hours,
            hourlyRate,
            actualHours,
            correctedTotal
          })

          return {
            total: correctedTotal,
            calculation: `${hourlyRate}€ × ${actualHours}h`
          }
        } else {
          // For nuitée, use shared pricing calculation logic
          if (this.priceDisplayCalculator) {
            const result = this.priceDisplayCalculator(suitePricing, startDate, endDate)
            console.log('TimeSelector nuitée calculation using shared logic:', result)
            return result
          } else {
            // Fallback to local logic if shared calculator not available
            const numberOfNights = this.calculateNights()
            console.log('TimeSelector nuitée calculation (fallback):', {
              nightlyRate: suitePricing.Prices[0],
              numberOfNights
            })

            return {
              total: suitePricing.Prices[0] * numberOfNights,
              calculation: `${suitePricing.Prices[0]}€ × ${numberOfNights} nights`
            }
          }
        }
      } else {
        console.log('TimeSelector: No pricing data available for suite')
        // No pricing data available
        return {
          total: 'N/A',
          calculation: ''
        }
      }
    }
  }
}
</script>

<style scoped>
.time-selector {
  width: 100%;
  background: var(--timeselector-background, #2d2d2d);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.summary-box {
  background: var(--timeselector-background, #2d2d2d);
  color: white;
  padding: 20px 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Details Section */
.details-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
  padding-bottom: 20px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

/* Side by side layout for time/date fields */
.time-selection .details-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.time-selection .details-section .detail-row:first-child {
  grid-column: 1 / -1;
}

.time-selection .details-section .detail-row:nth-child(2),
.time-selection .details-section .detail-row:nth-child(3) {
  display: inline-block;
}

/* Night booking - side by side layout */
.date-confirmation .details-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (min-width: 768px) {
  .time-selection .details-section {
    grid-template-columns: 1fr 1fr;
  }
}

.detail-label {
  font-size: 11px;
  letter-spacing: 1px;
  color: #999;
  text-transform: uppercase;
}

.detail-value {
  font-size: 16px;
  color: #333;
  padding: 10px 0;
  border-bottom: 1px solid rgba(51, 51, 51, 0.2);
}

.time-select {
  width: 100%;
  background: transparent;
  color: #333;
  border: none;
  border-bottom: 1px solid rgba(51, 51, 51, 0.2);
  padding: 10px 0;
  font-size: 16px;
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right center;
  padding-right: 20px;
}

.time-select option {
  background: #E9E9DF;
  color: #333;
}

.time-select option:disabled {
  color: #999;
  font-style: italic;
}

/* Night booking styles */
.date-confirmation .detail-value {
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

/* Book Button */
.book-btn {
  background: #c9a961;
  color: white;
  border: none;
  padding: 15px;
  font-size: 14px;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.3s ease;
  margin-top: 10px;
}

.book-btn:hover:not(:disabled) {
  background: #b89851;
}

.book-btn:disabled {
  background: #666;
  cursor: not-allowed;
  opacity: 0.5;
}

.validation-message {
  color: #ff6b6b;
  font-size: 13px;
  text-align: center;
  margin: 10px 0;
  font-weight: 500;
}

.no-charge-text {
  text-align: center;
  font-size: 13px;
  color: #999;
  margin-top: 10px;
}

/* Pricing Display */
.pricing-display {
  border-bottom: 1px solid rgba(51, 51, 51, 0.2);
  padding: 20px 20px 10px 20px;
  text-align: left;
}

.pricing-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pricing-header {
  font-size: 11px;
  letter-spacing: 1px;
  color: #999;
  text-transform: uppercase;
  margin: 0;
}

.pricing-details {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 24px;
  font-weight: 600;
}

.pricing-details-italic {
  font-style: italic;
  color: #999;
  font-size: 16px;
  font-weight: normal;
}

.pricing-amount {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.pricing-calculation {
  font-size: 12px;
  color: #999;
  font-style: italic;
}

.pricing-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 32px;
}

.pricing-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #c9a961;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: pricing-spin 1s linear infinite;
}

@keyframes pricing-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.pricing-unavailable {
  color: #999;
  font-style: italic;
  font-size: 12px;
}

/* Responsive */
@media (max-width: 768px) {
  .summary-box {
    padding: 20px 15px;
  }

  .pricing-display {
    padding: 15px 15px 12px 15px;
    margin-bottom: 15px;
  }

  .pricing-header {
    font-size: 10px;
  }

  .pricing-details {
    font-size: 20px;
  }

  .pricing-details-italic {
    font-size: 14px;
  }

  .pricing-calculation {
    font-size: 11px;
  }
}
</style>
