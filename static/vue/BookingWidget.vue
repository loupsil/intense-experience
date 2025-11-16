<template>
  <div class="booking-widget">
    <div class="booking-container">
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
          @date-selected="handleDateSelection"
          @dates-confirmed="nextStep"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
        </div>
      </div>

      <!-- Step 3: Suite Selection (only for general access) -->
      <div v-if="currentStep === 3 && !preselectedSuite" class="step">
        <h2>Choisissez votre suite</h2>
        <SuiteSelector
          :suites="availableSuites"
          :availability="suiteAvailability"
          @suite-selected="selectSuite"
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

      <!-- Step 4: Options & Upsells -->
      <div v-if="currentStep === 4" class="step">
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
            <span>{{ pricing.total }}€</span>
          </div>
          <div v-if="selectedOptions.length > 0" class="summary-item">
            <span>Options</span>
            <span>{{ pricing.options }}€</span>
          </div>
          <div class="summary-total">
            <strong>Total: {{ pricing.total + pricing.options }}€</strong>
          </div>
        </div>
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
          <button class="next-btn" @click="nextStep">Continuer</button>
        </div>
      </div>

      <!-- Step 5: Customer Information -->
      <div v-if="currentStep === 5" class="step">
        <h2>Vos informations</h2>
        <CustomerForm
          @customer-info="updateCustomerInfo"
        />
        <div class="step-navigation">
          <button class="prev-btn" @click="prevStep">Retour</button>
          <button
            class="next-btn"
            :disabled="!customerInfoComplete"
            @click="createReservation"
          >
            Finaliser la réservation
          </button>
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
              <span>{{ customerInfo.firstName }} {{ customerInfo.lastName }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Email :</span>
              <span>{{ customerInfo.email }}</span>
            </div>
            <div class="detail-item total">
              <span class="label">Total :</span>
              <span>{{ pricing.total + pricing.options }}€</span>
            </div>
          </div>
          <p class="payment-note">Le paiement sera traité ultérieurement.</p>
        </div>
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
    'CustomerForm': Vue.defineAsyncComponent(() => window.vueLoadModule('/static/vue/components/CustomerForm.vue', window.vueOptions))
  },
  props: {
    preselectedSuite: {
      type: Object,
      default: null
    },
    accessPoint: {
      type: String,
      default: 'general' // 'general' or 'specific'
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
      pricing: { total: 0, options: 0 },
      customerInfo: {},
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
    if (this.preselectedSuite) {
      this.currentStep = 2 // Skip suite selection
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

    selectService(service) {
      this.selectedService = service
      // JOURNEE service ID
      const JOURNEE_ID = '86fcc6a7-75ce-457a-a425-b3850108b6bf'
      this.bookingType = service.Id === JOURNEE_ID ? 'day' : 'night'
    },

    handleDateSelection(dates) {
      this.selectedDates = {
        start: dates.start,
        end: dates.end
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
        console.log('Fetching suites for service:', this.selectedService.Id)
        const response = await fetch(`/intense_experience-api/suites?service_id=${this.selectedService.Id}`)
        const data = await response.json()
        console.log('Suites response:', data)
        
        if (data.status === 'success') {
          this.availableSuites = data.suites
          console.log('Loaded', this.availableSuites.length, 'suites')
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
      console.log('='.repeat(80))
      console.log('FRONTEND: checkSuiteAvailability called')
      console.log('='.repeat(80))
      console.log('Selected dates:', this.selectedDates)
      console.log('Selected service:', this.selectedService?.Id)
      console.log('Booking type:', this.bookingType)
      console.log('Available suites count:', this.availableSuites?.length || 0)

      if (!this.selectedDates.start || !this.selectedDates.end) {
        console.warn('FRONTEND: No dates selected - aborting availability check')
        return
      }

      if (!this.availableSuites || this.availableSuites.length === 0) {
        console.warn('FRONTEND: No suites available to check - aborting availability check')
        return
      }

      this.loadingMessage = 'Vérification des disponibilités...'

      try {
        console.log(`FRONTEND: Checking availability for ${this.availableSuites.length} suite(s)`)
        for (const suite of this.availableSuites) {
          try {
            console.log(`FRONTEND: Checking suite: ${suite.Id} (${suite.Names?.['fr-FR'] || suite.Name})`)
            const payload = {
              service_id: this.selectedService.Id,
              suite_id: suite.Id,
              start_date: this.selectedDates.start,
              end_date: this.selectedDates.end,
              booking_type: this.bookingType
            }
            console.log('FRONTEND: Request payload:', JSON.stringify(payload, null, 2))

            const response = await fetch('/intense_experience-api/availability', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            })
            console.log(`FRONTEND: Response status for suite ${suite.Id}:`, response.status)

            const data = await response.json()
            console.log(`FRONTEND: Response data for suite ${suite.Id}:`, JSON.stringify(data, null, 2))

            if (data.status === 'success') {
              this.suiteAvailability[suite.Id] = data.available
              console.log(`FRONTEND: Suite ${suite.Id} availability result: ${data.available}`)
              if (!data.available) {
                console.warn(`FRONTEND: Suite ${suite.Id} is UNAVAILABLE. Conflicting reservations: ${data.conflicting_reservations?.length || 0}`)
              } else {
                console.log(`FRONTEND: Suite ${suite.Id} is AVAILABLE`)
              }
            } else {
              console.error(`FRONTEND: Availability check failed for suite ${suite.Id}:`, data.error)
              this.suiteAvailability[suite.Id] = false
            }
          } catch (error) {
            console.error(`FRONTEND: Error checking availability for suite ${suite.Id}:`, error)
            this.suiteAvailability[suite.Id] = false
          }
        }
        console.log('FRONTEND: Availability check complete for all suites')
        console.log('FRONTEND: Final availability results:', this.suiteAvailability)
      } catch (error) {
        console.error('FRONTEND: Error in availability check:', error)
      }
      console.log('='.repeat(80))
    },

    selectSuite(suite) {
      this.selectedSuite = suite
    },

    async loadProducts() {
      try {
        const response = await fetch('/intense_experience-api/products')
        const data = await response.json()
        if (data.status === 'success') {
          // Load all products without filtering
          this.availableProducts = data.products || []
          console.log('Loaded products for options:', this.availableProducts.length)
        }
      } catch (error) {
        console.error('Error loading products:', error)
      }
    },

    updateOptions(options) {
      this.selectedOptions = options
      this.calculatePricing()
    },

    async calculatePricing() {
      if (!this.selectedSuite || !this.selectedDates.start || !this.selectedDates.end) return

      try {
        // Convert dates to TimeUnit start times (23:00:00.000Z)
        const startDate = new Date(this.selectedDates.start)
        const endDate = new Date(this.selectedDates.end)
        
        // Set to 23:00 UTC for TimeUnit start
        startDate.setUTCHours(23, 0, 0, 0)
        
        // For end date, we need the TimeUnit that covers the checkout
        // If checkout is before 23:00, use previous day at 23:00
        // If checkout is at or after 23:00, use same day at 23:00
        if (endDate.getUTCHours() < 23) {
          endDate.setUTCDate(endDate.getUTCDate() - 1)
        }
        endDate.setUTCHours(23, 0, 0, 0)

        const response = await fetch('/intense_experience-api/pricing', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rate_id: 'ed9391ac-b184-4876-8cc1-b3850108b8b0', // Default rate
            start_date: startDate.toISOString(),
            end_date: endDate.toISOString(),
            suite_id: this.selectedSuite.Id
          })
        })
        const data = await response.json()
        if (data.status === 'success') {
          // Calculate total from pricing data
          const prices = data.pricing.Prices || []
          this.pricing.total = prices.reduce((sum, price) => sum + price, 0)

          // Calculate options pricing
          this.pricing.options = this.selectedOptions.reduce((sum, option) => {
            return sum + (option.Amount?.Value || 0)
          }, 0)
        }
      } catch (error) {
        console.error('Error calculating pricing:', error)
      }
    },

    updateCustomerInfo(info) {
      this.customerInfo = info
    },

    async createReservation() {
      this.loading = true
      this.loadingMessage = 'Création de votre réservation...'

      try {
        console.log('='.repeat(80))
        console.log('FRONTEND: Creating reservation flow')
        console.log('='.repeat(80))
        
        // First create customer
        console.log('FRONTEND: Step 1 - Creating customer')
        console.log('FRONTEND: Customer info:', this.customerInfo)
        
        const customerResponse = await fetch('/intense_experience-api/create-customer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.customerInfo)
        })
        
        console.log('FRONTEND: Customer response status:', customerResponse.status)
        const customerData = await customerResponse.json()
        console.log('FRONTEND: Customer response data:', customerData)

        if (customerData.status !== 'success') {
          console.error('FRONTEND: Failed to create customer:', customerData.error)
          throw new Error('Failed to create customer')
        }
        
        console.log('FRONTEND: Customer created successfully:', customerData.customer.Id)

        // Then create reservation
        console.log('FRONTEND: Step 2 - Creating reservation')
        const reservationPayload = {
          service_id: this.selectedService.Id,
          customer_id: customerData.customer.Id,
          suite_id: this.selectedSuite.Id,
          rate_id: 'ed9391ac-b184-4876-8cc1-b3850108b8b0',
          start_date: this.selectedDates.start,
          end_date: this.selectedDates.end,
          person_count: 2,
          options: this.selectedOptions
        }
        console.log('FRONTEND: Reservation payload:', reservationPayload)
        
        const reservationResponse = await fetch('/intense_experience-api/create-reservation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(reservationPayload)
        })
        
        console.log('FRONTEND: Reservation response status:', reservationResponse.status)
        const reservationData = await reservationResponse.json()
        console.log('FRONTEND: Reservation response data:', reservationData)

        if (reservationData.status !== 'success') {
          console.error('FRONTEND: Failed to create reservation:', reservationData.error)
          throw new Error('Failed to create reservation')
        }

        this.reservation = reservationData.reservation
        console.log('FRONTEND: Reservation created successfully:', this.reservation.Id)
        console.log('='.repeat(80))

        // Payment will be handled later - for now just show confirmation
        this.nextStep()

      } catch (error) {
        console.error('FRONTEND: Error creating reservation:', error)
        alert('Erreur lors de la création de la réservation. Veuillez réessayer.')
      } finally {
        this.loading = false
      }
    },

    async nextStep() {
      if (this.currentStep === 1) {
        this.currentStep = 2
      } else if (this.currentStep === 2) {
        if (this.accessPoint === 'general') {
          await this.loadSuites()
          this.currentStep = 3
        } else {
          this.loadProducts()
          this.calculatePricing()
          this.currentStep = 4
        }
      } else if (this.currentStep === 3) {
        this.loadProducts()
        this.calculatePricing()
        this.currentStep = 4
      } else if (this.currentStep === 4) {
        this.currentStep = 5
      } else if (this.currentStep === 5) {
        // Reservation creation handled separately
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

    formatDateRange(start, end) {
      if (!start || !end) return ''
      const startDate = new Date(start).toLocaleDateString('fr-FR')
      const endDate = new Date(end).toLocaleDateString('fr-FR')
      return `${startDate} - ${endDate}`
    }
  }
}
</script>

<style scoped>
.booking-widget {
  font-family: 'Arial', sans-serif;
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.booking-container {
  padding: 30px;
}

.step {
  min-height: 400px;
}

h2 {
  color: #333;
  margin-bottom: 30px;
  text-align: center;
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
  color: #333;
}

.service-card p {
  margin: 10px 0;
  color: #666;
  font-size: 14px;
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
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
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
  background: #f8f9fa;
  border-radius: 8px;
  padding: 25px;
  margin: 30px auto;
  max-width: 500px;
  text-align: left;
}

.reservation-details h3 {
  color: #333;
  margin-bottom: 20px;
  text-align: center;
  font-size: 20px;
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

.payment-note {
  color: #666;
  font-style: italic;
  margin-top: 25px;
  padding: 15px;
  background: #fff3cd;
  border-radius: 6px;
  border-left: 4px solid #ffc107;
}

/* Responsive */
@media (max-width: 768px) {
  .booking-container {
    padding: 20px;
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
}
</style>

