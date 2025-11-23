<template>
  <div class="time-selector">
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
                v-for="time in arrivalTimes" 
                :key="time" 
                :value="time"
                :disabled="isArrivalTimeDisabled(time)"
              >
                {{ time }}{{ isArrivalTimeDisabled(time) ? ' (No slots available)' : '' }}
              </option>
            </select>
          </div>
          <div class="detail-row">
            <div class="detail-label">DEPARTURE</div>
            <select v-model="selectedDeparture" class="time-select">
              <option value="">Select</option>
              <option 
                v-for="time in departureTimes" 
                :key="time" 
                :value="time"
                :disabled="isDepartureTimeDisabled(time)"
              >
                {{ time }}{{ isDepartureTimeDisabled(time) ? ' (No slots available)' : '' }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="validationMessage" class="validation-message">
          {{ validationMessage }}
        </div>

        <!-- Pricing display for preselected suite -->
        <div v-if="selectedSuite && canBook" class="pricing-display">
          <div v-if="pricingLoading" class="pricing-loading">
            <div class="pricing-spinner"></div>
            <span>Calculating...</span>
          </div>
          <div v-else-if="pricingInfo && pricingInfo.total !== 'N/A'" class="pricing-content">
            <div class="pricing-amount">{{ pricingInfo.total }}€</div>
            <div v-if="pricingInfo.calculation" class="pricing-calculation">{{ pricingInfo.calculation }}</div>
          </div>
          <div v-else class="pricing-unavailable">
            Pricing unavailable
          </div>
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

        <!-- Pricing display for preselected suite -->
        <div v-if="selectedSuite && canBook" class="pricing-display">
          <div v-if="pricingLoading" class="pricing-loading">
            <div class="pricing-spinner"></div>
            <span>Calculating...</span>
          </div>
          <div v-else-if="pricingInfo && pricingInfo.total !== 'N/A'" class="pricing-content">
            <div class="pricing-amount">{{ pricingInfo.total }}€</div>
            <div v-if="pricingInfo.calculation" class="pricing-calculation">{{ pricingInfo.calculation }}</div>
          </div>
          <div v-else class="pricing-unavailable">
            Pricing unavailable
          </div>
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
      limitsLoaded: false,
      pricingLoading: false
    }
  },
  computed: {
    canBook() {
      if (this.bookingType === 'day') {
        const hasSelection = this.selectedDate && this.selectedArrival && this.selectedDeparture && this.limitsLoaded
        const duration = this.calculateHours()
        const isValidDuration = duration >= this.bookingLimits.day_min_hours && duration <= this.bookingLimits.day_max_hours
        return hasSelection && isValidDuration
      } else {
        return this.selectedDates.start && this.selectedDates.end
      }
    },
    validationMessage() {
      if (this.bookingType === 'day' && this.selectedArrival && this.selectedDeparture && this.limitsLoaded) {
        const duration = this.calculateHours()
        if (duration < this.bookingLimits.day_min_hours) {
          return `Durée minimum: ${this.bookingLimits.day_min_hours} heures`
        } else if (duration > this.bookingLimits.day_max_hours) {
          return `Durée maximum: ${this.bookingLimits.day_max_hours} heures`
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
        selectedDates: this.selectedDates
      })

      if (!this.selectedSuite || !this.suitePricing) {
        console.log('TimeSelector: Missing selectedSuite or suitePricing, returning null')
        return null
      }

      const startDate = this.bookingType === 'day' ? this.selectedDate : this.selectedDates.start
      const endDate = this.bookingType === 'day' ? this.selectedDate : this.selectedDates.end

      console.log('TimeSelector: startDate and endDate:', { startDate, endDate })

      if (!startDate || !endDate) {
        console.log('TimeSelector: Missing startDate or endDate, returning null')
        return null
      }

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
      handler() {
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
        // Set loading state when pricing data changes
        this.pricingLoading = Object.keys(newVal || {}).length === 0
      },
      deep: true,
      immediate: true
    },
    selectedSuite: {
      handler(newVal, oldVal) {
        console.log('TimeSelector selectedSuite changed:', { newVal, oldVal })
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
        const response = await fetch('/intense_experience-api/booking-limits')
        const data = await response.json()
        if (data.status === 'success' && data.booking_limits) {
          this.bookingLimits = data.booking_limits
          this.arrivalTimes = data.arrival_times || []
          this.departureTimes = data.departure_times || []
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
        return false
      }

      // If a specific suite is selected, only check that suite
      if (this.selectedSuite) {
        const suiteId = this.selectedSuite.Id
        const slots = this.dateAvailability.suite_availability[suiteId]
        if (!slots) {
          return true
        }

        // If no arrival time selected, check if this departure time is used in any available slot for this suite
        if (!this.selectedArrival) {
          const hasSlotWithThisDeparture = slots.some(slot => slot.departure === departureTime)
          return !hasSlotWithThisDeparture
        }

        // If arrival time is selected, check if this combination is available for this suite
        const hasMatchingSlot = slots.some(slot =>
          slot.arrival === this.selectedArrival && slot.departure === departureTime
        )
        return !hasMatchingSlot
      }

      // If no suite is selected, check across all suites

      // If no arrival time selected, check if this departure time is used in any available slot
      if (!this.selectedArrival) {
        for (const suiteId in this.dateAvailability.suite_availability) {
          const slots = this.dateAvailability.suite_availability[suiteId]
          const hasSlotWithThisDeparture = slots.some(slot => slot.departure === departureTime)
          if (hasSlotWithThisDeparture) {
            return false
          }
        }
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
          // For nuitée, take the first price (daily rate) and multiply by number of nights
          const numberOfNights = this.calculateNights()
          console.log('TimeSelector nuitée calculation:', {
            nightlyRate: suitePricing.Prices[0],
            numberOfNights
          })

          return {
            total: suitePricing.Prices[0] * numberOfNights,
            calculation: `${suitePricing.Prices[0]}€ × ${numberOfNights} nuits`
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
  padding: 30px 20px;
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
  background: rgba(201, 169, 97, 0.1);
  border: 1px solid rgba(201, 169, 97, 0.3);
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
  text-align: center;
}

.pricing-amount {
  font-size: 24px;
  font-weight: bold;
  color: #c9a961;
  margin-bottom: 5px;
}

.pricing-calculation {
  font-size: 14px;
  color: #999;
  font-style: italic;
}

.pricing-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c9a961;
  font-style: italic;
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
  text-align: center;
}

/* Responsive */
@media (max-width: 768px) {
  .summary-box {
    padding: 20px 15px;
  }

  .pricing-display {
    padding: 12px;
    margin: 12px 0;
  }

  .pricing-amount {
    font-size: 20px;
  }

  .pricing-calculation {
    font-size: 12px;
  }
}
</style>
