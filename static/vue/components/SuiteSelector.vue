<template>
  <div class="suite-selector">
    <!-- Loading state -->
    <div v-if="isLoadingSuites" class="suites-loading">
      <div class="spinner"></div>
      <p>Loading available suites...</p>
    </div>

    <!-- Suites loaded -->
    <div v-else class="suites-grid">
      <div
        v-for="suite in availableSuites"
        :key="suite.Id"
        class="suite-card"
        :class="{
          selected: selectedSuite?.Id === suite.Id,
          available: suiteAvailability[suite.Id],
          unavailable: !suiteAvailability[suite.Id]
        }"
        @click="suiteAvailability[suite.Id] ? selectSuite(suite) : null"
      >
        <div class="suite-header">
          <h3>{{ suite.Names['fr-FR'] || suite.Name }}</h3>
          <div class="availability-badge">
            <span
              :class="suiteAvailability[suite.Id] ? 'available-badge' : 'unavailable-badge'"
            >
              {{ suiteAvailability[suite.Id] ? 'Disponible' : 'Indisponible' }}
            </span>
          </div>
        </div>

        <div class="suite-image">
          <!-- Suite image or placeholder -->
          <div v-if="getCurrentImageUrl(suite.Id)" class="suite-image-container">
            <img
              :src="getCurrentImageUrl(suite.Id)"
              :alt="suite.Names['fr-FR'] || suite.Name"
              class="suite-img"
              :class="{ 'clickable': getImageCount(suite.Id) > 1 }"
              @click="cycleSuiteImage(suite.Id)"
            />
            <!-- Image indicators for multiple images -->
            <div v-if="getImageCount(suite.Id) > 1" class="image-indicators">
              <span
                v-for="(image, index) in suiteImages[suite.Id]"
                :key="index"
                class="image-dot"
                :class="{ 'active': (currentImageIndex[suite.Id] || 0) === index }"
              ></span>
            </div>
          </div>
          <div v-else class="image-placeholder">
            <i class="fas fa-bed"></i>
          </div>
        </div>

        <div class="suite-details">
          <p v-if="getSuiteDescription(suite)" class="suite-description">
            {{ getSuiteDescription(suite) }}
          </p>
        </div>

        <div class="suite-footer">
          <div class="pricing-info">
            <span class="price-label">À partir de</span>
            <span class="price-value">{{ getSuiteBasePrice(suite) }}€</span>
          </div>

          <button
            class="select-suite-btn"
            :disabled="!suiteAvailability[suite.Id]"
            @click.stop="selectSuite(suite)"
          >
            {{ selectedSuite?.Id === suite.Id ? 'Sélectionnée' : 'Sélectionner' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SuiteSelector',
  props: {
    suites: {
      type: Array,
      default: () => []
    },
    availability: {
      type: Object,
      default: () => ({})
    },
    serviceType: {
      type: String,
      required: true,
      validator: (value) => ['nuitée', 'journée'].includes(value)
    },
    startDate: {
      type: String,
      required: true
    },
    endDate: {
      type: String,
      required: true
    },
    pricing: {
      type: Object,
      default: () => ({})
    },
    preselectedSuite: {
      type: Object,
      default: null
    },
    service: {
      type: Object,
      default: null
    }
  },
  emits: [
    'suite-selected',
    'pricing-requested',
    'suites-loaded',
    'availability-checked',
    'pricing-updated',
    'pricing-calculated'
  ],
  data() {
    return {
      selectedSuite: this.preselectedSuite,
      availableSuites: [],
      suiteAvailability: {},
      suitePricing: {},
      suiteImages: {}, // Will now store arrays of images per suite
      currentImageIndex: {}, // Track current image index for each suite
      pricing: { total: 0, options: 0 },
      loading: false,
      isLoadingSuites: false
    }
  },
  watch: {
    serviceType: 'requestPricing',
    startDate: 'requestPricing',
    endDate: 'requestPricing',
    preselectedSuite: {
      handler(newSuite) {
        this.selectedSuite = newSuite
      },
      immediate: true
    },
    service: {
      handler(newService) {
        if (newService) {
          this.loadSuites()
        }
      },
      immediate: true
    }
  },
  mounted() {
    this.requestPricing()
    if (this.service) {
      this.loadSuites()
    }
  },
  methods: {
    selectSuite(suite) {
      if (this.suiteAvailability[suite.Id]) {
        this.selectedSuite = suite
        this.calculateSuitePricing()
        this.$emit('suite-selected', suite)
      }
    },

    requestPricing() {
      // Emit event to parent component to handle pricing
      this.$emit('pricing-requested', {
        serviceType: this.serviceType,
        startDate: this.startDate,
        endDate: this.endDate
      })
    },

    getSuiteBasePrice(suite) {
      // Get price from API pricing data
      const categoryPrice = this.suitePricing[suite.Id]
      if (categoryPrice && categoryPrice.Prices && categoryPrice.Prices.length > 0) {
        // For journée: sum all hourly prices, for nuitée: take the first (daily) price
        if (this.serviceType === 'journée') {
          const total = categoryPrice.Prices.reduce((sum, price) => sum + price, 0)
          const hours = categoryPrice.Prices.length
          const hourlyRate = categoryPrice.Prices[0]

          // For time-based bookings, the number of hours should be hours - 1
          // because the API includes both start and end boundaries
          const actualHours = hours - 1
          const correctedTotal = actualHours * hourlyRate

          return correctedTotal
        } else {
          // For nuitée, take the first price (daily rate)
          return categoryPrice.Prices[0]
        }
      }

      // No pricing data available
      return 'N/A'
    },

    getSuiteDescription(suite) {
      // Get the first available description from any language
      if (suite.Descriptions && typeof suite.Descriptions === 'object') {
        const descriptionKeys = Object.keys(suite.Descriptions)
        if (descriptionKeys.length > 0) {
          return suite.Descriptions[descriptionKeys[0]]
        }
      }
      // No fallback - return empty string if no descriptions are available
      return ''
    },

    async loadSuites() {
      if (!this.service) {
        console.warn('No service selected')
        return
      }

      this.isLoadingSuites = true

      try {
        const response = await fetch(`/intense_experience-api/suites?service_id=${this.service.Id}`)
        const data = await response.json()

        if (data.status === 'success') {
          this.availableSuites = data.suites
          await this.checkSuiteAvailability()
          await this.loadSuiteImages()
          this.$emit('suites-loaded', this.availableSuites)
        } else {
          console.error('Failed to load suites:', data.error)
        }
      } catch (error) {
        console.error('Error loading suites:', error)
      } finally {
        this.isLoadingSuites = false
      }
    },

    async loadSuiteImages() {
      if (!this.availableSuites || this.availableSuites.length === 0) {
        return
      }

      try {
        // Extract category IDs from suites
        const categoryIds = this.availableSuites.map(suite => suite.Id)

        // Get image assignments for these categories
        const assignmentsResponse = await fetch('/intense_experience-api/resource-category-images', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category_ids: categoryIds })
        })

        const assignmentsData = await assignmentsResponse.json()

        if (assignmentsData.status === 'success') {
          // Group all assignments by category, sorted by ordering
          const categoryImages = {}
          assignmentsData.image_assignments.forEach(assignment => {
            const categoryId = assignment.CategoryId
            if (!categoryImages[categoryId]) {
              categoryImages[categoryId] = []
            }
            categoryImages[categoryId].push(assignment)
          })

          // Sort images by ordering within each category
          Object.keys(categoryImages).forEach(categoryId => {
            categoryImages[categoryId].sort((a, b) => a.Ordering - b.Ordering)
          })

          // Extract all image IDs
          const allAssignments = Object.values(categoryImages).flat()
          const imageIds = allAssignments.map(assignment => assignment.ImageId)

          if (imageIds.length > 0) {
            // Get image URLs
            const urlsResponse = await fetch('/intense_experience-api/images/get-urls', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ image_ids: imageIds })
            })

            const urlsData = await urlsResponse.json()

            if (urlsData.status === 'success') {
              // Create image URL map
              const imageUrlMap = {}
              urlsData.image_urls.forEach(imageUrl => {
                imageUrlMap[imageUrl.ImageId] = imageUrl.Url
              })

              // Map URLs back to categories as arrays
              Object.keys(categoryImages).forEach(categoryId => {
                this.suiteImages[categoryId] = categoryImages[categoryId].map(assignment =>
                  imageUrlMap[assignment.ImageId]
                ).filter(url => url) // Remove any undefined URLs
                this.currentImageIndex[categoryId] = 0 // Start with first image
              })
            } else {
              console.error('Failed to fetch image URLs:', urlsData.error)
            }
          }
        } else {
          console.error('Failed to fetch image assignments:', assignmentsData.error)
        }
      } catch (error) {
        console.error('Error loading suite images:', error)
      }
    },

    async checkSuiteAvailability() {
      if (!this.startDate || !this.endDate) {
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

      try {
        for (const suite of suitesToCheck) {
          try {
            const payload = {
              service_id: this.service.Id,
              suite_id: suite.Id,
              start_date: this.startDate,
              end_date: this.endDate,
              booking_type: this.serviceType === 'journée' ? 'day' : 'night'
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
        this.$emit('availability-checked', this.suiteAvailability)
      } catch (error) {
        console.error('Error in availability check:', error)
      }
    },

    updateSuitePricing(pricing) {
      this.suitePricing = pricing
      if (this.selectedSuite) {
        this.calculateSuitePricing()
      }
      this.$emit('pricing-updated', pricing)
    },

    calculateSuitePricing() {
      if (!this.selectedSuite || !this.suitePricing) {
        return
      }

      // Get pricing for the selected suite
      const suitePricing = this.suitePricing[this.selectedSuite.Id]

      if (suitePricing && suitePricing.Prices && suitePricing.Prices.length > 0) {
        // For journée: sum all hourly prices, for nuitée: take the first (daily) price
        if (this.serviceType === 'journée') {
          const total = suitePricing.Prices.reduce((sum, price) => sum + price, 0)
          const hours = suitePricing.Prices.length
          const hourlyRate = suitePricing.Prices[0]

          // For time-based bookings, the number of hours should be hours - 1
          // because the API includes both start and end boundaries
          const actualHours = hours - 1
          const correctedTotal = actualHours * hourlyRate

          this.pricing.total = correctedTotal
        } else {
          // For nuitée, take the first price (daily rate) and multiply by number of nights
          const numberOfNights = this.calculateNumberOfNights()
          this.pricing.total = suitePricing.Prices[0] * numberOfNights
        }
      } else {
        // No pricing data available
        this.pricing.total = 'N/A'
      }
      this.$emit('pricing-calculated', { total: this.pricing.total, options: this.pricing.options })
    },

    calculateNumberOfNights() {
      if (!this.startDate || !this.endDate) {
        return 1
      }

      const start = new Date(this.startDate)
      const end = new Date(this.endDate)
      const diffTime = Math.abs(end - start)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      // For night stays, number of nights is typically diffDays - 1
      // But according to user, PerPersonPerTimeUnit should be for nights, so return diffDays
      return diffDays
    },

    cycleSuiteImage(suiteId) {
      const images = this.suiteImages[suiteId]
      if (!images || images.length <= 1) {
        return // No cycling needed if only one or no images
      }

      const currentIndex = this.currentImageIndex[suiteId] || 0
      const nextIndex = (currentIndex + 1) % images.length
      this.currentImageIndex[suiteId] = nextIndex
    },

    getCurrentImageUrl(suiteId) {
      const images = this.suiteImages[suiteId]
      if (!images || images.length === 0) {
        return null
      }
      const currentIndex = this.currentImageIndex[suiteId] || 0
      return images[currentIndex]
    },

    getImageCount(suiteId) {
      const images = this.suiteImages[suiteId]
      return images ? images.length : 0
    },

    getSuitePriceInfo() {
      if (!this.selectedSuite || !this.suitePricing) {
        return { price: this.pricing.total, calculation: '' }
      }

      const suitePricing = this.suitePricing[this.selectedSuite.Id]

      if (!suitePricing || !suitePricing.Prices || suitePricing.Prices.length === 0) {
        return { price: this.pricing.total, calculation: '' }
      }

      let calculation = ''
      let finalPrice = this.pricing.total

      if (this.serviceType === 'journée') {
        // For day stays, show the hourly calculation
        const hours = suitePricing.Prices.length
        const actualHours = hours - 1
        const hourlyRate = suitePricing.Prices[0]
        calculation = `${hourlyRate}€ × ${actualHours}h`
      } else {
        // For night stays, show daily rate × nights
        const dailyRate = suitePricing.Prices[0]
        const numberOfNights = this.calculateNumberOfNights()
        calculation = `${dailyRate}€ × ${numberOfNights} nuits`
      }

      return {
        price: finalPrice,
        calculation
      }
    }
  }
}
</script>

<style scoped>
.suite-selector {
  max-width: 1000px;
  margin: 0 auto;
}

.suites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.suite-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  background: #fff;
}

.suite-card:hover:not(.unavailable) {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.suite-card.available {
  border-color: #28a745;
}

.suite-card.unavailable {
  border-color: #dc3545;
  opacity: 0.7;
  cursor: not-allowed;
}

.suite-card.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
}

.suite-header {
  padding: 20px;
  background: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suite-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.availability-badge span {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.available-badge {
  background: #d4edda;
  color: #155724;
}

.unavailable-badge {
  background: #f8d7da;
  color: #721c24;
}

.suite-image {
  height: 150px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.suite-image-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.suite-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s ease;
}

.suite-img.clickable {
  cursor: pointer;
}

.suite-img.clickable:hover {
  opacity: 0.9;
}

.image-indicators {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
}

.image-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  transition: background-color 0.3s ease;
}

.image-dot.active {
  background: rgba(255, 255, 255, 1);
}

.image-placeholder {
  color: #6c757d;
  font-size: 48px;
}

.suite-details {
  padding: 20px;
}

.suite-description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.5;
}

.suite-features {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.feature i {
  color: #007bff;
  width: 16px;
}

.suite-footer {
  padding: 20px;
  background: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pricing-info {
  display: flex;
  flex-direction: column;
}

.price-label {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
}

.price-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.select-suite-btn {
  background: #c9a961;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.suite-card.unavailable .select-suite-btn {
  background: #dc3545;
  cursor: not-allowed;
}

.select-suite-btn:hover:not(:disabled) {
  background: #b89851;
}

.selection-summary {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 12px;
  border: 2px solid #007bff;
}

.selection-summary h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.selected-suite-info h4 {
  margin: 0 0 10px 0;
  color: #007bff;
}

.selected-suite-info p {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.5;
}

.suite-highlights {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.highlight {
  background: #007bff;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.suites-loading {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.suites-loading .spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #c9a961;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .suites-grid {
    grid-template-columns: 1fr;
  }

  .suite-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }

  .suite-footer {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .suite-highlights {
    justify-content: center;
  }
}
</style>
