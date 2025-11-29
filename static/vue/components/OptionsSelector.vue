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
        :class="{ selected: isSelected(product) }"
        @click="toggleOption(product)"
      >
        <!-- Product Image -->
        <div class="option-image">
          <img :src="getProductImage(product) || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PC9zdmc+'" :alt="product.Names?.['fr-FR'] || product.Name" />
        </div>

        <div class="option-header">
          <h4>{{ product.Names?.['fr-FR'] || product.Name }}</h4>
          <div class="option-price">
            <span class="price">{{ getProductPriceInfo(product).price }}€</span>
            <span v-if="product.Pricing?.Type === 'PerPerson'" class="per-person">/pers.</span>
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
    }
  },
  data() {
    return {
      localSelectedOptions: [...this.selectedOptions],
      isLoadingProducts: false,
      productImages: {} // Store image URLs by product ID
    }
  },
  mounted() {
    // Load products if we have a serviceId but no products loaded
    if (this.serviceId && this.products.length === 0) {
      this.loadProducts()
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
    }
  },
  methods: {
    isSelected(product) {
      return this.localSelectedOptions.some(opt => opt.Id === product.Id)
    },

    toggleOption(product) {
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

    getProductPrice(product) {
      // Extract base price from product data (Mews API format)
      let basePrice = null

      if (product.Price && typeof product.Price.GrossValue === 'number') {
        basePrice = product.Price.GrossValue
      } else if (product.Pricing && product.Pricing.Value && typeof product.Pricing.Value.GrossValue === 'number') {
        basePrice = product.Pricing.Value.GrossValue
      } else {
        // No price found - return error indicator
        console.error('Price not found for product:', product.Name || product.Id)
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
      // Extract base price from product data (Mews API format)
      let basePrice = null

      if (product.Price && typeof product.Price.GrossValue === 'number') {
        basePrice = product.Price.GrossValue
      } else if (product.Pricing && product.Pricing.Value && typeof product.Pricing.Value.GrossValue === 'number') {
        basePrice = product.Pricing.Value.GrossValue
      } else {
        // No price found - return error indicator
        console.error('Price not found for product:', product.Name || product.Id)
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
}

.price {
  font-size: 20px;
  font-weight: bold;
  color: var(--option-card-text, #333);
  display: block;
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
