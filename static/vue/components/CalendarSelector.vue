<template>
  <div class="calendar-selector">
    <div class="date-selection">
      <div v-if="selectedBookingType === 'day'" class="day-booking">
        <h3>Sélectionnez votre journée</h3>
        <div class="calendar-grid">
          <div
            v-for="date in availableDates"
            :key="date.toISOString()"
            class="calendar-day"
            :class="{
              selected: isDateSelected(date),
              available: isDateAvailable(date),
              unavailable: !isDateAvailable(date)
            }"
            @click="selectDate(date)"
          >
            <div class="day-number">{{ date.getDate() }}</div>
            <div class="day-name">{{ getDayName(date) }}</div>
            <div class="availability-indicator">
              <span v-if="isDateAvailable(date)" class="available-dot"></span>
              <span v-else class="unavailable-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="selectedBookingType === 'night'" class="night-booking">
        <h3>Sélectionnez vos dates</h3>
        <div class="date-inputs">
          <div class="date-input">
            <label>Arrivée (19h)</label>
            <input
              type="date"
              v-model="checkInDate"
              :min="minDate"
              @change="updateNightSelection"
            >
          </div>
          <div class="date-input">
            <label>Départ (10h)</label>
            <input
              type="date"
              v-model="checkOutDate"
              :min="checkInDate || minDate"
              @change="updateNightSelection"
            >
          </div>
        </div>

        <div v-if="selectedDates.start && selectedDates.end" class="selection-summary">
          <p><strong>Arrivée:</strong> {{ formatDate(selectedDates.start) }} à 19h</p>
          <p><strong>Départ:</strong> {{ formatDate(selectedDates.end) }} à 10h</p>
          <p><strong>Durée:</strong> {{ calculateNights() }} nuit(s)</p>
        </div>
      </div>
    </div>

    <div class="calendar-footer">
      <div class="legend">
        <div class="legend-item">
          <span class="available-dot"></span>
          <span>Disponible</span>
        </div>
        <div class="legend-item">
          <span class="unavailable-dot"></span>
          <span>Indisponible</span>
        </div>
      </div>

      <button
        class="confirm-dates-btn"
        :disabled="!selectionComplete"
        @click="confirmSelection"
      >
        Confirmer les dates
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CalendarSelector',
  props: {
    service: {
      type: Object,
      required: true
    },
    bookingType: {
      type: String,
      default: 'day'
    }
  },
  data() {
    return {
      selectedBookingType: this.bookingType,
      selectedDates: { start: null, end: null },
      checkInDate: '',
      checkOutDate: '',
      availableDates: [],
      minDate: new Date().toISOString().split('T')[0]
    }
  },
  computed: {
    selectionComplete() {
      return this.selectedDates.start && this.selectedDates.end
    }
  },
  watch: {
    bookingType: {
      immediate: true,
      handler(newType) {
        this.selectedBookingType = newType
        this.resetSelection()
        if (newType === 'day') {
          this.generateAvailableDates()
        }
      }
    }
  },
  mounted() {
    if (this.selectedBookingType === 'day') {
      this.generateAvailableDates()
    }
  },
  methods: {
    generateAvailableDates() {
      const dates = []
      const today = new Date()

      // Generate next 30 days
      for (let i = 0; i < 30; i++) {
        const date = new Date(today)
        date.setDate(today.getDate() + i)
        dates.push(date)
      }

      this.availableDates = dates
    },

    async checkDateAvailability(date) {
      // This would call the backend to check availability
      // For now, we'll simulate some unavailable dates
      const dayOfWeek = date.getDay()
      // Simulate weekends being more booked
      return Math.random() > (dayOfWeek === 0 || dayOfWeek === 6 ? 0.3 : 0.1)
    },

    isDateAvailable(date) {
      // Simplified availability check - in real implementation,
      // this would check against backend data
      return true // Assume all dates are available for demo
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

    selectDate(date) {
      if (this.selectedBookingType === 'day') {
        // For day bookings, select a single day
        this.selectedDates = {
          start: new Date(date),
          end: new Date(date)
        }
        // Set time to default day hours (13:00 - 18:00)
        this.selectedDates.start.setHours(13, 0, 0, 0)
        this.selectedDates.end.setHours(18, 0, 0, 0)
      }
    },

    updateNightSelection() {
      if (this.checkInDate && this.checkOutDate) {
        const start = new Date(this.checkInDate)
        const end = new Date(this.checkOutDate)

        // Set default night hours (19:00 - 10:00 next day)
        start.setHours(19, 0, 0, 0)
        end.setHours(10, 0, 0, 0)

        this.selectedDates = { start, end }
      }
    },

    resetSelection() {
      this.selectedDates = { start: null, end: null }
      this.checkInDate = ''
      this.checkOutDate = ''
    },

    confirmSelection() {
      if (this.selectionComplete) {
        this.$emit('date-selected', {
          start: this.selectedDates.start.toISOString(),
          end: this.selectedDates.end.toISOString(),
          type: this.selectedBookingType
        })
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
    }
  }
}
</script>

<style scoped>
.calendar-selector {
  max-width: 600px;
  margin: 0 auto;
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

.available-dot, .unavailable-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.available-dot {
  background: #28a745;
}

.unavailable-dot {
  background: #dc3545;
}

.date-inputs {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.date-input {
  flex: 1;
}

.date-input label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.date-input input {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 16px;
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

.calendar-footer {
  margin-top: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.confirm-dates-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s ease;
}

.confirm-dates-btn:hover:not(:disabled) {
  background: #218838;
}

.confirm-dates-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
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
  }

  .legend {
    justify-content: center;
  }
}
</style>
