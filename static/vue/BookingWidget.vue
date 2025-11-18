<template>
  <div class="booking-widget">
    <div class="booking-container">
      <!-- Selection Header - Show selected service and suite -->
      <div v-if="selectedService && currentStep > 1" class="selection-header">
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
        <h2>Sélectionnez vos dates</h2>
        <CalendarSelector
          :service="selectedService"
          :booking-type="bookingType"
          :selected-suite="selectedSuite"
          @date-selected="handleDateSelection"
          @dates-confirmed="nextStep"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
        </div>
      </div>

      <!-- Step 3: Customer Information -->
      <div v-if="currentStep === 3" class="step">
        <h2>Vos informations</h2>
        <CustomerForm
          :loading="loading"
          @customer-info="handleCustomerInfo"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
        </div>
      </div>

      <!-- Step 4: Suite Selection (only if not preselected) -->
      <div v-if="currentStep === 4 && !preselectedSuite && !preselectedSuiteId" class="step">
        <h2>Choisissez votre suite</h2>
        <SuiteSelector
          :suites="availableSuites"
          :availability="suiteAvailability"
          :service-type="getServiceType()"
          :start-date="selectedDates.start"
          :end-date="selectedDates.end"
          :pricing="suitePricing"
          @suite-selected="selectSuite"
          @pricing-updated="updateSuitePricing"
          @pricing-requested="handlePricingRequest"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
          <button
            class="next-btn"
            :disabled="!selectedSuite"
            @click="nextStep"
          >
            Continuer
          </button>
        </div>
      </div>

      <!-- Step 5: Options & Upsells -->
      <div v-if="currentStep === 5" class="step">
        <h2>Options supplémentaires</h2>
        <OptionsSelector
          :products="availableProducts"
          :selected-options="selectedOptions"
          @options-updated="updateOptions"
        />
        <div class="booking-summary">
          <h3>Récapitulatif</h3>
          <div class="summary-item">
            <span>{{ selectedService?.Names['fr-FR'] }}</span>
            <span>{{ formatDateRange(selectedDates.start, selectedDates.end) }}</span>
          </div>
          <div class="summary-item">
            <span>{{ selectedSuite?.Names['fr-FR'] }}</span>
            <span>{{ pricing.total }}{{ typeof pricing.total === 'number' ? '€' : '' }}</span>
          </div>
          <!-- Individual option lines -->
          <div
            v-for="option in selectedOptions"
            :key="option.Id"
            class="summary-item"
          >
            <span>{{ option.Names?.['fr-FR'] || option.Name }}</span>
            <span>{{ getProductPrice(option) }}€</span>
          </div>
          <div class="summary-total">
            <strong>Total: {{ typeof pricing.total === 'number' ? (pricing.total + pricing.options) + '€' : pricing.total }}</strong>
          </div>
        </div>
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
          <button class="next-btn" @click="nextStep">Continuer</button>
        </div>
      </div>


      <!-- Step 6: Confirmation -->
      <div v-if="currentStep === 6" class="step">
        <div class="confirmation-message">
          <i class="fas fa-check-circle"></i>
          <h2>Réservation confirmée !</h2>
          <p>Votre réservation a été créée avec succès.</p>
          <div class="reservation-details">
            <h3>Détails de votre réservation</h3>
            <div class="detail-item">
              <span class="label">Service :</span>
              <span>{{ selectedService?.Names['fr-FR'] }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Suite :</span>
              <span>{{ selectedSuite?.Names['fr-FR'] }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Dates :</span>
              <span>{{ formatDateRange(selectedDates.start, selectedDates.end) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Client :</span>
              <span>{{ customer?.FirstName }} {{ customer?.LastName }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Email :</span>
              <span>{{ customer?.Email }}</span>
            </div>
            <div class="detail-item total">
              <span class="label">Total :</span>
              <span>{{ typeof pricing.total === 'number' ? (pricing.total + pricing.options) + '€' : pricing.total }}</span>
            </div>
          </div>

          <div class="payment-choice">
            <p>Que souhaitez-vous faire maintenant ?</p>
            <div class="choice-buttons">
              <button class="pay-now-btn" @click="nextStep">
                Payer maintenant
              </button>
              <button class="home-btn" @click="resetBooking">
                Retour à l'accueil
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 7: Payment -->
      <div v-if="currentStep === 7" class="step">
        <PaymentComponent
          :reservation="reservation"
          :amount="typeof pricing.total === 'number' ? pricing.total + pricing.options : 0"
          @reset-booking="resetBooking"
        />
      </div>

      <!-- Loading overlay -->
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>{{ loadingMessage }}</p>
      </div>
    </div>
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
      availableSuites: [],
      suiteAvailability: {},
      selectedSuite: this.preselectedSuite,
      availableProducts: [],
      selectedOptions: [],
      suitePricing: {}, // Pricing data from SuiteSelector
      pricing: { total: 0, options: 0 },
      customerInfo: {},
      customer: null,
      reservation: null,
      loading: false,
      loadingMessage: '',
      bookingType: 'day' // 'day' or 'night'
    }
  },
  computed: {
    customerInfoComplete() {
      return this.customerInfo.firstName &&
             this.customerInfo.lastName &&
             this.customerInfo.email
    }
  },
  async mounted() {
    await this.loadServices()

    // Handle preselected service
    if (this.preselectedServiceId) {
      const service = this.services.find(s => s.Id === this.preselectedServiceId)
      if (service) {
        this.selectService(service)
        this.currentStep = 2 // Skip service selection
      }
    }

    // Handle preselected suite (either from prop or URL parameter)
    if (this.preselectedSuite || this.preselectedSuiteId) {
      if (this.preselectedSuite) {
        this.selectedSuite = this.preselectedSuite
      } else if (this.preselectedSuiteId) {
        await this.loadPreselectedSuite()
      }

      // Don't skip calendar step - always show it so user can choose dates
      // Only skip suite selection step (step 4)
      // If we're at step 2 (calendar), stay there
      // If we're at step 1, go to step 2 (calendar)
      if (this.currentStep === 1) {
        this.currentStep = 2
      }
      // If we're at step 2, stay at step 2 (calendar) - user needs to select dates
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

    async loadPreselectedSuite() {
      try {
        // We need to determine the service ID to fetch suites
        const serviceId = this.selectedService?.Id || this.preselectedServiceId
        if (!serviceId) return

        const response = await fetch(`/intense_experience-api/suites?service_id=${serviceId}`)
        const data = await response.json()

        if (data.status === 'success' && data.suites) {
          const suite = data.suites.find(s => s.Id === this.preselectedSuiteId)
          if (suite) {
            this.selectedSuite = suite
            // Pricing will be loaded when dates are selected in handleDateSelection
          }
        }
      } catch (error) {
        console.error('Error loading preselected suite:', error)
      }
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

    async loadSuitePricing() {
      if (!this.selectedService || !this.selectedSuite || !this.selectedDates.start || !this.selectedDates.end) {
        return
      }

      try {
        const rateId = this.getRateId()
        if (!rateId) {
          console.error('No rate ID available for service type')
          return
        }

        const response = await fetch('/intense_experience-api/pricing', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            rate_id: rateId,
            start_date: this.selectedDates.start,
            end_date: this.selectedDates.end
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()
        if (result.status === 'success') {
          // Store pricing data by category ID (same format as SuiteSelector)
          const pricing = {}
          if (Array.isArray(result.pricing)) {
            result.pricing.forEach(categoryPrice => {
              pricing[categoryPrice.CategoryId] = categoryPrice
            })
          }

          // Update suite pricing which will trigger calculateSuitePricing
          this.updateSuitePricing(pricing)
        } else {
          console.error('BookingWidget: Failed to load pricing:', result.error)
        }
      } catch (error) {
        console.error('BookingWidget: Error loading suite pricing:', error)
      }
    },

    getRateId() {
      // Return appropriate rate ID based on service type (same as SuiteSelector)
      const serviceType = this.getServiceType()
      if (serviceType === 'nuitée') {
        return 'ed9391ac-b184-4876-8cc1-b3850108b8b0' // Tarif Suites nuitée
      } else if (serviceType === 'journée') {
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

      // Emit service selection event to parent
      const serviceType = service.Id === JOURNEE_ID ? 'journée' : 'nuitée'
      this.$emit('service-selected', { service, serviceType })
    },

    async handleDateSelection(dates) {
      this.selectedDates = {
        start: dates.start,
        end: dates.end
      }

      // Load pricing for preselected suite when dates are selected
      if (this.selectedSuite && !this.suitePricing[this.selectedSuite.Id]) {
        await this.loadSuitePricing()
      }
    },

    async handleCustomerInfo(customerInfo) {
      this.loading = true
      this.loadingMessage = 'Création de votre profil client...'

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

        // Don't set loading to false here - let nextStep() handle it
        await this.nextStep()

      } catch (error) {
        console.error('Error in handleCustomerInfo:', error)
        alert(`Erreur lors de la création du profil client: ${error.message}`)
        this.loading = false
      }
    },

    async loadSuites() {
      if (!this.selectedService) {
        console.warn('No service selected')
        return
      }

      this.loading = true
      this.loadingMessage = 'Chargement des suites...'

      try {
        const response = await fetch(`/intense_experience-api/suites?service_id=${this.selectedService.Id}`)
        const data = await response.json()

        if (data.status === 'success') {
          this.availableSuites = data.suites
          await this.checkSuiteAvailability()
        } else {
          console.error('Failed to load suites:', data.error)
        }
      } catch (error) {
        console.error('Error loading suites:', error)
      } finally {
        this.loading = false
      }
    },

    async checkSuiteAvailability() {
      if (!this.selectedDates.start || !this.selectedDates.end) {
        console.warn('No dates selected - aborting availability check')
        return
      }

      // Determine which suites to check availability for
      let suitesToCheck = []
      if (this.selectedSuite) {
        suitesToCheck = [this.selectedSuite]
      } else if (this.availableSuites && this.availableSuites.length > 0) {
        suitesToCheck = this.availableSuites
      } else {
        console.warn('No suites available to check - aborting availability check')
        return
      }

      this.loadingMessage = 'Vérification des disponibilités...'

      try {
        for (const suite of suitesToCheck) {
          try {
            const payload = {
              service_id: this.selectedService.Id,
              suite_id: suite.Id,
              start_date: this.selectedDates.start,
              end_date: this.selectedDates.end,
              booking_type: this.bookingType
            }

            const response = await fetch('/intense_experience-api/availability', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            })

            const data = await response.json()

            if (data.status === 'success') {
              this.suiteAvailability[suite.Id] = data.available
            } else {
              console.error(`Availability check failed for suite ${suite.Id}:`, data.error)
              this.suiteAvailability[suite.Id] = false
            }
          } catch (error) {
            console.error(`Error checking availability for suite ${suite.Id}:`, error)
            this.suiteAvailability[suite.Id] = false
          }
        }
      } catch (error) {
        console.error('Error in availability check:', error)
      }
    },

    selectSuite(suite) {
      this.selectedSuite = suite
      this.calculateSuitePricing()
    },

    updateSuitePricing(pricing) {
      this.suitePricing = pricing
      if (this.selectedSuite) {
        this.calculateSuitePricing()
      }
    },

    calculateSuitePricing() {
      if (!this.selectedSuite || !this.suitePricing) {
        return
      }

      // Get pricing for the selected suite
      const suitePricing = this.suitePricing[this.selectedSuite.Id]

      if (suitePricing && suitePricing.Prices && suitePricing.Prices.length > 0) {
        // For journée: sum all hourly prices, for nuitée: take the first (daily) price
        if (this.getServiceType() === 'journée') {
          const total = suitePricing.Prices.reduce((sum, price) => sum + price, 0)
          const hours = suitePricing.Prices.length
          const hourlyRate = suitePricing.Prices[0]

          // For time-based bookings, the number of hours should be hours - 1
          // because the API includes both start and end boundaries
          const actualHours = hours - 1
          const correctedTotal = actualHours * hourlyRate

          this.pricing.total = correctedTotal
        } else {
          // For nuitée, take the first price (daily rate)
          this.pricing.total = suitePricing.Prices[0]
        }
      } else {
        // No pricing data available
        this.pricing.total = 'N/A'
      }
    },

    async loadProducts() {
      try {
        const response = await fetch('/intense_experience-api/products')
        const data = await response.json()
        if (data.status === 'success') {
          // Filter products by selected service
          const allProducts = data.products || []
          this.availableProducts = allProducts.filter(product =>
            product.ServiceId === this.selectedService.Id
          )
        }
      } catch (error) {
        console.error('Error loading products:', error)
      }
    },

    updateOptions(options) {
      this.selectedOptions = options
      this.calculateOptionsPricing()
    },

    calculateOptionsPricing() {
      // Calculate options pricing only (suite pricing comes from SuiteSelector)
      this.pricing.options = this.selectedOptions.reduce((sum, option) => {
        const price = this.getProductPrice(option)
        return sum + (typeof price === 'number' ? price : 0)
      }, 0)
    },

    async createReservation() {
      this.loading = true
      this.loadingMessage = 'Création de votre réservation...'

      try {
        const reservationPayload = {
          service_id: this.selectedService.Id,
          customer_id: this.customer.Id,
          suite_id: this.selectedSuite.Id,
          rate_id: this.getDefaultRateForService(),
          start_date: this.selectedDates.start,
          end_date: this.selectedDates.end,
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
          throw new Error('Failed to create reservation')
        }

        this.reservation = reservationData.reservation

        // Stay on confirmation step - user will choose to pay or go home

      } catch (error) {
        console.error('Error creating reservation:', error)
        alert('Erreur lors de la création de la réservation. Veuillez réessayer.')
      } finally {
        this.loading = false
      }
    },

    async nextStep() {
      if (this.currentStep === 1) {
        this.currentStep = 2
      } else if (this.currentStep === 2) {
        this.currentStep = 3
      } else if (this.currentStep === 3) {
        if (this.accessPoint === 'general') {
          await this.loadSuites()
          // Skip suite selection if suite is preselected
          if (this.selectedSuite) {
            this.loadProducts()
            this.calculateOptionsPricing()
            this.currentStep = 5
          } else {
            this.currentStep = 4
          }
        } else {
          this.loadProducts()
          this.calculateOptionsPricing()
          this.currentStep = 5
        }
      } else if (this.currentStep === 4) {
        this.loadProducts()
        this.calculateOptionsPricing()
        this.currentStep = 5
      } else if (this.currentStep === 5) {
        await this.createReservation()
        this.currentStep = 6
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
      return `${startDate} - ${endDate}`
    },

    getProductPrice(product) {
      // Extract price from product data (Mews API format)
      if (product.Price && typeof product.Price.GrossValue === 'number') {
        return product.Price.GrossValue
      }

      // Try pricing field as well
      if (product.Pricing && product.Pricing.Value && typeof product.Pricing.Value.GrossValue === 'number') {
        return product.Pricing.Value.GrossValue
      }

      // No price found - return error indicator
      console.error('Price not found for product:', product.Name || product.Id)
      return 'N/A'
    },

    resetBooking() {
      // Reset the entire booking process
      this.currentStep = 1
      this.selectedService = null
      this.selectedSuite = null
      this.selectedDates = { start: null, end: null }
      this.selectedOptions = []
      this.suitePricing = {}
      this.customerInfo = { firstName: '', lastName: '', email: '', phone: '' }
      this.pricing = { total: 0, options: 0, breakdown: [] }
      this.reservation = null
      this.accessPoint = 'general'
    }
  }
}
</script>

<style scoped>
.booking-widget {
  font-family: 'Arial', sans-serif;
  max-width: 800px;
  margin: 0 auto;
  background: var(--booking-section-background, #fff);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  transition: background-color 0.5s ease;
}

.booking-container {
  padding: 30px;
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

.service-loading .spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

.service-error {
  color: #dc3545;
}

.service-error i {
  font-size: 48px;
  margin-bottom: 20px;
  display: block;
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
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s ease;
}

.next-btn:hover:not(:disabled), .prev-btn:hover {
  background: #0056b3;
}

.next-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.step-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}

.booking-summary {
  background: var(--booking-section-background, #f8f9fa);
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
  transition: background-color 0.5s ease;
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
  border-top: 2px solid #007bff;
  text-align: right;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255,255,255,0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-overlay p {
  color: #666;
  font-size: 16px;
}

/* Confirmation page styles */
.confirmation-message {
  text-align: center;
  padding: 40px 20px;
}

.confirmation-message .fa-check-circle {
  font-size: 80px;
  color: #28a745;
  margin-bottom: 20px;
}

.confirmation-message h2 {
  color: #28a745;
  margin-bottom: 15px;
}

.confirmation-message > p {
  color: #666;
  font-size: 18px;
  margin-bottom: 30px;
}

.reservation-details {
  background: var(--booking-section-background, #f8f9fa);
  border-radius: 8px;
  padding: 25px;
  margin: 30px auto;
  max-width: 500px;
  text-align: left;
  transition: background-color 0.5s ease;
}

.reservation-details h3 {
  color: var(--heading-text-color, #333);
  margin-bottom: 20px;
  text-align: center;
  font-size: 20px;
  transition: color 0.5s ease;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
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
  margin-top: 15px;
  padding-top: 20px;
  border-top: 2px solid #007bff;
  font-size: 18px;
  color: #007bff;
}

.payment-choice {
  margin-top: 30px;
  text-align: center;
}

.payment-choice p {
  color: #666;
  margin-bottom: 20px;
  font-size: 16px;
}

.choice-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.pay-now-btn, .home-btn {
  padding: 12px 25px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 16px;
}

.pay-now-btn {
  background: #007bff;
  color: white;
}

.pay-now-btn:hover {
  background: #0056b3;
}

.home-btn {
  background: #6c757d;
  color: white;
}

.home-btn:hover {
  background: #5a6268;
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

  .confirmation-message {
    padding: 20px 10px;
  }

  .confirmation-message .fa-check-circle {
    font-size: 60px;
  }

  .reservation-details {
    padding: 20px;
  }

  .choice-buttons {
    flex-direction: column;
  }

  .pay-now-btn, .home-btn {
    width: 100%;
  }
}
</style>

