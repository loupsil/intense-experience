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
    }
  },
  data() {
    return {
      selectedSuite: null
    }
  },
  methods: {
    selectSuite(suite) {
      if (this.availability[suite.Id]) {
        this.selectedSuite = suite
        this.$emit('suite-selected', suite)
      }
    },

    getSuiteBasePrice(suite) {
      // This would typically come from the pricing API
      // For now, we'll use some default prices based on suite type
      const basePrices = {
        'GAIA': 260,
        'EXTASE': 500,
        'INTENSE': 260,
        'EUPHORYA': 260,
        'IGNIS': 260,
        'KAIROS': 260,
        'AETHER': 260
      }

      const suiteName = suite.Names?.['fr-FR'] || suite.Name
      for (const [key, price] of Object.entries(basePrices)) {
        if (suiteName.includes(key)) {
          return price
        }
      }

      return 260 // Default price
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
