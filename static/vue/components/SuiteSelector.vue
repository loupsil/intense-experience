<template>
  <div class="suite-selector">
    <div class="suites-grid">
      <div
        v-for="suite in suites"
        :key="suite.Id"
        class="suite-card"
        :class="{
          selected: selectedSuite?.Id === suite.Id,
          available: availability[suite.Id],
          unavailable: !availability[suite.Id]
        }"
        @click="availability[suite.Id] ? selectSuite(suite) : null"
      >
        <div class="suite-header">
          <h3>{{ suite.Names['fr-FR'] || suite.Name }}</h3>
          <div class="availability-badge">
            <span
              :class="availability[suite.Id] ? 'available-badge' : 'unavailable-badge'"
            >
              {{ availability[suite.Id] ? 'Disponible' : 'Indisponible' }}
            </span>
          </div>
        </div>

        <div class="suite-image">
          <!-- Placeholder for suite image -->
          <div class="image-placeholder">
            <i class="fas fa-bed"></i>
          </div>
        </div>

        <div class="suite-details">
          <p class="suite-description">
            {{ suite.Descriptions?.['fr-FR'] || 'Suite exclusive avec équipements premium' }}
          </p>

          <div class="suite-features">
            <div class="feature">
              <i class="fas fa-users"></i>
              <span>Jusqu'à {{ suite.Capacity }} personnes</span>
            </div>
            <div class="feature">
              <i class="fas fa-expand-arrows-alt"></i>
              <span>{{ suite.ExtraCapacity || 0 }}m² supplémentaires</span>
            </div>
          </div>
        </div>

        <div class="suite-footer">
          <div class="pricing-info">
            <span class="price-label">À partir de</span>
            <span class="price-value">{{ getSuiteBasePrice(suite) }}€</span>
          </div>

          <button
            class="select-suite-btn"
            :disabled="!availability[suite.Id]"
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
      required: true
    },
    availability: {
      type: Object,
      required: true
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
    }
  },
  data() {
    return {
      selectedSuite: null,
      pricing: {}, // Will store pricing data for each suite
      loading: false
    }
  },
  watch: {
    serviceType: 'fetchPricing',
    startDate: 'fetchPricing',
    endDate: 'fetchPricing',
    pricing: {
      handler(newPricing) {
        this.$emit('pricing-updated', newPricing)
      },
      deep: true,
      immediate: true
    }
  },
  mounted() {
    this.fetchPricing()
  },
  methods: {
    selectSuite(suite) {
      if (this.availability[suite.Id]) {
        this.selectedSuite = suite
        this.$emit('suite-selected', suite)
      }
    },

    async fetchPricing() {
      this.loading = true
      try {
        const rateId = this.getRateId()
        const response = await fetch('/intense_experience-api/pricing', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            rate_id: rateId,
            start_date: this.startDate,
            end_date: this.endDate
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()
        if (result.status === 'success') {
          // Store pricing data by category ID
          this.pricing = {}
          if (Array.isArray(result.pricing)) {
            result.pricing.forEach(categoryPrice => {
              this.pricing[categoryPrice.CategoryId] = categoryPrice
            })
          }
        }
      } catch (error) {
        console.error('Error fetching pricing:', error)
        // Fallback to default pricing if API fails
        this.pricing = {}
      } finally {
        this.loading = false
      }
    },

    getRateId() {
      // Return appropriate rate ID based on service type
      if (this.serviceType === 'nuitée') {
        return 'ed9391ac-b184-4876-8cc1-b3850108b8b0' // Tarif Suites nuitée
      } else if (this.serviceType === 'journée') {
        return 'c3c2109d-984a-4ad4-978e-b3850108b8ad' // TARIF JOURNEE EN SEMAINE
      }
      return null
    },

    getSuiteBasePrice(suite) {
      // Get price from API pricing data
      const categoryPrice = this.pricing[suite.Id]
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

          console.log(`SuiteSelector: JOURNÉE PRICING COMPUTATION for ${suite.Names?.['fr-FR'] || suite.Name}:`)
          console.log(`  - Service Type: ${this.serviceType}`)
          console.log(`  - API returned ${hours} price entries`)
          console.log(`  - Corrected hours for booking: ${actualHours} (API includes boundaries)`)
          console.log(`  - Hourly rate: ${hourlyRate}€`)
          console.log(`  - Total calculation: ${actualHours} × ${hourlyRate}€ = ${correctedTotal}€`)
          console.log(`  - Date range: ${this.startDate} to ${this.endDate}`)

          return correctedTotal
        } else {
          // For nuitée, take the first price (daily rate)
          console.log(`SuiteSelector: NUITÉE PRICING for ${suite.Names?.['fr-FR'] || suite.Name}: ${categoryPrice.Prices[0]}€`)
          return categoryPrice.Prices[0]
        }
      }

      // No pricing data available
      console.log(`SuiteSelector: NO PRICING DATA for ${suite.Names?.['fr-FR'] || suite.Name} - returning N/A`)
      return 'N/A'
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
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.3s ease;
}

.suite-card.unavailable .select-suite-btn {
  background: #dc3545;
  cursor: not-allowed;
}

.select-suite-btn:hover:not(:disabled) {
  background: #0056b3;
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
