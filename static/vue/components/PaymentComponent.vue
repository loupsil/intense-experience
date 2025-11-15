<template>
  <div class="payment-component">
    <div class="payment-success" v-if="paymentCompleted">
      <div class="success-icon">
        <i class="fas fa-check-circle"></i>
      </div>
      <h2>Réservation confirmée !</h2>
      <p>Votre paiement a été traité avec succès.</p>

      <div class="reservation-details">
        <h3>Détails de votre réservation</h3>
        <div class="detail-item">
          <span>Référence:</span>
          <strong>{{ reservation?.Identifier }}</strong>
        </div>
        <div class="detail-item">
          <span>Montant payé:</span>
          <strong>{{ amount }}€</strong>
        </div>
        <div class="detail-item">
          <span>Statut:</span>
          <span class="status-confirmed">Confirmée</span>
        </div>
      </div>

      <div class="next-steps">
        <h3>Prochaines étapes</h3>
        <ul>
          <li>Un email de confirmation vous a été envoyé</li>
          <li>Vous recevrez un SMS 24h avant votre arrivée avec les instructions</li>
          <li>Contactez-nous si vous avez des questions</li>
        </ul>
      </div>

      <div class="action-buttons">
        <button class="download-btn" @click="downloadConfirmation">
          <i class="fas fa-download"></i>
          Télécharger la confirmation
        </button>
        <button class="home-btn" @click="goHome">
          Retour à l'accueil
        </button>
      </div>
    </div>

    <div class="payment-processing" v-else-if="processingPayment">
      <div class="processing-icon">
        <div class="spinner"></div>
      </div>
      <h2>Traitement du paiement...</h2>
      <p>Veuillez patienter pendant que nous sécurisons votre transaction.</p>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </div>

    <div class="payment-form" v-else>
      <div class="payment-header">
        <h2>Finaliser votre réservation</h2>
        <div class="amount-summary">
          <div class="total-amount">
            <span class="label">Total à payer:</span>
            <span class="value">{{ amount }}€</span>
          </div>
        </div>
      </div>

      <div class="payment-methods">
        <h3>Mode de paiement</h3>
        <div class="method-selector">
          <div class="method-option">
            <input
              type="radio"
              id="card"
              value="card"
              v-model="selectedMethod"
            >
            <label for="card" class="method-label">
              <div class="method-info">
                <i class="fas fa-credit-card"></i>
                <div>
                  <div class="method-name">Carte bancaire</div>
                  <div class="method-desc">Visa, Mastercard, American Express</div>
                </div>
              </div>
            </label>
          </div>

          <div class="method-option">
            <input
              type="radio"
              id="bank"
              value="bank"
              v-model="selectedMethod"
            >
            <label for="bank" class="method-label">
              <div class="method-info">
                <i class="fas fa-university"></i>
                <div>
                  <div class="method-name">Virement bancaire</div>
                  <div class="method-desc">Paiement par virement (délai de traitement)</div>
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      <div class="secure-payment-notice">
        <div class="security-badges">
          <i class="fas fa-shield-alt"></i>
          <span>Paiement 100% sécurisé</span>
        </div>
        <div class="security-info">
          <i class="fas fa-lock"></i>
          <span>SSL chiffré</span>
        </div>
      </div>

      <div class="payment-actions">
        <button
          class="pay-btn"
          :disabled="!selectedMethod || processingPayment"
          @click="processPayment"
        >
          <span v-if="processingPayment">
            <div class="btn-spinner"></div>
            Traitement...
          </span>
          <span v-else>
            Payer {{ amount }}€
          </span>
        </button>

        <p class="payment-note">
          En cliquant sur "Payer", vous acceptez nos conditions générales et confirmez votre réservation.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaymentComponent',
  props: {
    reservation: {
      type: Object,
      default: null
    },
    paymentUrl: {
      type: String,
      default: ''
    },
    amount: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      selectedMethod: 'card',
      processingPayment: false,
      paymentCompleted: false,
      progressPercent: 0,
      progressInterval: null
    }
  },
  methods: {
    async processPayment() {
      if (!this.selectedMethod) return

      this.processingPayment = true
      this.progressPercent = 0

      // Simulate payment processing with progress
      this.progressInterval = setInterval(() => {
        this.progressPercent += Math.random() * 15
        if (this.progressPercent >= 100) {
          this.progressPercent = 100
          clearInterval(this.progressInterval)
          setTimeout(() => {
            this.completePayment()
          }, 500)
        }
      }, 200)
    },

    completePayment() {
      this.processingPayment = false
      this.paymentCompleted = true

      // In a real implementation, you would redirect to the payment URL
      // window.location.href = this.paymentUrl
    },

    downloadConfirmation() {
      // Simulate PDF download
      alert('Téléchargement de la confirmation PDF - Fonctionnalité à implémenter')
    },

    goHome() {
      // Reset the booking process
      this.$emit('reset-booking')
    }
  },

  beforeUnmount() {
    if (this.progressInterval) {
      clearInterval(this.progressInterval)
    }
  }
}
</script>

<style scoped>
.payment-component {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.payment-success {
  padding: 40px 20px;
}

.success-icon {
  font-size: 64px;
  color: #28a745;
  margin-bottom: 20px;
}

.payment-success h2 {
  color: #28a745;
  margin-bottom: 15px;
}

.payment-success p {
  color: #666;
  margin-bottom: 30px;
}

.reservation-details {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 12px;
  margin-bottom: 30px;
  text-align: left;
}

.reservation-details h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.status-confirmed {
  color: #28a745;
  font-weight: bold;
}

.next-steps {
  text-align: left;
  margin-bottom: 30px;
}

.next-steps h3 {
  margin-bottom: 15px;
  color: #333;
}

.next-steps ul {
  padding-left: 20px;
}

.next-steps li {
  margin-bottom: 8px;
  color: #666;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.download-btn, .home-btn {
  padding: 12px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.download-btn {
  background: #007bff;
  color: white;
  border: none;
}

.download-btn:hover {
  background: #0056b3;
}

.home-btn {
  background: #6c757d;
  color: white;
  border: none;
}

.home-btn:hover {
  background: #5a6268;
}

.payment-processing {
  padding: 60px 20px;
}

.processing-icon {
  margin-bottom: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  margin: 20px 0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.payment-form {
  text-align: left;
}

.payment-header {
  text-align: center;
  margin-bottom: 30px;
}

.amount-summary {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.total-amount {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-amount .label {
  font-size: 18px;
  color: #666;
}

.total-amount .value {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
}

.payment-methods {
  margin-bottom: 30px;
}

.payment-methods h3 {
  margin-bottom: 20px;
  color: #333;
}

.method-selector {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.method-option {
  border-bottom: 1px solid #e0e0e0;
}

.method-option:last-child {
  border-bottom: none;
}

.method-option input[type="radio"] {
  display: none;
}

.method-label {
  display: block;
  padding: 20px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.method-label:hover {
  background: #f8f9fa;
}

.method-option input[type="radio"]:checked + .method-label {
  background: #e7f3ff;
  border-left: 4px solid #007bff;
}

.method-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.method-info i {
  font-size: 24px;
  color: #007bff;
}

.method-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.method-desc {
  font-size: 14px;
  color: #666;
}

.secure-payment-notice {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 30px;
  padding: 15px;
  background: #f8fff9;
  border-radius: 8px;
}

.security-badges, .security-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #28a745;
  font-weight: 500;
}

.payment-actions {
  text-align: center;
}

.pay-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 15px 40px;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
  min-width: 200px;
}

.pay-btn:hover:not(:disabled) {
  background: #218838;
}

.pay-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
}

.payment-note {
  margin-top: 20px;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

/* Responsive */
@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }

  .download-btn, .home-btn {
    width: 100%;
  }

  .secure-payment-notice {
    flex-direction: column;
    gap: 15px;
  }

  .pay-btn {
    width: 100%;
  }
}
</style>
