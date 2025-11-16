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

        <button class="book-btn" :disabled="!canBook" @click="bookSuite">BOOK A SUITE</button>
        <div class="no-charge-text">You won't be charget yet</div>
        <!-- Debug info -->
        <div style="font-size: 10px; color: #666; margin-top: 10px;">
          Debug: Date: {{ !!selectedDate }} | Arrival: {{ !!selectedArrival }} ({{ selectedArrival }}) | Departure: {{ !!selectedDeparture }} ({{ selectedDeparture }}) | Hours: {{ calculateHours() }} | Limits: {{ bookingLimits.day_min_hours }}-{{ bookingLimits.day_max_hours }} (loaded: {{ limitsLoaded }}) | canBook: {{ canBook }} | validation: {{ validationMessage }}
        </div>
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

        <button class="book-btn" :disabled="!canBook" @click="bookSuite">BOOK A SUITE</button>
        <div class="no-charge-text">You won't be charget yet</div>
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
      limitsLoaded: false
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
    }
  },
  mounted() {
    this.fetchBookingLimits()
  },
  watch: {
    selectedArrival() {
      this.emitTimeSelection()
    },
    selectedDeparture() {
      this.emitTimeSelection()
    },
    dateAvailability: {
      handler(newVal) {
        console.log('Date availability updated:', newVal)
        // Reset selections if currently selected times are now unavailable
        if (this.selectedArrival && this.isArrivalTimeDisabled(this.selectedArrival)) {
          this.selectedArrival = ''
        }
        if (this.selectedDeparture && this.isDepartureTimeDisabled(this.selectedDeparture)) {
          this.selectedDeparture = ''
        }
      },
      deep: true
    }
  },
  methods: {
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
      return new Date(date).toLocaleDateString('en-GB')
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
      console.log('Book suite clicked', {
        canBook: this.canBook,
        selectedDate: this.selectedDate,
        selectedArrival: this.selectedArrival,
        selectedDeparture: this.selectedDeparture
      })
      
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
      if (this.bookingType !== 'day' || !this.dateAvailability || !this.dateAvailability.suite_availability) {
        return false
      }

      // Check if there's at least one suite with at least one available slot starting at this arrival time
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
    }
  }
}
</script>

<style scoped>
.time-selector {
  width: 100%;
}

.summary-box {
  background: #2d2d2d;
  color: white;
  padding: 30px 20px;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Details Section */
.details-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 11px;
  letter-spacing: 1px;
  color: #999;
  text-transform: uppercase;
}

.detail-value {
  font-size: 16px;
  color: white;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.time-select {
  background: transparent;
  color: white;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 10px 0;
  font-size: 16px;
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23999' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right center;
  padding-right: 20px;
}

.time-select option {
  background: #2d2d2d;
  color: white;
}

.time-select option:disabled {
  color: #666;
  font-style: italic;
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

/* Responsive */
@media (max-width: 768px) {
  .summary-box {
    padding: 20px 15px;
  }
}
</style>
