<template>
  <div class="options-selector">
    <h3>Options et services supplémentaires</h3>
    <p class="options-intro">
      Personnalisez votre expérience avec nos options premium
    </p>

    <div class="options-grid">
      <div
        v-for="product in products"
        :key="product.Id"
        class="option-card"
        :class="{ selected: isSelected(product) }"
        @click="toggleOption(product)"
      >
        <div class="option-header">
          <h4>{{ product.Names?.['fr-FR'] || product.Name }}</h4>
          <div class="option-price">
            <span class="price">{{ getProductPrice(product) }}€</span>
            <span v-if="product.Pricing?.Type === 'PerPerson'" class="per-person">/pers.</span>
          </div>
        </div>

        <div class="option-description">
          <p>{{ getProductDescription(product) }}</p>
        </div>

        <div class="option-meta">
          <span class="category-badge">{{ getCategoryName(product) }}</span>
          <div class="selection-indicator">
            <i :class="isSelected(product) ? 'fas fa-check-circle' : 'far fa-circle'"></i>
          </div>
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
    }
  },
  data() {
    return {
      localSelectedOptions: [...this.selectedOptions]
    }
  },
  watch: {
    selectedOptions: {
      handler(newOptions) {
        this.localSelectedOptions = [...newOptions]
      },
      deep: true
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

    emitUpdate() {
      this.$emit('options-updated', [...this.localSelectedOptions])
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

    getProductDescription(product) {
      // Return description from product data if available
      return product.Descriptions?.['fr-FR'] || ''
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.option-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.option-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.option-card.selected {
  border-color: #007bff;
  background: #f8f9ff;
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.option-header h4 {
  margin: 0;
  color: #333;
  flex: 1;
}

.option-price {
  text-align: right;
}

.price {
  font-size: 20px;
  font-weight: bold;
  color: #007bff;
  display: block;
}

.per-person {
  font-size: 12px;
  color: #666;
}

.option-description {
  margin-bottom: 15px;
}

.option-description p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.option-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-badge {
  background: #f8f9fa;
  color: #666;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.selection-indicator {
  color: #007bff;
  font-size: 18px;
}

.option-card.selected .selection-indicator {
  color: #28a745;
}


/* Responsive */
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
