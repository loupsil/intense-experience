<template>
  <div class="options-selector">
    <!-- Loading state -->
    <div v-if="isLoadingProducts" class="options-loading">
      <div class="spinner"></div>
      <p>Loading available options...</p>
    </div>

    <!-- Options loaded -->
    <div v-else class="options-grid">
      <div
        v-for="product in products"
        :key="product.Id"
        class="option-card"
        :class="{ 
          selected: isSelected(product),
          unavailable: !isProductAvailable(product)
        }"
        @click="toggleOption(product)"
      >
        <!-- Unavailable overlay -->
        <div v-if="!isProductAvailable(product)" class="unavailable-overlay">
          <i class="fas fa-ban"></i>
          <span>Not available for selected dates</span>
        </div>
        
        <!-- Product Image -->
        <div class="option-image">
          <img :src="getProductImage(product) || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PC9zdmc+'" :alt="product.Names?.['fr-FR'] || product.Name" />
        </div>

        <div class="option-header">
          <h4>{{ product.Names?.['fr-FR'] || product.Name }}</h4>
          <div class="option-price">
            <span class="price">{{ formatUnitPrice(product) }}</span>
            <span v-if="isPerPersonCharging(product)" class="per-person">/pp</span>
          </div>
        </div>

        <div class="option-description">
          <p>{{ getProductDescription(product) }}</p>
        </div>


        <div class="category-badge-container">
          <span class="category-badge">{{ getCategoryName(product) }}</span>
        </div>

        <div class="selection-indicator">
          <i :class="isSelected(product) ? 'fas fa-check-circle' : 'far fa-circle'"></i>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
export default {
  name: 'OptionsSelector',
  props: {
    products: {
      type: Array,
      required: true
    },
    selectedOptions: {
      type: Array,
      default: () => []
    },
    serviceId: {
      type: String,
      default: ''
    },
    numberOfNights: {
      type: Number,
      default: 1
    },
    debugMode: {
      type: Boolean,
      default: false
    },
    bookingType: {
      type: String,
      default: 'day'
    },
    selectedSuite: {
      type: Object,
      default: null
    },
    checkInDate: {
      type: String,
      default: ''
    },
    checkOutDate: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      localSelectedOptions: [...this.selectedOptions],
      isLoadingProducts: false,
      productImages: {}, // Store image URLs by product ID
      timeOptionsAvailability: {
        early_checkin_available: true,
        late_checkout_available: true
      },
      isCheckingAvailability: false
    }
  },
  async mounted() {
    // Load products if we have a serviceId but no products loaded
    if (this.serviceId && this.products.length === 0) {
      this.loadProducts()
    }
    
    // Check time options availability for nuitée bookings
    if (this.bookingType === 'night' && this.selectedSuite && this.checkInDate && this.checkOutDate) {
      await this.checkTimeOptionsAvailability()
    }
    
    this.$nextTick(() => {
      this.updateBackgroundColor()
    })
  },
  watch: {
    selectedOptions: {
      handler(newOptions) {
        this.localSelectedOptions = [...newOptions]
      },
      deep: true
    },
    serviceId: {
      handler(newServiceId) {
        // Load products when service changes
        if (newServiceId && this.products.length === 0) {
          this.loadProducts()
        }
      }
    },
    bookingType: {
      handler() {
        this.$nextTick(() => {
          this.updateBackgroundColor()
        })
      },
      immediate: true
    },
    selectedSuite: {
      async handler(newSuite) {
        // Re-check availability when suite changes
        if (this.bookingType === 'night' && newSuite && this.checkInDate && this.checkOutDate) {
          await this.checkTimeOptionsAvailability()
        }
      }
    },
    checkInDate: {
      async handler(newDate) {
        // Re-check availability when check-in date changes
        if (this.bookingType === 'night' && this.selectedSuite && newDate && this.checkOutDate) {
          await this.checkTimeOptionsAvailability()
        }
      }
    },
    checkOutDate: {
      async handler(newDate) {
        // Re-check availability when check-out date changes
        if (this.bookingType === 'night' && this.selectedSuite && this.checkInDate && newDate) {
          await this.checkTimeOptionsAvailability()
        }
      }
    }
  },
  methods: {
    isSelected(product) {
      return this.localSelectedOptions.some(opt => opt.Id === product.Id)
    },
    
    isProductAvailable(product) {
      // For nuitée bookings, check if time-based options are available
      if (this.bookingType === 'night') {
        const productName = (product.Names?.['fr-FR'] || product.Name || '').toLowerCase()
        
        // Check early check-in availability
        if (productName.includes('arrivée anticipée')) {
          return this.timeOptionsAvailability.early_checkin_available
        }
        
        // Check late check-out availability
        if (productName.includes('départ tardif')) {
          return this.timeOptionsAvailability.late_checkout_available
        }
      }
      
      // All other products are available
      return true
    },

    toggleOption(product) {
      // Don't allow selection if product is not available
      if (!this.isProductAvailable(product)) {
        return
      }
      
      const index = this.localSelectedOptions.findIndex(opt => opt.Id === product.Id)
      if (index > -1) {
        this.localSelectedOptions.splice(index, 1)
      } else {
        this.localSelectedOptions.push(product)
      }
      this.emitUpdate()
    },

    calculateOptionsTotal() {
      // Calculate total price of all selected options
      return this.localSelectedOptions.reduce((sum, option) => {
        const price = this.getProductPriceInfo(option).price
        return sum + (typeof price === 'number' ? price : 0)
      }, 0)
    },

    emitUpdate() {
      // Add price information to selected options
      const optionsWithPrices = this.localSelectedOptions.map(option => ({
        ...option,
        calculatedPrice: this.getProductPriceInfo(option).price,
        priceCalculation: this.getProductPriceInfo(option).calculation
      }))

      // Calculate total options price
      const totalOptionsPrice = this.calculateOptionsTotal()

      // Check for special time-modifying products (for nuitée mode)
      const hasArriveeAnticipee = this.localSelectedOptions.some(option => {
        const name = option.Names?.['fr-FR'] || option.Name || ''
        return name.includes('Arrivée anticipée') || name.toLowerCase().includes('arrivée anticipée')
      })

      const hasDepartTardif = this.localSelectedOptions.some(option => {
        const name = option.Names?.['fr-FR'] || option.Name || ''
        return name.includes('Départ tardif') || name.toLowerCase().includes('départ tardif')
      })

      // Emit selected options, total price, and time modification flags
      this.$emit('options-updated', optionsWithPrices, totalOptionsPrice, {
        hasArriveeAnticipee,
        hasDepartTardif
      })
    },

    getBasePrice(product) {
      if (product.Price && typeof product.Price.GrossValue === 'number') {
        return product.Price.GrossValue
      }
      if (product.Pricing && product.Pricing.Value && typeof product.Pricing.Value.GrossValue === 'number') {
        return product.Pricing.Value.GrossValue
      }

      console.error('Price not found for product:', product.Name || product.Id)
      return null
    },

    formatUnitPrice(product) {
      const basePrice = this.getBasePrice(product)
      if (typeof basePrice === 'number') {
        return `${basePrice}€`
      }
      return 'N/A'
    },

    isPerPersonCharging(product) {
      const charging = product.Charging
      const pricingType = product.Pricing?.Type
      return charging === 'PerPerson' ||
        charging === 'PerPersonPerTimeUnit' ||
        pricingType === 'PerPerson' ||
        pricingType === 'PerPersonPerTimeUnit'
    },

    getProductPrice(product) {
      const basePrice = this.getBasePrice(product)
      if (typeof basePrice !== 'number') {
        return 'N/A'
      }

      // Calculate price based on charging type
      const charging = product.Charging

      switch (charging) {
        case 'Once':
          return basePrice
        case 'PerPerson':
          return basePrice * 2 // For 2 people
        case 'PerPersonPerTimeUnit':
          return basePrice * 2 * this.numberOfNights // For 2 people per night
        default:
          return basePrice
      }
    },

    getProductPriceInfo(product) {
      const basePrice = this.getBasePrice(product)
      if (typeof basePrice !== 'number') {
        return { calculation: 'N/A', price: 'N/A' }
      }

      // Calculate price based on charging type
      const charging = product.Charging
      let calculation = ''
      let finalPrice = basePrice

      switch (charging) {
        case 'Once':
          calculation = `${basePrice}€`
          finalPrice = basePrice
          break
        case 'PerPerson':
          calculation = `${basePrice}€ × 2`
          finalPrice = basePrice * 2
          break
        case 'PerPersonPerTimeUnit':
          calculation = `${basePrice}€ × 2 × ${this.numberOfNights}`
          finalPrice = basePrice * 2 * this.numberOfNights
          break
        default:
          calculation = `${basePrice}€`
          finalPrice = basePrice
      }

      return {
        calculation,
        price: finalPrice
      }
    },

    getProductDescription(product) {
      // Return description from product data if available
      return product.Description || product.Descriptions?.['fr-FR'] || ''
    },

    getCategoryName(product) {
      // Categorize products
      const productName = (product.Names?.['fr-FR'] || product.Name).toLowerCase()

      if (productName.includes('petit') || productName.includes('déjeuner')) {
        return 'Restauration'
      } else if (productName.includes('check') || productName.includes('arrivée') || productName.includes('départ')) {
        return 'Flexibilité'
      } else if (productName.includes('massage') || productName.includes('spa')) {
        return 'Bien-être'
      } else {
        return 'Premium'
      }
    },

    getChargingInfo(product) {
      // Display charging information as is
      const charging = product.Charging

      if (!charging) return ''

      return charging
    },

    async loadProducts() {
      if (!this.serviceId) {
        console.warn('OptionsSelector: No serviceId provided for loading products')
        return
      }

      this.isLoadingProducts = true

      try {
        const response = await fetch('/intense_experience-api/products')
        const data = await response.json()
        if (data.status === 'success') {
          // Filter products by selected service
          const allProducts = data.products || []
          const filteredProducts = allProducts.filter(product =>
            product.ServiceId === this.serviceId
          )

          // Load images for products that have ImageIds
          await this.loadProductImages(filteredProducts)

          // Emit the loaded products
          this.$emit('products-loaded', filteredProducts)
        } else {
          console.error('Failed to load products:', data.error)
        }
      } catch (error) {
        console.error('Error loading products:', error)
      } finally {
        this.isLoadingProducts = false
      }
    },

    async loadProductImages(products) {
      // Collect all image IDs from products
      const imageIds = []
      products.forEach(product => {
        if (product.ImageIds && product.ImageIds.length > 0) {
          // Take the first image ID for each product
          imageIds.push(product.ImageIds[0])
        }
      })

      if (imageIds.length === 0) {
        return // No images to load
      }

      try {
        const response = await fetch('/intense_experience-api/images/get-urls', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ image_ids: imageIds })
        })

        const data = await response.json()
        if (data.status === 'success' && data.image_urls) {
          // Map image URLs back to products
          data.image_urls.forEach(imageUrl => {
            // Find the product that has this image ID
            const product = products.find(p =>
              p.ImageIds && p.ImageIds.includes(imageUrl.ImageId)
            )
            if (product) {
              this.productImages[product.Id] = imageUrl.Url
            }
          })
        } else {
          console.error('Failed to load product images:', data.error)
        }
      } catch (error) {
        console.error('Error loading product images:', error)
      }
    },

    getProductImage(product) {
      return this.productImages[product.Id] || null
    },

    updateBackgroundColor() {
      if (this.bookingType === 'night') {
        this.$el.style.setProperty('--option-card-background', '#161616')
        this.$el.style.setProperty('--option-card-text', '#ffffff')
        this.$el.style.setProperty('--option-badge-background', '#333')
        this.$el.style.setProperty('--option-selected-background', '#161616')
        this.$el.style.setProperty('--option-selected-box-shadow', '0px 0px 5px 5px rgb(255 255 255 / 30%)')
      } else if (this.bookingType === 'day') {
        this.$el.style.setProperty('--option-card-background', '#E9E9DF')
        this.$el.style.setProperty('--option-card-text', '#333')
        this.$el.style.setProperty('--option-badge-background', '#f8f9fa')
        this.$el.style.setProperty('--option-selected-background', '#f8f9ff')
        this.$el.style.setProperty('--option-selected-box-shadow', 'none')
      }
    },
    
    async checkTimeOptionsAvailability() {
      // Only check for nuitée bookings
      if (this.bookingType !== 'night' || !this.selectedSuite || !this.checkInDate || !this.checkOutDate) {
        return
      }
      
      this.isCheckingAvailability = true
      
      try {
        const response = await fetch('/intense_experience-api/check-time-options-availability', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            suite_id: this.selectedSuite.Id,
            check_in_date: this.checkInDate,
            check_out_date: this.checkOutDate
          })
        })
        
        const data = await response.json()
        
        if (data.status === 'success') {
          this.timeOptionsAvailability = {
            early_checkin_available: data.early_checkin_available,
            late_checkout_available: data.late_checkout_available
          }
          
          if (this.debugMode) {
            console.log('Time options availability updated:', this.timeOptionsAvailability)
          }
          
          // Remove any selected options that are no longer available
          this.localSelectedOptions = this.localSelectedOptions.filter(option => {
            return this.isProductAvailable(option)
          })
          
          // Emit update if we removed any options
          if (this.localSelectedOptions.length !== this.selectedOptions.length) {
            this.emitUpdate()
          }
        } else {
          console.error('Failed to check time options availability:', data.error)
        }
      } catch (error) {
        console.error('Error checking time options availability:', error)
      } finally {
        this.isCheckingAvailability = false
      }
    }
  }
}
</script>

<style scoped>
.options-selector {
  max-width: 800px;
  margin: 0 auto;
}

.options-selector h3 {
  text-align: center;
  color: #333;
  margin-bottom: 10px;
}

.options-intro {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
  font-style: italic;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.option-card {
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--option-card-background, #fff);
  color: var(--option-card-text, #333);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border:none;
  position: relative;
  padding-bottom: 50px;
}

.option-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.option-card.selected {
  border-color: #007bff;
  background: var(--option-selected-background, #f8f9ff);
  box-shadow: var(--option-selected-box-shadow, none);
}

.option-card.unavailable {
  opacity: 0.6;
  cursor: not-allowed;
  position: relative;
}

.option-card.unavailable:hover {
  transform: none;
}

.unavailable-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  gap: 10px;
  z-index: 10;
  padding: 20px;
  text-align: center;
}

.unavailable-overlay i {
  font-size: 32px;
}

.unavailable-overlay span {
  font-size: 14px;
  font-weight: 500;
}

.option-image {
  margin-bottom: 15px;
  border-radius: 8px;
  overflow: hidden;
  background: #f8f9fa;
}

.option-image img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.option-card:hover .option-image img {
  transform: scale(1.02);
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.option-header h4 {
  margin: 0;
  color: var(--option-card-text, #333);
  flex: 1;
}

.option-price {
  text-align: right;
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 6px;
}

.price {
  font-size: 20px;
  font-weight: bold;
  color: var(--option-card-text, #333);
}

.per-person {
  font-size: 12px;
  color: var(--option-card-text, #333);
}

.calculation {
  font-size: 11px;
  color: var(--option-card-text, #333);
  font-weight: normal;
  margin-left: 4px;
}

.option-description {
  margin-bottom: 15px;
}

.option-description p {
  margin: 0;
  color: var(--option-card-text, #333);
  line-height: 1.5;
}


.category-badge-container {
  position: absolute;
  bottom: 15px;
  left: 15px;
}

.category-badge {
  background: var(--option-badge-background, #f8f9fa);
  color: var(--option-card-text, #333);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}


.selection-indicator {
  color: var(--option-card-text, #333);
  font-size: 18px;
  position: absolute;
  bottom: 15px;
  right: 15px;
}

.option-card.selected .selection-indicator {
  color: #b89851;
}

.options-loading {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.options-loading .spinner {
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
@media (max-width: 1024px) {
  .options-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .options-grid {
    grid-template-columns: 1fr;
  }

  .option-header {
    flex-direction: column;
    gap: 10px;
  }

  .options-actions {
    flex-direction: column;
  }
}
</style>
