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
        v-for="suite in sortedSuites"
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
              {{ suiteAvailability[suite.Id] ? 'Available' : 'Unavailable' }}
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
              :class="{ 
                'clickable': getImageCount(suite.Id) > 1,
                'grayscale': !suiteAvailability[suite.Id]
              }"
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
            <span class="price-value">{{ getSuitePriceDisplay(suite) }}</span>
          </div>
        </div>

        <div class="selection-indicator">
          <i :class="selectedSuite?.Id === suite.Id ? 'fas fa-check-circle' : 'far fa-circle'"></i>
        </div>

        <!-- Gold glitter animation for selected suite (only for night bookings) -->
        <div v-if="selectedSuite?.Id === suite.Id && bookingType === 'night'" class="gold-glitter-overlay">
          <img 
            :src="glitterGifUrl"
            alt="Gold glitter effect"
            class="glitter-gif"
            @error="handleGlitterError"
          />
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
    pricingCalculator: {
      type: Function,
      default: null
    },
    priceDisplayCalculator: {
      type: Function,
      default: null
    },
    service: {
      type: Object,
      default: null
    }
  },
  computed: {
    bookingType() {
      return this.serviceType === 'journée' ? 'day' : 'night'
    },
    sortedSuites() {
      // Define the desired order for suite names
      const suiteOrder = ['GAIA', 'EXTASE', 'INTENSE']
      
      // Sort suites to show available ones first, then by suite order
      return [...this.availableSuites].sort((a, b) => {
        const aAvailable = this.suiteAvailability[a.Id] ? 1 : 0
        const bAvailable = this.suiteAvailability[b.Id] ? 1 : 0
        
        // Primary sort: available first (descending order)
        if (bAvailable !== aAvailable) {
          return bAvailable - aAvailable
        }
        
        // Secondary sort: by suite order (GAIA, EXTASE, INTENSE)
        const aName = (a.Names && a.Names['fr-FR']) || a.Name || ''
        const bName = (b.Names && b.Names['fr-FR']) || b.Name || ''
        
        // Find the index of each suite in the order array
        const aIndex = suiteOrder.findIndex(name => aName.toUpperCase().includes(name))
        const bIndex = suiteOrder.findIndex(name => bName.toUpperCase().includes(name))
        
        // If both found in order, sort by their position
        if (aIndex !== -1 && bIndex !== -1) {
          return aIndex - bIndex
        }
        
        // If only one found, it comes first
        if (aIndex !== -1) return -1
        if (bIndex !== -1) return 1
        
        // If neither found, maintain original order
        return 0
      })
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
      calculatedPricing: { total: 0, options: 0 },
      suitePriceCalculation: '', // Cache the calculation string to prevent flicker
      loading: false,
      isLoadingSuites: false,
      _isMounted: false,
      glitterGifUrl: '/static/images/glitter2.gif' // Gold glitter GIF
    }
  },
  watch: {
    serviceType: 'requestPricing',
    startDate: 'requestPricing',
    endDate: 'requestPricing',
    pricing: {
      handler(newPricing) {
        this.updateSuitePricing(newPricing)
      },
      immediate: true,
      deep: true
    },
    preselectedSuite: {
      handler(newSuite) {
        this.selectedSuite = newSuite
      }
    },
    service: {
      handler(newService) {
        if (newService && this._isMounted) {
          this.loadSuites()
        }
      },
      immediate: false
    },
    bookingType: {
      handler() {
        this.$nextTick(() => {
          this.updateBackgroundColor()
        })
      },
      immediate: true
    }
  },
  mounted() {
    this._isMounted = true
    this.requestPricing()
    if (this.service) {
      this.loadSuites()
    }
    this.$nextTick(() => {
      this.updateBackgroundColor()
    })
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

    getSuitePriceDisplay(suite) {
      // Get price from API pricing data
      const categoryPrice = this.suitePricing[suite.Id]
      if (categoryPrice && categoryPrice.Prices && categoryPrice.Prices.length > 0) {
        if (this.serviceType === 'journée') {
          // For journée: show the total price
          const total = categoryPrice.Prices.reduce((sum, price) => sum + price, 0)
          const hours = categoryPrice.Prices.length
          const hourlyRate = categoryPrice.Prices[0]
          const actualHours = hours - 1
          const correctedTotal = actualHours * hourlyRate

          return `${correctedTotal}€`
        } else {
          // For nuitée: use shared pricing calculation logic
          if (this.priceDisplayCalculator) {
            const result = this.priceDisplayCalculator(categoryPrice, this.startDate, this.endDate)
            if (result.calculation) {
              return `${result.total}€ (${result.calculation})`
            } else {
              return `${result.total}€`
            }
          } else {
            // Fallback to local logic if shared calculator not available
            const numberOfNights = this.calculateNumberOfNights()
            const total = categoryPrice.Prices[0] * numberOfNights
            return `${total}€ (${numberOfNights}x${categoryPrice.Prices[0]}€)`
          }
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
      if (!this.selectedSuite || !this.suitePricing || !this.pricingCalculator) {
        return
      }

      // Use the pricing calculator function passed from parent
      const pricingResult = this.pricingCalculator(
        this.suitePricing,
        this.startDate,
        this.endDate,
        this.selectedSuite
      )

      this.calculatedPricing.total = pricingResult.total
      this.suitePriceCalculation = pricingResult.calculation

      this.$emit('pricing-calculated', {
        total: this.calculatedPricing.total,
        options: this.calculatedPricing.options,
        calculation: this.suitePriceCalculation
      })
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

    updateBackgroundColor() {
      if (this.bookingType === 'night') {
        this.$el.style.setProperty('--suite-card-background', '#161616')
        this.$el.style.setProperty('--suite-card-text', '#ffffff')
        this.$el.style.setProperty('--suite-badge-background', '#333')
        this.$el.style.setProperty('--suite-selected-background', '#161616')
        this.$el.style.setProperty('--suite-selected-box-shadow', '0px 0px 5px 5px rgb(255 255 255 / 30%)')
      } else if (this.bookingType === 'day') {
        this.$el.style.setProperty('--suite-card-background', '#E9E9DF')
        this.$el.style.setProperty('--suite-card-text', '#333')
        this.$el.style.setProperty('--suite-badge-background', '#f8f9fa')
        this.$el.style.setProperty('--suite-selected-background', '#f8f9ff')
        this.$el.style.setProperty('--suite-selected-box-shadow', 'none')
      }
    },

    getSuitePriceInfo() {
      return {
        price: this.calculatedPricing.total,
        calculation: this.suitePriceCalculation
      }
    },

    handleGlitterError(event) {
      // Fallback to alternative gold glitter GIF if the first one fails
      console.warn('Primary glitter GIF failed to load, trying fallback')
      event.target.src = 'https://media.giphy.com/media/xTiTnLZ2dqfYWY9ybm/giphy.gif'
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
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--suite-card-background, #fff);
  color: var(--suite-card-text, #333);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border:none;
  position: relative;
  padding-bottom: 60px;
}

.suite-card:hover:not(.unavailable) {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.suite-card.available {
  border-color: #28a745;
}

.suite-card.unavailable {
  border-color: #999;
  cursor: not-allowed;
  background: #808080 !important;
  color: #e0e0e0 !important;
  opacity: 0.5;
}

.suite-card.selected {
  border-color: #007bff;
  background: var(--suite-selected-background, #f8f9ff);
  box-shadow: var(--suite-selected-box-shadow, 0 0 0 3px rgba(0,123,255,0.25));
}

.suite-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.suite-header h3 {
  margin: 0;
  color: var(--suite-card-text, #333);
}

.suite-card.unavailable .suite-header h3,
.suite-card.unavailable .suite-description,
.suite-card.unavailable .price-value,
.suite-card.unavailable .selection-indicator {
  color: #e0e0e0 !important;
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
  background: var(--suite-badge-background, #f8f9fa);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  margin-top: 15px;
  margin-bottom: 15px;
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

.suite-img.grayscale {
  filter: grayscale(100%);
  opacity: 0.6;
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

.suite-description {
  color: var(--suite-card-text, #333);
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
  position: absolute;
  bottom: 15px;
  left: 15px;
}

.pricing-info {
  display: flex;
  flex-direction: column;
  text-align: center;
}

.price-value {
  font-size: 20px;
  font-weight: bold;
  color: var(--suite-card-text, #333);
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

.selection-indicator {
  color: var(--suite-card-text, #333);
  font-size: 18px;
  position: absolute;
  bottom: 15px;
  right: 15px;
}

.suite-card.selected .selection-indicator {
  color: #b89851;
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
    text-align: center;
  }

  .suite-highlights {
    justify-content: center;
  }
}

/* Gold glitter overlay for selected suite */
.gold-glitter-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  border-radius: 12px;
  overflow: hidden;
  z-index: 10;
}

.glitter-gif {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.4;
  mix-blend-mode: screen;
  animation: glitterPulse 3s ease-in-out infinite;
}

@keyframes glitterPulse {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
