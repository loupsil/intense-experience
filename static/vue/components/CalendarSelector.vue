<template>
  <div class="calendar-selector">
    <div class="calendar-layout">
      <!-- Left Side: Calendar -->
      <div class="calendar-left">
        <div class="date-selection">
          <div v-if="selectedBookingType === 'day'" class="day-booking">
            <h3>Sélectionnez votre journée</h3>

            <!-- Calendar Navigation -->
            <div class="calendar-navigation">
              <button @click="previousMonth" class="nav-btn">&larr;</button>
              <h4>{{ formatMonthYear(currentMonth) }}</h4>
              <button @click="nextMonth" class="nav-btn">&rarr;</button>
            </div>

            <!-- Two Month Calendar View -->
            <div class="two-month-calendar">
              <!-- Current Month -->
              <div class="month-calendar">
                <h4>{{ formatMonthYear(currentMonth) }}</h4>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <!-- Loading overlay for current month -->
                  <div v-if="availabilityLoading" class="calendar-loading-overlay">
                    <div class="calendar-spinner"></div>
                  </div>

                  <div
                    v-for="date in getDaysInMonth(currentMonth)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateSelected(date),
                      'available': isDateAvailable(date),
                      'unavailable': !isDateAvailable(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, currentMonth),
                      'loading': availabilityLoading
                    }"
                    @click="!availabilityLoading && selectDate(date)"
                  >
                    <span class="date-number">{{ date.getDate() }}</span>
                  </div>
                </div>
              </div>

              <!-- Next Month -->
              <div class="month-calendar">
                <h4>{{ formatMonthYear(nextMonth) }}</h4>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <!-- Loading overlay for next month -->
                  <div v-if="availabilityLoading" class="calendar-loading-overlay">
                    <div class="calendar-spinner"></div>
                  </div>

                  <div
                    v-for="date in getDaysInMonth(nextMonth)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateSelected(date),
                      'available': isDateAvailable(date),
                      'unavailable': !isDateAvailable(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, nextMonth),
                      'loading': availabilityLoading
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
            <h3>Sélectionnez vos dates</h3>

            <!-- Calendar Navigation -->
            <div class="calendar-navigation">
              <button @click="previousMonth" class="nav-btn">&larr;</button>
              <h4>{{ formatMonthYear(currentMonth) }}</h4>
              <button @click="nextMonth" class="nav-btn">&rarr;</button>
            </div>

            <!-- Two Month Calendar View -->
            <div class="two-month-calendar">
              <!-- Current Month -->
              <div class="month-calendar">
                <h4>{{ formatMonthYear(currentMonth) }}</h4>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <!-- Loading overlay for current month -->
                  <div v-if="availabilityLoading" class="calendar-loading-overlay">
                    <div class="calendar-spinner"></div>
                  </div>

                  <div
                    v-for="date in getDaysInMonth(currentMonth)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateInRange(date),
                      'selected-start': isStartDate(date),
                      'selected-end': isEndDate(date),
                      'available': isDateAvailable(date),
                      'unavailable': !isDateAvailable(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, currentMonth),
                      'loading': availabilityLoading
                    }"
                    @click="!availabilityLoading && selectNightDate(date)"
                  >
                    <span class="date-number">{{ date.getDate() }}</span>
                  </div>
                </div>
              </div>

              <!-- Next Month -->
              <div class="month-calendar">
                <h4>{{ formatMonthYear(nextMonth) }}</h4>
                <div class="calendar-header">
                  <div v-for="day in weekDays" :key="day" class="calendar-header-day">{{ day }}</div>
                </div>
                <div class="calendar-body">
                  <!-- Loading overlay for next month -->
                  <div v-if="availabilityLoading" class="calendar-loading-overlay">
                    <div class="calendar-spinner"></div>
                  </div>

                  <div
                    v-for="date in getDaysInMonth(nextMonth)"
                    :key="date.toISOString()"
                    class="calendar-cell"
                    :class="{
                      'selected': isDateInRange(date),
                      'selected-start': isStartDate(date),
                      'selected-end': isEndDate(date),
                      'available': isDateAvailable(date),
                      'unavailable': !isDateAvailable(date),
                      'past': isDateInPast(date),
                      'other-month': !isDateInCurrentMonth(date, nextMonth),
                      'loading': availabilityLoading
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
          @time-selected="handleTimeSelection"
          @book-suite="confirmSelection"
        />
      </div>
    </div>

    <div class="calendar-footer">
      <div class="legend">
        <div class="legend-item">
          <div class="legend-color available-color"></div>
          <span>Au moins une suite disponible</span>
        </div>
        <div class="legend-item">
          <div class="legend-color unavailable-color"></div>
          <span>Toutes les suites réservées</span>
        </div>
      </div>
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
      dateAvailabilityCache: {}, // Cache for availability data
      availabilityLoading: false,
      minDate: new Date().toISOString().split('T')[0],
      currentMonth: new Date(),
      weekDays: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
      selectionMode: 'start' // 'start' or 'end'
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
    nextMonth() {
      const next = new Date(this.currentMonth)
      next.setMonth(next.getMonth() + 1)
      return next
    }
  },
  watch: {
    bookingType: {
      immediate: true,
      handler(newType) {
        this.selectedBookingType = newType
        this.resetSelection()
        // Calendar is now always displayed for both booking types
      }
    }
  },
  async mounted() {
    // Calendar is now always displayed for both day and night bookings
    // Fetch availability for initially displayed dates
    await this.fetchAvailabilityForDisplayedDates()
  },
  methods: {

    async fetchBulkAvailability(dates) {
      if (!this.service || !dates || dates.length === 0) return

      this.availabilityLoading = true

      // Determine which endpoint to use based on booking type
      const endpoint = this.selectedBookingType === 'night' 
        ? '/intense_experience-api/bulk-availability-nuitee'
        : '/intense_experience-api/bulk-availability-journee'

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            service_id: this.service.Id,
            dates: dates,
            booking_type: this.selectedBookingType
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        if (data.status === 'success' && data.availability) {
          // Update cache with new availability data
          Object.assign(this.dateAvailabilityCache, data.availability)
        } else {
          console.error('Bulk availability failed:', data.error)
          // Mark dates as unavailable if the API fails
          dates.forEach(dateStr => {
            this.dateAvailabilityCache[dateStr] = {
              available: false,
              total_suites: 0,
              booked_suites: 0,
              available_suites: 0,
              booked_suite_ids: [],
              error: true
            }
          })
        }
      } catch (error) {
        console.error('Failed to fetch availability:', error)
        // Mark dates as unavailable on error for safety
        dates.forEach(dateStr => {
          this.dateAvailabilityCache[dateStr] = {
            available: false,
            total_suites: 0,
            booked_suites: 0,
            available_suites: 0,
            booked_suite_ids: [],
            error: true
          }
        })
      } finally {
        this.availabilityLoading = false
      }
    },

    async fetchAvailabilityForDisplayedDates() {
      // Get all dates currently displayed in the calendar
      const displayedDates = []
      const currentMonthDates = this.getDaysInMonth(this.currentMonth)
      const nextMonthDates = this.getDaysInMonth(this.nextMonth)

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

      // Filter out dates we already have in cache
      const uncachedDates = displayedDates.filter(dateStr => !this.dateAvailabilityCache[dateStr])

      if (uncachedDates.length > 0) {
        await this.fetchBulkAvailability(uncachedDates)
      }
    },

    isDateAvailable(date) {
      if (this.isDateInPast(date)) return false

      // Normalize to UTC midnight to match API keys
      const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
      const dateStr = utcDate.toISOString()
      const availability = this.dateAvailabilityCache[dateStr]

      if (!availability) {
        // If we don't have availability data yet, show as unavailable (will load)
        return false
      }

      // Date is available if at least one suite has at least one time slot free
      return availability.available
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
        // Set time to default day hours (13:00 - 18:00)
        this.selectedDates.start.setHours(13, 0, 0, 0)
        this.selectedDates.end.setHours(18, 0, 0, 0)
        
        // Ensure availability data is loaded for this date (normalize to UTC midnight)
        const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
        const dateStr = utcDate.toISOString()
        if (!this.dateAvailabilityCache[dateStr]) {
          await this.fetchBulkAvailability([dateStr])
        }
      }
    },

    selectNightDate(date) {
      if (this.isDateInPast(date) || !this.isDateAvailable(date)) return

      const selectedDate = new Date(date)

      if (this.selectionMode === 'start' || !this.selectedDates.start) {
        // Selecting start date
        this.selectedDates.start = new Date(selectedDate)
        this.selectedDates.start.setHours(19, 0, 0, 0)
        this.selectedDates.end = null
        this.selectionMode = 'end'
      } else {
        // Selecting end date
        if (selectedDate <= this.selectedDates.start) {
          // If selected date is before or same as start, reset start date
          this.selectedDates.start = new Date(selectedDate)
          this.selectedDates.start.setHours(19, 0, 0, 0)
          this.selectedDates.end = null
          this.selectionMode = 'end'
        } else {
          // Set end date
          this.selectedDates.end = new Date(selectedDate)
          this.selectedDates.end.setHours(10, 0, 0, 0)
          this.selectionMode = 'start'
        }
      }
    },

    resetSelection() {
      this.selectedDates = { start: null, end: null }
      this.checkInDate = ''
      this.checkOutDate = ''
      this.selectionMode = 'start'
    },

    async previousMonth() {
      this.currentMonth.setMonth(this.currentMonth.getMonth() - 1)
      this.currentMonth = new Date(this.currentMonth)
      // Fetch availability for newly displayed dates
      await this.fetchAvailabilityForDisplayedDates()
    },

    async nextMonth() {
      this.currentMonth.setMonth(this.currentMonth.getMonth() + 1)
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
      for (let i = 0; i < startDayOfWeek; i++) {
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
      return date.toLocaleDateString('fr-FR', { year: 'numeric', month: 'long' })
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

    getDateAvailability(date) {
      if (!date) return null
      // Normalize to UTC midnight to match cache keys
      const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
      const dateStr = utcDate.toISOString()
      const availability = this.dateAvailabilityCache[dateStr] || null
      
      // Debug log
      if (date.getMonth() === 11 && date.getDate() === 17) {
        console.log('🔍 getDateAvailability for Dec 17:')
        console.log('   Input date:', date)
        console.log('   UTC dateStr:', dateStr)
        console.log('   Availability:', availability)
        console.log('   Cache keys:', Object.keys(this.dateAvailabilityCache))
      }
      
      return availability
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
  align-items: start;
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
  border: 2px solid #28a745;
}

.unavailable-color {
  background: #f8d7da;
  border: 2px solid #dc3545;
}

/* Calendar Navigation */
.calendar-navigation {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin: 20px 0;
}

.nav-btn {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #666;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.calendar-navigation h4 {
  margin: 0;
  color: #333;
  font-size: 18px;
  min-width: 200px;
  text-align: center;
}

/* Two Month Calendar View */
.two-month-calendar {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin: 20px 0;
}

.month-calendar {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
}

.month-calendar h4 {
  margin: 0 0 15px 0;
  color: #333;
  text-align: center;
  font-size: 16px;
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
  gap: 4px;
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
  border: 1px solid transparent;
}

.calendar-cell:hover:not(.past):not(.unavailable) {
  background: #e9ecef;
  transform: scale(1.1);
}

.calendar-cell.selected {
  background: #007bff;
  color: white;
}

.calendar-cell.selected-start {
  background: #28a745;
  color: white;
}

.calendar-cell.selected-end {
  background: #dc3545;
  color: white;
}

.calendar-cell.selected-start::after,
.calendar-cell.selected-end::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
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
  background: #d4edda; /* Light green background */
  color: #155724; /* Dark green text */
  border-color: #c3e6cb; /* Green border */
}

.calendar-cell.unavailable {
  background: #f8d7da; /* Light red background */
  color: #721c24; /* Dark red text */
  border-color: #f5c6cb; /* Red border */
}

.calendar-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 6px;
}

.calendar-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.calendar-cell.loading {
  opacity: 0.6;
  pointer-events: none;
}

.date-number {
  font-size: 14px;
  font-weight: 500;
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
  justify-content: center;
  align-items: center;
  gap: 40px;
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

  /* Responsive calendar */
  .two-month-calendar {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .calendar-navigation {
    gap: 15px;
  }

  .calendar-navigation h4 {
    font-size: 16px;
    min-width: 150px;
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
    width: 35px;
    height: 35px;
    font-size: 16px;
  }
}
</style>
