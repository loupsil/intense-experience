<template>
  <div class="booking-widget" :class="{ 'has-sidebar': showSidebar }">
    <div class="booking-container">
      <!-- Quick Booking Header -->
      <div v-if="currentStep === 2" class="quick-booking-header">
        <h2>Quick booking</h2>
        <p>Add your travel dates for exact pricing</p>
      </div>

      <!-- Debug Timeline -->
      <div v-if="debugMode" class="debug-timeline">
        <div 
          v-for="step in 7" 
          :key="step"
          class="timeline-step"
          :class="{ active: currentStep === step }"
          @click="currentStep = step"
        >
          <div class="step-dot"></div>
          <span class="step-number">{{ step }}</span>
        </div>
      </div>

      <!-- Selection Header - Show selected service and suite -->
      <div v-if="selectedService && currentStep > 1" v-show="debugMode" class="selection-header">
        <div class="header-content">
          <div class="header-item">
            <i class="fas fa-calendar-check"></i>
            <span class="header-label">Service:</span>
            <span class="header-value">{{ selectedService.Names['fr-FR'] || selectedService.Name }}</span>
          </div>
          <div v-if="selectedSuite" class="header-item">
            <i class="fas fa-home"></i>
            <span class="header-label">Suite:</span>
            <span class="header-value">{{ selectedSuite.Names['fr-FR'] || selectedSuite.Name }}</span>
          </div>
        </div>
      </div>

      <!-- Step 1: Service Selection -->
      <div v-if="currentStep === 1" class="step">
        <h2>Choisissez votre expérience</h2>
        
        <!-- Loading state -->
        <div v-if="loadingServices" class="service-loading">
          <div class="spinner"></div>
          <p>Chargement des services disponibles...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="servicesError" class="service-error">
          <i class="fas fa-exclamation-triangle"></i>
          <p>{{ servicesError }}</p>
          <button class="retry-btn" @click="loadServices">Réessayer</button>
        </div>

        <!-- Services loaded -->
        <div v-else-if="services.length > 0" class="service-selection">
          <div
            v-for="service in services"
            :key="service.Id"
            class="service-card"
            :class="{ selected: selectedService?.Id === service.Id }"
            @click="selectService(service)"
          >
            <h3>{{ service.Names['fr-FR'] || service.Name }}</h3>
            <p>{{ getServiceDescription(service.Id) }}</p>
            <div class="service-icon">
              <i :class="getServiceIcon(service.Id)"></i>
            </div>
          </div>
        </div>

        <!-- No services available -->
        <div v-else class="service-empty">
          <i class="fas fa-inbox"></i>
          <p>Aucun service disponible pour le moment.</p>
        </div>

        <button
          v-if="services.length > 0"
          class="next-btn"
          :disabled="!selectedService"
          @click="nextStep"
        >
          Continuer
        </button>
      </div>

      <!-- Step 2: Calendar Selection -->
      <div v-if="currentStep === 2" class="step">
        <CalendarSelector
          :service="selectedService"
          :booking-type="bookingType"
          :selected-suite="selectedSuite"
          :suite-for-booking="suiteForBooking"
          :suite-pricing="suitePricing"
          :price-display-calculator="calculateSuitePriceDisplay"
          @date-selected="handleDateSelection"
          @dates-confirmed="nextStep"
          @suite-deselected="handleSuiteDeselected"
          @suite-reselected="handleSuiteReselected"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Back</button>
        </div>
      </div>

      <!-- Step 3: Customer Information -->
      <div v-if="currentStep === 3" class="step">
        <h2>Your information</h2>
        <CustomerForm
          ref="customerForm"
          :loading="loading"
          :bookingType="bookingType"
          @customer-info="handleCustomerInfo"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Back</button>
          <button
            class="next-btn"
            :disabled="customerCreationLoading"
            @click="submitCustomerForm"
          >
            <span v-if="customerCreationLoading" class="button-spinner"></span>
            {{ customerCreationLoading ? 'Creating profile...' : 'Continue' }}
          </button>
        </div>
      </div>

      <!-- Step 4: Suite Selection -->
      <div v-if="currentStep === 4" class="step">
        <h2>Choose your suite</h2>
        <SuiteSelector
          ref="suiteSelector"
          :service="selectedService"
          :service-type="getServiceType()"
          :start-date="selectedDates.start"
          :end-date="selectedDates.end"
          :pricing="suitePricing"
          :preselected-suite="preselectedSuite"
          :pricing-calculator="calculateSuitePricingFromData"
          :price-display-calculator="calculateSuitePriceDisplay"
          @suite-selected="selectSuite"
          @pricing-updated="updateSuitePricing"
          @pricing-calculated="updatePricing"
          @pricing-requested="handlePricingRequest"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Back</button>
          <button
            class="next-btn"
            :disabled="!hasActiveSuiteSelection"
            @click="nextStep"
          >
            Continue
          </button>
        </div>
      </div>

      <!-- Step 5: Options & Upsells -->
      <div v-if="currentStep === 5" class="step">
        <h2>Additional options</h2>
        <OptionsSelector
          :products="availableProducts"
          :selected-options="selectedOptions"
          :service-id="selectedService?.Id"
          :number-of-nights="numberOfNights"
          :debug-mode="debugMode"
          :booking-type="bookingType"
          :selected-suite="suiteForBooking"
          :check-in-date="selectedDates.start"
          :check-out-date="selectedDates.end"
          @options-updated="updateOptions"
          @products-loaded="handleProductsLoaded"
        />
        <!-- Booking Summary - Mobile (inline) -->
        <div v-if="!showSidebar" class="booking-summary">
          <h3>{{ formatDateRange(selectedDates.start, selectedDates.end) }}</h3>
          <p v-if="bookingSubtitle" class="booking-subtitle">{{ bookingSubtitle }}</p>
          <div class="summary-item">
            <span>{{ selectedSuite?.Names['fr-FR'] }}</span>
            <span>{{ getSuitePriceInfo().price }}€ <span class="calculation" v-if="getSuitePriceInfo().calculation">({{ getSuitePriceInfo().calculation }})</span></span>
          </div>
          <!-- Individual option lines -->
          <div
            v-for="option in selectedOptions"
            :key="option.Id"
            class="summary-item"
          >
            <span>{{ option.Names?.['fr-FR'] || option.Name }}</span>
            <span>{{ option.calculatedPrice }}€ <span class="calculation" v-if="option.priceCalculation !== option.calculatedPrice + '€'">({{ option.priceCalculation }})</span></span>
          </div>
          <div class="summary-total">
            <strong>Total: {{ typeof pricing.total === 'number' ? (pricing.total + pricing.options) + '€' : pricing.total }}</strong>
          </div>
        </div>
        <!-- Step navigation - shown when sidebar is not visible (mobile) -->
        <div v-if="!showSidebar" class="step-navigation">
          <button class="prev-btn" @click="prevStep">Back</button>
          <button
            class="next-btn"
            :disabled="reservationCreationLoading"
            @click="nextStep"
          >
            <span v-if="reservationCreationLoading" class="button-spinner"></span>
            {{ reservationCreationLoading ? '' : 'Continue' }}
          </button>
        </div>
        <!-- Reservation error message - mobile -->
        <div v-if="!showSidebar && reservationError" class="reservation-error">
          <i class="fas fa-exclamation-triangle"></i>
          <span>{{ reservationError }}</span>
        </div>
      </div>


      <!-- Step 6: Confirmation -->
      <div v-if="currentStep === 6" class="step">
        <!-- Day booking confirmation -->
        <div v-if="bookingType === 'day'" class="confirmation-message">
          <i class="fas fa-check-circle"></i>
          <h2>Reservation pre-registered!</h2>
          <p>Your reservation request has been received. Please note that the payment should be completed now for your reservation to be fully validated.</p>
          <div class="reservation-details">
            <h3>Your reservation details</h3>
            <div class="detail-item">
              <span class="label">Service:</span>
              <span>{{ selectedService?.Names['fr-FR'] }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Suite:</span>
              <span>{{ selectedSuite?.Names['fr-FR'] }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Dates:</span>
              <span>{{ formatDateRange(selectedDates.start, selectedDates.end) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Client:</span>
              <span>{{ customer?.FirstName }} {{ customer?.LastName }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Email:</span>
              <span>{{ customer?.Email }}</span>
            </div>
            <div class="detail-item total">
              <span class="label">Total:</span>
              <span>{{ typeof pricing.total === 'number' ? (pricing.total + pricing.options) + '€' : pricing.total }}</span>
            </div>
          </div>

          <div class="payment-choice">
            <div class="choice-buttons">
              <button class="pay-now-btn" @click="nextStep">
                Pay now
              </button>
            </div>
          </div>
        </div>

        <!-- Night booking confirmation -->
        <div v-else class="confirmation-message">
          <i class="fas fa-check-circle"></i>
          <h2>Reservation confirmed!</h2>
          <p>Your reservation has been created successfully. Please note that payment of 50% is required for your reservation to be fully validated.</p>
          <div class="reservation-details">
            <h3>Your reservation details</h3>
            <div class="detail-item">
              <span class="label">Service:</span>
              <span>{{ selectedService?.Names['fr-FR'] }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Suite:</span>
              <span>{{ selectedSuite?.Names['fr-FR'] }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Dates:</span>
              <span>{{ formatDateRange(selectedDates.start, selectedDates.end) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Client:</span>
              <span>{{ customer?.FirstName }} {{ customer?.LastName }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Email:</span>
              <span>{{ customer?.Email }}</span>
            </div>
            <div class="detail-item total">
              <span class="label">Total:</span>
              <span>{{ typeof pricing.total === 'number' ? (pricing.total + pricing.options) + '€' : pricing.total }}</span>
            </div>
          </div>

          <div class="payment-choice">
            <div class="choice-buttons">
              <button class="pay-now-btn" @click="nextStep">
                {{ bookingType === 'night' ? 'Pay 50% now' : 'Pay now' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 7: Payment -->
      <div v-if="currentStep === 7" class="step">
        <PaymentComponent
          :reservation="reservation"
          :amount="getPaymentAmount()"
          :booking-type="bookingType"
          @reset-booking="resetBooking"
        />
      </div>

    </div>

    <!-- Booking Summary - Desktop Right Side -->
    <div v-if="showSidebar" class="booking-summary-sidebar">
      <div class="booking-summary">
        <h3>{{ formatDateRange(selectedDates.start, selectedDates.end) }}</h3>
        <p v-if="bookingSubtitle" class="booking-subtitle">{{ bookingSubtitle }}</p>
        <div class="summary-item">
          <span>{{ selectedSuite?.Names['fr-FR'] }}</span>
          <span>{{ getSuitePriceInfo().price }}€ <span class="calculation" v-if="getSuitePriceInfo().calculation">({{ getSuitePriceInfo().calculation }})</span></span>
        </div>
        <!-- Individual option lines -->
        <div
          v-for="option in selectedOptions"
          :key="option.Id"
          class="summary-item"
        >
          <span>{{ option.Names?.['fr-FR'] || option.Name }}</span>
          <span>{{ option.calculatedPrice }}€ <span class="calculation" v-if="option.priceCalculation !== option.calculatedPrice + '€'">({{ option.priceCalculation }})</span></span>
        </div>
        <div class="summary-total">
          <strong>Total: {{ typeof pricing.total === 'number' ? (pricing.total + pricing.options) + '€' : pricing.total }}</strong>
        </div>
      </div>
      <div class="sidebar-navigation">
        <button class="prev-btn" @click="prevStep">Back</button>
        <button
          class="next-btn"
          :disabled="reservationCreationLoading"
          @click="nextStep"
        >
          <span v-if="reservationCreationLoading" class="button-spinner"></span>
          {{ reservationCreationLoading ? '' : 'Continue' }}
        </button>
      </div>
      <!-- Reservation error message - desktop sidebar -->
      <div v-if="reservationError" class="reservation-error">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ reservationError }}</span>
      </div>
    </div>

    <!-- Debug button -->
    <button class="debug-btn" @click="toggleDebug" title="Toggle debug mode">
      DEV
    </button>
  </div>
</template>

<script>
export default {
  name: 'BookingWidget',
  components: {
    'CalendarSelector': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/CalendarSelector.vue', window.vueOptions)),
    'SuiteSelector': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/SuiteSelector.vue', window.vueOptions)),
    'OptionsSelector': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/OptionsSelector.vue', window.vueOptions)),
    'CustomerForm': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/CustomerForm.vue', window.vueOptions)),
    'PaymentComponent': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/PaymentComponent.vue', window.vueOptions))
  },
  props: {
    preselectedSuite: {
      type: Object,
      default: null
    },
    preselectedSuiteId: {
      type: String,
      default: ''
    },
    preselectedServiceId: {
      type: String,
      default: ''
    },
    accessPoint: {
      type: String,
      default: 'general'
    }
  },
  data() {
    return {
      currentStep: 1,
      services: [],
      loadingServices: false,
      servicesError: null,
      selectedService: null,
      selectedDates: { start: null, end: null },
      selectedSuite: this.preselectedSuite,
      availableProducts: [],
      selectedOptions: [],
      suitePricing: {}, // Pricing data from SuiteSelector
      suitePriceCalculation: '',
      pricing: { total: 0, options: 0 },
      customerInfo: {},
      customer: null,
      reservation: null,
      customerCreationLoading: false,
      reservationCreationLoading: false,
      reservationError: null,
      bookingType: 'day', // 'day' or 'night'
      debugMode: false, // Debug mode toggle
      suiteClearedForGoldenCell: false,
      hasArriveeAnticipee: false, // Track if early check-in is selected
      hasDepartTardif: false // Track if late check-out is selected
    }
  },
  computed: {
    customerInfoComplete() {
      return this.customerInfo.firstName &&
             this.customerInfo.lastName &&
             this.customerInfo.email
    },

    showSidebar() {
      return this.currentStep === 5
    },

    numberOfNights() {
      if (!this.selectedDates.start || !this.selectedDates.end) {
        return 1
      }

      const start = new Date(this.selectedDates.start)
      const end = new Date(this.selectedDates.end)
      const diffTime = Math.abs(end - start)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      // For night stays, number of nights is typically diffDays - 1
      // But according to user, PerPersonPerTimeUnit should be for nights, so return diffDays
      return diffDays
    },

    hasActiveSuiteSelection() {
      return Boolean(this.selectedSuite && !this.suiteClearedForGoldenCell)
    },

    suiteForBooking() {
      return this.hasActiveSuiteSelection ? this.selectedSuite : null
    },

    bookingSubtitle() {
      if (this.getServiceType() === 'nuitée') {
        const arrivalTime = this.hasArriveeAnticipee ? '18h' : '19h'
        const departureTime = this.hasDepartTardif ? '12h' : '10h'
        return `Arrival: ${arrivalTime} - Departure: ${departureTime}`
      } else if (this.getServiceType() === 'journée' && this.selectedDates.start && this.selectedDates.end) {
        const startTime = new Date(this.selectedDates.start).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
        const endTime = new Date(this.selectedDates.end).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
        return `Arrival: ${startTime} - Departure: ${endTime}`
      }
      return null
    }
  },
  watch: {
    currentStep: {
      handler(newStep) {
        // Ensure products are loaded when accessing step 5 directly
        if (newStep === 5 && this.selectedService && this.availableProducts.length === 0) {
          // The OptionsSelector will handle loading products itself
        }
      }
    },
  },
  async mounted() {
    await this.loadServices()

    // Handle preselected service
    if (this.preselectedServiceId) {
      const service = this.services.find(s => s.Id === this.preselectedServiceId)
      if (service) {
        this.selectService(service)
        this.currentStep = 2 // Skip service selection

        // Handle preselected suite if service was found
        if (this.preselectedSuiteId) {
          await this.loadSuitesForPreselection(service)
        }
      }
    }
  },
  methods: {
    async loadServices() {
      this.loadingServices = true
      this.servicesError = null
      try {
        const response = await fetch('/intense_experience-api/services')
        const data = await response.json()
        if (data.status === 'success') {
          this.services = data.services
          if (this.services.length === 0) {
            this.servicesError = 'Aucun service disponible pour le moment.'
          }
        } else {
          this.servicesError = data.error || 'Erreur lors du chargement des services.'
        }
      } catch (error) {
        console.error('Error loading services:', error)
        this.servicesError = 'Impossible de se connecter au serveur. Vérifiez que l\'application est démarrée et que les identifiants API sont configurés.'
      } finally {
        this.loadingServices = false
      }
    },

    async loadSuitesForPreselection(service) {
      try {
        const response = await fetch(`/intense_experience-api/suites?service_id=${service.Id}`)
        const data = await response.json()
        if (data.status === 'success' && data.suites) {
          // Find the suite with the matching ID
          const suite = data.suites.find(s => s.Id === this.preselectedSuiteId)
          if (suite) {
            this.selectedSuite = suite
            this.suiteClearedForGoldenCell = false
            console.log('Preselected suite found:', suite.Names['fr-FR'] || suite.Name)
          } else {
            console.warn('Preselected suite ID not found:', this.preselectedSuiteId)
          }
        } else {
          console.error('Failed to load suites for preselection:', data.error)
        }
      } catch (error) {
        console.error('Error loading suites for preselection:', error)
      }
    },

    async calculatePreselectedSuitePricing(startDate, endDate) {
      console.log('BookingWidget calculatePreselectedSuitePricing called:', {
        selectedSuite: this.selectedSuite,
        selectedSuiteId: this.selectedSuite?.Id,
        startDate,
        endDate,
        currentSuitePricing: this.suitePricing
      })

      const targetSuite = this.suiteForBooking
      if (!targetSuite || !startDate || !endDate) {
        console.log('BookingWidget: Missing required data for pricing calculation')
        return
      }

      try {
        const rateId = this.getRateId()
        console.log('BookingWidget: rateId for pricing request:', rateId)

        if (!rateId) {
          console.error('BookingWidget: No rate ID available for service type')
          return
        }

        const response = await fetch('/intense_experience-api/pricing', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            rate_id: rateId,
            start_date: startDate,
            end_date: endDate
          })
        })

        console.log('BookingWidget: Pricing API response status:', response.status)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()
        console.log('BookingWidget: Pricing API result:', result)

        if (result.status === 'success') {
          // Store pricing data by category ID
          const pricing = {}
          if (Array.isArray(result.pricing)) {
            console.log('BookingWidget: Processing', result.pricing.length, 'pricing items')
            result.pricing.forEach((categoryPrice, index) => {
              console.log(`BookingWidget: Processing pricing item ${index}:`, {
                CategoryId: categoryPrice.CategoryId,
                Prices: categoryPrice.Prices
              })
              pricing[categoryPrice.CategoryId] = categoryPrice
            })
          } else {
            console.log('BookingWidget: result.pricing is not an array:', result.pricing)
          }

          console.log('BookingWidget: Final pricing object keys:', Object.keys(pricing))
          console.log('BookingWidget: Final pricing object:', pricing)

          // Store pricing data for TimeSelector component
          this.suitePricing = pricing
          console.log('BookingWidget: Set suitePricing to:', this.suitePricing)

          // Calculate suite pricing using shared logic
          const pricingResult = this.calculateSuitePricingFromData(pricing, startDate, endDate, targetSuite)
          console.log('BookingWidget: Local pricing calculation result:', pricingResult)
          this.pricing.total = pricingResult.total
          this.suitePriceCalculation = pricingResult.calculation
        } else {
          console.error('BookingWidget: Failed to load pricing for preselected suite:', result.error)
        }
      } catch (error) {
        console.error('BookingWidget: Error loading pricing for preselected suite:', error)
      }
    },

    calculateSuitePricingFromData(pricing, startDate, endDate, suite = null) {
      const targetSuite = suite || this.selectedSuite
      if (!targetSuite || !pricing) {
        return
      }

      // Get pricing for the selected suite
      const suitePricing = pricing[targetSuite.Id]

      if (suitePricing && suitePricing.Prices && suitePricing.Prices.length > 0) {
        const serviceType = this.getServiceType()

        // For journée: sum all hourly prices, for nuitée: take the first (daily) price
        if (serviceType === 'journée') {
          const total = suitePricing.Prices.reduce((sum, price) => sum + price, 0)
          const hours = suitePricing.Prices.length
          const hourlyRate = suitePricing.Prices[0]

          // For time-based bookings, the number of hours should be hours - 1
          // because the API includes both start and end boundaries
          const actualHours = hours - 1
          const correctedTotal = actualHours * hourlyRate

          return {
            total: correctedTotal,
            calculation: `${hourlyRate}€ × ${actualHours}h`
          }
        } else {
          // For nuitée: use shared pricing calculation logic
          const pricingResult = this.calculateSuitePriceDisplay(suitePricing, startDate, endDate)
          return {
            total: pricingResult.total,
            calculation: pricingResult.calculation
          }
        }
      } else {
        // No pricing data available
        return {
          total: 'N/A',
          calculation: ''
        }
      }
    },

    calculateSuitePriceDisplay(suitePricing, startDate, endDate) {
      // Shared pricing calculation logic for night bookings
      // This ensures consistent pricing display between SuiteSelector and BookingWidget
      const numberOfNights = this.calculateNumberOfNights(startDate, endDate)

      // For night bookings, check if we have individual prices for each night
      // or if it's a single rate to be multiplied
      const prices = suitePricing.Prices

      if (prices.length === 1) {
        // Single rate for all nights
        const total = prices[0] * numberOfNights
        if (numberOfNights === 1) {
          return {
            total: total,
            calculation: ''
          }
        } else {
          return {
            total: total,
            calculation: `${numberOfNights}x${prices[0]}€`
          }
        }
      } else if (prices.length >= numberOfNights) {
        // Individual prices for each night
        const relevantPrices = prices.slice(0, numberOfNights)
        const total = relevantPrices.reduce((sum, price) => sum + price, 0)

        if (numberOfNights === 1) {
          // Single night: don't show calculation details
          return {
            total: total,
            calculation: ''
          }
        } else if (numberOfNights === 2) {
          if (relevantPrices[0] === relevantPrices[1]) {
            // Same price for both nights: show "2x{price}"
            return {
              total: total,
              calculation: `2x${relevantPrices[0]}€`
            }
          } else {
            // Different prices: show "price1 + price2"
            return {
              total: total,
              calculation: `${relevantPrices[0]}€ + ${relevantPrices[1]}€`
            }
          }
        } else {
          // More than 2 nights: check if all prices are the same
          const allSamePrice = relevantPrices.every(price => price === relevantPrices[0])
          if (allSamePrice && numberOfNights > 1) {
            return {
              total: total,
              calculation: `${numberOfNights}x${relevantPrices[0]}€`
            }
          } else {
            // Different prices: show individual prices
            const priceList = relevantPrices.map(price => `${price}€`).join(' + ')
            return {
              total: total,
              calculation: priceList
            }
          }
        }
      } else {
        // Fallback: multiply single price by number of nights
        const total = prices[0] * numberOfNights
        return {
          total: total,
          calculation: `${numberOfNights}x${prices[0]}€`
        }
      }
    },

    calculateNumberOfNights(startDate, endDate) {
      if (!startDate || !endDate) {
        return 1
      }

      const start = new Date(startDate)
      const end = new Date(endDate)
      const diffTime = Math.abs(end - start)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      // For night stays, number of nights is typically diffDays - 1
      // But according to user, PerPersonPerTimeUnit should be for nights, so return diffDays
      return diffDays
    },


    async handlePricingRequest(requestData) {
      const { serviceType, startDate, endDate } = requestData
      if (!startDate || !endDate) {
        return
      }

      try {
        const rateId = this.getRateId()
        if (!rateId) {
          console.error('BookingWidget: No rate ID available for service type')
          return
        }

        const response = await fetch('/intense_experience-api/pricing', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            rate_id: rateId,
            start_date: startDate,
            end_date: endDate
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()
        if (result.status === 'success') {
          // Store pricing data by category ID (same format as before)
          const pricing = {}
          if (Array.isArray(result.pricing)) {
            result.pricing.forEach(categoryPrice => {
              pricing[categoryPrice.CategoryId] = categoryPrice
            })
          }

          // Update suite pricing which will trigger calculateSuitePricing
          this.updateSuitePricing(pricing)
        } else {
          console.error('BookingWidget: Failed to load pricing for SuiteSelector:', result.error)
        }
      } catch (error) {
        console.error('BookingWidget: Error loading pricing for SuiteSelector:', error)
      }
    },


    getRateId() {
      // Return appropriate rate ID based on service type (same as SuiteSelector)
      const serviceType = this.getServiceType()
      if (serviceType === 'nuitée') {
        return 'ed9391ac-b184-4876-8cc1-b3850108b8b0' // Tarif Suites nuitée
      } else if (serviceType === 'journée') {
        // Check if it's a weekend journée
        if (this.selectedDates.start) {
          const date = new Date(this.selectedDates.start)
          const dayOfWeek = date.getDay() // 0 = Sunday, 6 = Saturday
          if (dayOfWeek === 0 || dayOfWeek === 6) {
            return 'd0496fa0-6686-4614-8847-b3850108c537' // TARIF JOURNEE LE WEEKEND
          }
        }
        return 'c3c2109d-984a-4ad4-978e-b3850108b8ad' // TARIF JOURNEE EN SEMAINE
      }
      return null
    },

    selectService(service) {
      this.selectedService = service
      // JOURNEE service ID
      const JOURNEE_ID = '86fcc6a7-75ce-457a-a425-b3850108b6bf'
      this.bookingType = service.Id === JOURNEE_ID ? 'day' : 'night'
      // Clear selected options when service changes to prevent invalid selections
      this.selectedOptions = []
      this.suitePriceCalculation = ''
      // Reset time modification flags
      this.hasArriveeAnticipee = false
      this.hasDepartTardif = false

      // Emit service selection event to parent
      const serviceType = service.Id === JOURNEE_ID ? 'journée' : 'nuitée'
      this.$emit('service-selected', { service, serviceType })
    },

    async handleDateSelection(dates) {
      console.log('BookingWidget handleDateSelection called with:', dates)
      console.log('BookingWidget current state:', {
        selectedSuite: this.selectedSuite,
        currentSelectedDates: this.selectedDates
      })

      this.selectedDates = {
        start: dates.start,
        end: dates.end
      }

      console.log('BookingWidget updated selectedDates to:', this.selectedDates)

      // Reset suitePricing when dates change to avoid showing stale pricing
      if (this.hasActiveSuiteSelection) {
        console.log('BookingWidget: Resetting suitePricing for new date selection')
        this.suitePricing = {}
      }

      // Calculate pricing for preselected suite when dates are selected
      if (this.hasActiveSuiteSelection && dates.start && dates.end) {
        console.log('BookingWidget: Calling calculatePreselectedSuitePricing')
        await this.calculatePreselectedSuitePricing(dates.start, dates.end)
      } else {
        console.log('BookingWidget: Not calling calculatePreselectedSuitePricing - missing data')
      }
    },

    handleSuiteDeselected() {
      // Called when a partially available date is selected (selected suite not available, but other suites are)
      // Clear the suite selection so the user will be prompted to select a suite
      console.log('BookingWidget: Suite deselected due to partial availability - clearing selectedSuite')
      if (!this.selectedSuite) {
        return
      }
      this.suiteClearedForGoldenCell = true
      this.suitePricing = {}
      this.suitePriceCalculation = ''
      this.pricing.total = 0
    },

    handleSuiteReselected() {
      // Called when a fully available date is selected after previously clearing suite selection
      // Reset the suite selection so pricing can be shown again
      console.log('BookingWidget: Suite reselected due to full availability - resetting suite selection')
      const wasCleared = this.suiteClearedForGoldenCell
      this.suiteClearedForGoldenCell = false
      // Recalculate pricing since we now have an active suite selection
      if (wasCleared && this.selectedDates.start && this.selectedDates.end) {
        this.calculatePreselectedSuitePricing(this.selectedDates.start, this.selectedDates.end)
      }
    },

    submitCustomerForm() {
      if (this.$refs.customerForm && this.$refs.customerForm.isFormValid) {
        this.$refs.customerForm.submitForm()
      }
    },

    async handleCustomerInfo(customerInfo) {
      this.customerCreationLoading = true
      try {
        const customerResponse = await fetch('/intense_experience-api/create-customer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(customerInfo)
        })

        if (!customerResponse.ok) {
          const errorText = await customerResponse.text()
          console.error('HTTP error creating customer:', customerResponse.status, errorText)
          throw new Error(`HTTP ${customerResponse.status}: ${errorText}`)
        }

        const customerData = await customerResponse.json()

        if (!customerData || customerData.status !== 'success') {
          console.error('Failed to create customer:', customerData?.error || 'Unknown error')
          throw new Error(customerData?.error || 'Failed to create customer')
        }

        if (!customerData.customer || !customerData.customer.Id) {
          console.error('Invalid customer data received:', customerData)
          throw new Error('Invalid customer data received')
        }

        // Store customer info and proceed to next step
        this.customerInfo = customerInfo
        this.customer = customerData.customer

        // Proceed to next step
        await this.nextStep()

        // Reset loading state
        this.customerCreationLoading = false

      } catch (error) {
        console.error('Error in handleCustomerInfo:', error)
        alert(`Erreur lors de la création du profil client: ${error.message}`)
      } finally {
        this.customerCreationLoading = false
      }
    },


    selectSuite(suite) {
      this.selectedSuite = suite
      this.suiteClearedForGoldenCell = false
    },

    updateSuitePricing(pricing) {
      this.suitePricing = pricing
    },

    updatePricing(pricingData) {
      this.pricing.total = pricingData.total
      this.pricing.options = pricingData.options
      if (Object.prototype.hasOwnProperty.call(pricingData, 'calculation')) {
        this.suitePriceCalculation = pricingData.calculation || ''
      }
    },


    updateOptions(options, totalPrice, timeModifiers) {
      this.selectedOptions = options
      this.pricing.options = totalPrice || 0
      
      // Update time modification flags if provided
      if (timeModifiers) {
        this.hasArriveeAnticipee = timeModifiers.hasArriveeAnticipee || false
        this.hasDepartTardif = timeModifiers.hasDepartTardif || false
        
        if (this.debugMode) {
          console.log('Time modifiers updated:', {
            hasArriveeAnticipee: this.hasArriveeAnticipee,
            hasDepartTardif: this.hasDepartTardif
          })
        }
      }
    },

    async createReservation() {
      this.reservationCreationLoading = true
      this.reservationError = null

      try {
        // Adjust times for nuitée bookings based on selected products
        let startDate = this.selectedDates.start
        let endDate = this.selectedDates.end

        if (this.bookingType === 'night') {
          // Helper function to create a date at a specific Brussels time and convert to UTC
          const createBrusselsTime = (dateStr, hour) => {
            // Get the date part (YYYY-MM-DD)
            const datePart = dateStr.split('T')[0]
            
            // Create date string in Brussels timezone
            const brusselsDateStr = `${datePart}T${hour.toString().padStart(2, '0')}:00:00`
            
            // Parse as local date first
            const date = new Date(brusselsDateStr)
            
            // Get Brussels timezone offset in minutes
            // Brussels is UTC+1 in winter, UTC+2 in summer (DST)
            const formatter = new Intl.DateTimeFormat('en-US', {
              timeZone: 'Europe/Brussels',
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false,
              timeZoneName: 'short'
            })
            
            // Create the target date in Brussels time
            const targetDate = new Date(`${datePart}T00:00:00Z`)
            
            // We need to find what UTC time gives us the desired Brussels time
            // Approach: Create a date object and manually adjust for Brussels offset
            const utcDate = new Date(Date.UTC(
              parseInt(datePart.split('-')[0]),
              parseInt(datePart.split('-')[1]) - 1,
              parseInt(datePart.split('-')[2]),
              hour,
              0,
              0,
              0
            ))
            
            // Check Brussels offset for this date (handles DST)
            const testDate = new Date(datePart + 'T12:00:00')
            const utcStr = testDate.toLocaleString('en-US', { timeZone: 'UTC', hour12: false })
            const brusselsStr = testDate.toLocaleString('en-US', { timeZone: 'Europe/Brussels', hour12: false })
            
            // Calculate offset in hours
            const utcTime = new Date(utcStr).getTime()
            const brusselsTime = new Date(brusselsStr).getTime()
            const offsetHours = Math.round((brusselsTime - utcTime) / (1000 * 60 * 60))
            
            // Subtract the offset to get the correct UTC time
            utcDate.setHours(utcDate.getHours() - offsetHours)
            
            return utcDate.toISOString()
          }

          // Adjust check-in time if "Arrivée anticipée" is selected (18:00 Brussels time)
          if (this.hasArriveeAnticipee) {
            startDate = createBrusselsTime(startDate, 18)
            
            if (this.debugMode) {
              console.log('Adjusted check-in time for Arrivée anticipée to 18:00 Brussels time:', startDate)
            }
          }

          // Adjust check-out time if "Départ tardif" is selected (12:00 Brussels time)
          if (this.hasDepartTardif) {
            endDate = createBrusselsTime(endDate, 12)
            
            if (this.debugMode) {
              console.log('Adjusted check-out time for Départ tardif to 12:00 Brussels time:', endDate)
            }
          }
        }

        const reservationPayload = {
          service_id: this.selectedService.Id,
          customer_id: this.customer.Id,
          suite_id: this.suiteForBooking?.Id,
          rate_id: this.getDefaultRateForService(),
          start_date: startDate,
          end_date: endDate,
          person_count: 2,
          options: this.selectedOptions
        }

        const reservationResponse = await fetch('/intense_experience-api/create-reservation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(reservationPayload)
        })

        const reservationData = await reservationResponse.json()

        if (reservationData.status !== 'success') {
          console.error('Failed to create reservation:', reservationData.error)
          // Use the backend error message if available
          const backendError = reservationData.error || 'Erreur inconnue'
          throw new Error(backendError)
        }

        this.reservation = reservationData.reservation

        // Stay on confirmation step - user will choose to pay or go home

      } catch (error) {
        console.error('Error creating reservation:', error)
        // Display detailed error only in debug mode, generic message otherwise
        if (this.debugMode) {
          this.reservationError = `Erreur lors de la création de la réservation: ${error.message}`
        } else {
          this.reservationError = 'Erreur lors de la création de la réservation. Veuillez réessayer.'
        }
      } finally {
        this.reservationCreationLoading = false
      }
    },

    async nextStep() {
      if (this.currentStep === 1) {
        this.currentStep = 2
      } else if (this.currentStep === 2) {
        this.currentStep = 3
      } else if (this.currentStep === 3) {
        if (!this.hasActiveSuiteSelection) {
          this.currentStep = 4
        } else {
          this.currentStep = 5
        }
      } else if (this.currentStep === 4) {
        this.currentStep = 5
      } else if (this.currentStep === 5) {
        await this.createReservation()
        // Only advance to step 6 if reservation was created successfully (no error)
        if (!this.reservationError) {
          this.currentStep = 6
        }
      } else if (this.currentStep === 6) {
        // Go to payment step
        this.currentStep = 7
      } else {
        this.currentStep++
      }
    },

    prevStep() {
      if (this.currentStep > 1) {
        this.currentStep--
      }
    },

    getSuitePriceInfo() {
      if (this.$refs.suiteSelector) {
        return this.$refs.suiteSelector.getSuitePriceInfo()
      }
      return { price: this.pricing.total, calculation: this.suitePriceCalculation }
    },

    getServiceDescription(serviceId) {
      const descriptions = {
        '86fcc6a7-75ce-457a-a425-b3850108b6bf': 'Réservation à la journée - arrivée entre 13h et 18h',
        '7ba0b732-93cc-477a-861d-b3850108b730': 'Réservation à la nuitée - arrivée à 19h, départ à 10h'
      }
      return descriptions[serviceId] || ''
    },

    getServiceIcon(serviceId) {
      return serviceId === '86fcc6a7-75ce-457a-a425-b3850108b6bf' ? 'fas fa-sun' : 'fas fa-moon'
    },

    getServiceType() {
      const JOURNEE_ID = '86fcc6a7-75ce-457a-a425-b3850108b6bf'
      const NUITEE_ID = '7ba0b732-93cc-477a-861d-b3850108b730'

      if (!this.selectedService) return 'journée' // default

      return this.selectedService.Id === JOURNEE_ID ? 'journée' : 'nuitée'
    },

    getDefaultRateForService() {
      // Return appropriate rate ID based on service type
      const JOURNEE_ID = '86fcc6a7-75ce-457a-a425-b3850108b6bf'
      const NUITEE_ID = '7ba0b732-93cc-477a-861d-b3850108b730'

      if (!this.selectedService) return null

      if (this.selectedService.Id === JOURNEE_ID) {
        // Day service - use weekday rate
        return 'c3c2109d-984a-4ad4-978e-b3850108b8ad'
      } else if (this.selectedService.Id === NUITEE_ID) {
        // Night service - use night rate
        return 'ed9391ac-b184-4876-8cc1-b3850108b8b0'
      }

      // Fallback to night rate if service not recognized
      console.warn('Unknown service ID, using default night rate:', this.selectedService.Id)
      return 'ed9391ac-b184-4876-8cc1-b3850108b8b0'
    },

    formatDateRange(start, end) {
      if (!start || !end) return ''
      const startDate = new Date(start).toLocaleDateString('fr-FR')
      const endDate = new Date(end).toLocaleDateString('fr-FR')

      // For journée bookings (same day), only show the date once
      if (startDate === endDate) {
        return startDate
      }

      return `${startDate} - ${endDate}`
    },



    resetBooking() {
      // Reset the entire booking process
      this.currentStep = 1
      this.selectedService = null
      this.selectedSuite = null
      this.suiteClearedForGoldenCell = false
      this.selectedDates = { start: null, end: null }
      this.selectedOptions = []
      this.suitePricing = {}
      this.suitePriceCalculation = ''
      this.customerInfo = { firstName: '', lastName: '', email: '', phone: '' }
      this.pricing = { total: 0, options: 0, breakdown: [] }
      this.reservation = null
      this.reservationError = null
      this.accessPoint = 'general'
      this.hasArriveeAnticipee = false
      this.hasDepartTardif = false
    },

    toggleDebug() {
      this.debugMode = !this.debugMode
    },

    handleProductsLoaded(products) {
      // Update available products when loaded by OptionsSelector
      this.availableProducts = products
    },

    getPaymentAmount() {
      const totalAmount = typeof this.pricing.total === 'number' ? this.pricing.total + this.pricing.options : 0
      
      // For night bookings, charge half the amount
      if (this.bookingType === 'night') {
        return totalAmount / 2
      }
      
      // For day bookings, charge full amount
      return totalAmount
    }
  }
}
</script>

<style scoped>
.booking-widget {
  font-family: 'Arial', sans-serif;
  margin: 0 auto;
  background: var(--booking-section-background, #fff);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  transition: background-color 0.5s ease;
}


.booking-container {
  padding: 30px;
}

.quick-booking-header {
  text-align: left;
  margin-bottom: 40px;
}

.quick-booking-header h2 {
  font-family: 'Canela Condensed Trial', serif;
  font-weight: 300;
  font-style: normal;
  font-size: 38px;
  line-height: 105%;
  letter-spacing: 0%;
  color: var(--heading-text-color, #333);
  margin: 0 0 15px 0;
  transition: color 0.5s ease;
  text-align: left;
}

.quick-booking-header p {
  font-family: 'Whitney HTF', sans-serif;
  font-weight: 500;
  font-style: normal;
  font-size: 15px;
  line-height: 21px;
  letter-spacing: 0%;
  color: var(--secondary-text-color, #666);
  margin: 0;
  transition: color 0.5s ease;
}

.selection-header {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  color: white;
  padding: 15px 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 10px rgba(0,123,255,0.2);
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.header-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-item i {
  font-size: 16px;
  opacity: 0.9;
  width: 20px;
  text-align: center;
}

.header-label {
  font-weight: 500;
  font-size: 14px;
  opacity: 0.9;
}

.header-value {
  font-weight: 600;
  font-size: 16px;
  margin-left: 5px;
}

.step {
  min-height: 400px;
}

h2 {
  color: var(--heading-text-color, #333);
  margin-bottom: 30px;
  text-align: center;
  transition: color 0.5s ease;
}

.service-selection {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.service-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.service-card:hover {
  border-color: #007bff;
  transform: translateY(-2px);
}

.service-card.selected {
  border-color: #28a745;
  background-color: #f8fff9;
}

.service-card h3 {
  margin: 0 0 10px 0;
  color: var(--heading-text-color, #333);
  transition: color 0.5s ease;
}

.service-card p {
  margin: 10px 0;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  transition: color 0.5s ease;
}

.service-icon {
  font-size: 48px;
  color: #007bff;
  margin-top: 15px;
}

.service-loading,
.service-error,
.service-empty {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}


.service-error {
  color: #dc3545;
}

.service-error i {
  font-size: 48px;
  margin-bottom: 20px;
  display: block;
}

.reservation-error {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #dc3545;
  font-size: 14px;
  margin-top: 10px;
  text-align: left;
}

.reservation-error i {
  font-size: 16px;
  flex-shrink: 0;
}

.service-empty i {
  font-size: 48px;
  margin-bottom: 20px;
  display: block;
  color: #ccc;
}

.retry-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 25px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 15px;
  transition: background 0.3s ease;
}

.retry-btn:hover {
  background: #c82333;
}

.next-btn, .prev-btn {
  background: #c9a961;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.next-btn:hover:not(:disabled), .prev-btn:hover {
  background: #b89851;
}

.next-btn:disabled {
  background: #666;
  cursor: not-allowed;
  opacity: 0.5;
}

.button-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: button-spin 1s ease-in-out infinite;
  margin-right: 8px;
}

@keyframes button-spin {
  to { transform: rotate(360deg); }
}

.step-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}

.sidebar-navigation {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
}

.booking-summary {
  background: var(--booking-section-background, #f8f9fa);
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
  transition: background-color 0.5s ease;
}

.booking-subtitle {
  font-size: 14px;
  color: var(--secondary-text-color, #666);
  margin: 5px 0 15px 0;
  font-weight: 500;
  text-align: left;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 5px 0;
  border-bottom: 1px solid #e0e0e0;
}

.summary-total {
  font-size: 18px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 2px solid #ccc;
  text-align: right;
}

.calculation {
  font-size: 11px;
  color: #666;
  font-weight: normal;
}


/* Confirmation page styles */
.confirmation-message {
  text-align: center;
  padding: 20px 20px;
}

.confirmation-message .fa-check-circle {
  font-size: 60px;
  color: #c9a961;
  margin-bottom: 12px;
}

.confirmation-message h2 {
  color: var(--heading-text-color, #333);
  margin-bottom: 8px;
}

.confirmation-message > p {
  color: #666;
  font-size: 16px;
  margin-bottom: 15px;
}

.reservation-details {
  background: var(--booking-section-background, #f8f9fa);
  border-radius: 8px;
  padding: 18px;
  margin: 15px auto;
  max-width: 500px;
  text-align: left;
  transition: background-color 0.5s ease;
}

.reservation-details h3 {
  color: var(--heading-text-color, #333);
  margin-bottom: 12px;
  text-align: center;
  font-size: 18px;
  transition: color 0.5s ease;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  font-weight: bold;
  color: #555;
}

.detail-item.total {
  margin-top: 10px;
  padding-top: 12px;
  border-top: 2px solid #c9a961;
  font-size: 16px;
  color: var(--heading-text-color, #333);
}

.payment-choice {
  margin-top: 18px;
  text-align: center;
}

.payment-choice p {
  color: #666;
  margin-bottom: 12px;
  font-size: 15px;
}

.choice-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.pay-now-btn, .home-btn {
  padding: 10px 22px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 15px;
}

.pay-now-btn {
  background: #c9a961;
  color: white;
}

.pay-now-btn:hover {
  background: #b89851;
}

.home-btn {
  background: #6c757d;
  color: white;
}

.home-btn:hover {
  background: #5a6268;
}

/* Desktop layout with sidebar */
@media (min-width: 1024px) {
  .booking-widget.has-sidebar {
    display: flex;
    gap: 30px;
    align-items: flex-start;
  }

  .booking-container {
    flex: 1;
    order: 1;
  }

  .booking-summary-sidebar {
    flex: 0 0 300px;
    position: sticky;
    top: 20px;
    margin: 20px;
    order: 2;
  }
}


/* Responsive */
@media (max-width: 768px) {

  .booking-container {
    padding: 20px;
  }

  .selection-header {
    padding: 12px 15px;
    margin-bottom: 20px;
  }

  .header-content {
    gap: 8px;
  }

  .header-item {
    gap: 6px;
  }

  .header-label {
    font-size: 13px;
  }

  .header-value {
    font-size: 15px;
  }

  .service-selection {
    grid-template-columns: 1fr;
  }

  .step-navigation {
    flex-direction: column;
  }

  .step-navigation button {
    margin: 5px 0;
  }

  .sidebar-navigation {
    flex-direction: column;
  }

  .sidebar-navigation button {
    margin: 5px 0;
  }

  .confirmation-message {
    padding: 20px 10px;
  }

  .confirmation-message .fa-check-circle {
    font-size: 60px;
    color: #c9a961;
  }

  .reservation-details {
    padding: 20px;
  }

  .quick-booking-header {
    margin-bottom: 30px;
  }

  .quick-booking-header h2 {
    font-size: 32px;
  }

  .quick-booking-header p {
    font-size: 14px;
    line-height: 18px;
  }

  .choice-buttons {
    flex-direction: column;
  }

  .pay-now-btn, .home-btn {
    width: 100%;
  }
}

/* Debug Timeline - Minimalistic */
.debug-timeline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 20px;
  margin-bottom: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px dashed #ddd;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.timeline-step:hover .step-dot {
  transform: scale(1.2);
  background: #007bff;
}

.step-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ccc;
  transition: all 0.2s ease;
}

.timeline-step.active .step-dot {
  width: 16px;
  height: 16px;
  background: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.2);
}

.step-number {
  font-size: 11px;
  color: #666;
  font-weight: 500;
}

.timeline-step.active .step-number {
  color: #007bff;
  font-weight: 700;
}

/* Debug button */
.debug-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #333;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
  z-index: 9999;
  letter-spacing: 0.5px;
}

.debug-btn:hover {
  background: #000;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.debug-btn:active {
  transform: translateY(0);
}

@media (max-width: 768px) {
  .debug-timeline {
    gap: 15px;
    padding: 15px;
  }
  
  .step-dot {
    width: 10px;
    height: 10px;
  }
  
  .timeline-step.active .step-dot {
    width: 14px;
    height: 14px;
  }
  
  .step-number {
    font-size: 10px;
  }
}
</style>

