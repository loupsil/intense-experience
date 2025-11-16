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
              <option v-for="time in arrivalTimes" :key="time" :value="time">{{ time }}</option>
            </select>
          </div>
          <div class="detail-row">
            <div class="detail-label">DEPARTURE</div>
            <select v-model="selectedDeparture" class="time-select">
              <option value="">Select</option>
              <option v-for="time in departureTimes" :key="time" :value="time">{{ time }}</option>
            </select>
          </div>
        </div>

        <button class="book-btn" :disabled="!canBook" @click="bookSuite">BOOK A SUITE</button>
        <div class="no-charge-text">You won't be charget yet</div>
        <!-- Debug info -->
        <div style="font-size: 10px; color: #666; margin-top: 10px;">
          Debug: Date: {{ !!selectedDate }} | Arrival: {{ !!selectedArrival }} ({{ selectedArrival }}) | Departure: {{ !!selectedDeparture }} ({{ selectedDeparture }}) | canBook: {{ canBook }}
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
    }
  },
  data() {
    return {
      selectedArrival: '',
      selectedDeparture: '',
      arrivalTimes: ['13:00', '14:00', '15:00', '16:00', '17:00'],
      departureTimes: ['14:00', '15:00', '16:00', '17:00', '18:00']
    }
  },
  computed: {
    canBook() {
      if (this.bookingType === 'day') {
        return this.selectedDate && this.selectedArrival && this.selectedDeparture
      } else {
        return this.selectedDates.start && this.selectedDates.end
      }
    }
  },
  watch: {
    selectedArrival() {
      this.emitTimeSelection()
    },
    selectedDeparture() {
      this.emitTimeSelection()
    }
  },
  methods: {
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
