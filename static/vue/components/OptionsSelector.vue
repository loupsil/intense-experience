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

    <div v-if="selectedOptions.length > 0" class="selected-options-summary">
      <h4>Options sélectionnées</h4>
      <div class="selected-list">
        <div
          v-for="option in selectedOptions"
          :key="option.Id"
          class="selected-option-item"
        >
          <span class="option-name">{{ option.Names?.['fr-FR'] || option.Name }}</span>
          <span class="option-price">{{ getProductPrice(option) }}€</span>
          <button class="remove-option" @click.stop="removeOption(option)">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <div class="options-total">
        <strong>Total options: {{ calculateOptionsTotal() }}€</strong>
      </div>
    </div>

    <div class="options-actions">
      <button class="skip-options-btn" @click="skipOptions">
        Passer les options
      </button>
      <button
        class="continue-btn"
        @click="confirmOptions"
      >
        Continuer avec {{ selectedOptions.length }} option(s)
      </button>
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

    removeOption(option) {
      const index = this.localSelectedOptions.findIndex(opt => opt.Id === option.Id)
      if (index > -1) {
        this.localSelectedOptions.splice(index, 1)
        this.emitUpdate()
      }
    },

    emitUpdate() {
      this.$emit('options-updated', [...this.localSelectedOptions])
    },

    getProductPrice(product) {
      // Extract price from product data
      if (product.Amounts && product.Amounts.length > 0) {
        const amount = product.Amounts[0]
        if (amount.Value) {
          return amount.Value
        }
      }

      // Fallback prices based on product type
      const fallbackPrices = {
        'Petit-déjeuner': 25,
        'Early check-in': 50,
        'Late check-out': 75,
        'Champagne': 85,
        'Massage': 120,
        'Spa': 150
      }

      const productName = product.Names?.['fr-FR'] || product.Name
      for (const [key, price] of Object.entries(fallbackPrices)) {
        if (productName.toLowerCase().includes(key.toLowerCase())) {
          return price
        }
      }

      return 0
    },

    getProductDescription(product) {
      // Try to get description from product data
      if (product.Descriptions?.['fr-FR']) {
        return product.Descriptions['fr-FR']
      }

      // Fallback descriptions
      const descriptions = {
        'Petit-déjeuner': 'Déjeuner gastronomique servi en suite',
        'Early check-in': 'Arrivée anticipée (à partir de 14h pour les journées)',
        'Late check-out': 'Départ différé (jusqu\'à 12h pour les nuitées)',
        'Champagne': 'Bouteille de champagne premium',
        'Massage': 'Massage relaxant d\'1 heure',
        'Spa': 'Accès au spa pendant votre séjour'
      }

      const productName = product.Names?.['fr-FR'] || product.Name
      for (const [key, desc] of Object.entries(descriptions)) {
        if (productName.toLowerCase().includes(key.toLowerCase())) {
          return desc
        }
      }

      return 'Service supplémentaire premium'
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

    calculateOptionsTotal() {
      return this.localSelectedOptions.reduce((total, option) => {
        return total + this.getProductPrice(option)
      }, 0)
    },

    skipOptions() {
      this.localSelectedOptions = []
      this.emitUpdate()
      this.$emit('options-confirmed', [])
    },

    confirmOptions() {
      this.emitUpdate()
      this.$emit('options-confirmed', [...this.localSelectedOptions])
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

.selected-options-summary {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 12px;
  margin-bottom: 30px;
}

.selected-options-summary h4 {
  margin: 0 0 20px 0;
  color: #333;
}

.selected-list {
  margin-bottom: 20px;
}

.selected-option-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e0e0e0;
}

.option-name {
  flex: 1;
  color: #333;
}

.selected-option-item .option-price {
  font-weight: bold;
  color: #007bff;
  margin-right: 15px;
}

.remove-option {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s ease;
}

.remove-option:hover {
  background: #c82333;
}

.options-total {
  text-align: right;
  font-size: 18px;
  color: #333;
  padding-top: 15px;
  border-top: 2px solid #007bff;
}

.options-actions {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.skip-options-btn, .continue-btn {
  flex: 1;
  padding: 15px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.skip-options-btn {
  background: #6c757d;
  color: white;
  border: none;
}

.skip-options-btn:hover {
  background: #5a6268;
}

.continue-btn {
  background: #28a745;
  color: white;
  border: none;
}

.continue-btn:hover {
  background: #218838;
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
