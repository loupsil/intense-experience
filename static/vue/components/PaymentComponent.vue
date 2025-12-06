<template>
  <div class="payment-component">
    <div class="payment-redirect" v-if="isRedirecting">
      <div class="redirect-icon">
        <i class="fas fa-external-link-alt"></i>
      </div>
      <h2>Payment in progress...</h2>
      <p>Payment is being processed in the other tab.</p>
      <div class="redirect-info">
        <p>Once your payment is confirmed on the payment page, click the button below to return to the site.</p>
        <button class="payment-complete-btn" @click="onPaymentCompleted">
          I've completed the payment
        </button>
      </div>
    </div>

    <div class="payment-error" v-else-if="hasError">
      <div class="error-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h2>Payment error</h2>
      <p>{{ errorMessage }}</p>
      <div class="error-actions">
        <button class="retry-btn" @click="createPaymentRequest">
          <i class="fas fa-redo"></i>
          Retry
        </button>
        <button class="home-btn" @click="goHome">
          Back to home
        </button>
      </div>
    </div>

    <div class="payment-ready" v-else-if="paymentReady">
      <div class="ready-icon">
        <i class="fas fa-credit-card"></i>
      </div>
      <h2>Payment ready</h2>
      <p>Your payment request has been created. Click the button below to proceed with payment.</p>

      <div class="payment-details">
        <h3>Payment details</h3>
        <div class="detail-item">
          <span>Reservation reference:</span>
          <strong>{{ reservation?.Identifier }}</strong>
        </div>
        <div class="detail-item">
          <span>Amount to pay:</span>
          <strong>{{ amount }}€</strong>
        </div>
      </div>

      <div class="payment-actions">
        <button class="pay-now-btn" @click="openPayment">
          Pay now
        </button>
      </div>
    </div>


    <div class="payment-init" v-else>
      <div class="init-icon">
        <i class="fas fa-credit-card"></i>
      </div>
      <h2>Preparing payment</h2>
      <p>Creating your payment request...</p>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
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
      required: true
    },
    amount: {
      type: Number,
      required: true
    },
    bookingType: {
      type: String,
      default: 'day'
    }
  },
  data() {
    return {
      isRedirecting: false,
      hasError: false,
      errorMessage: '',
      paymentUrl: '',
      paymentWindow: null,
      paymentRequestId: '',
      paymentReady: false,
      progressPercent: 0,
      progressInterval: null,
      frontendConfig: {
        payment_base_url: 'https://app.mews-demo.com/navigator/payment-requests/detail',
        default_currency: 'EUR',
        payment_expiration_days: 7,
        client_name: 'Intense Experience 1.0.0'
      }
    }
  },
  async mounted() {
    await this.fetchFrontendConfig()
    this.createPaymentRequest()
  },
  methods: {
    async fetchFrontendConfig() {
      try {
        const response = await fetch('/intense_experience-api/frontend-config')
        const data = await response.json()
        if (data.status === 'success') {
          this.frontendConfig = {
            payment_base_url: data.payment_base_url,
            default_currency: data.default_currency,
            payment_expiration_days: data.payment_expiration_days,
            client_name: data.client_name
          }
        }
      } catch (error) {
        console.error('Error loading frontend config:', error)
        // Use default values if config fails to load
      }
    },

    async createPaymentRequest() {
      try {
        this.hasError = false
        this.errorMessage = ''
        this.progressPercent = 0

        // Start progress animation
        this.progressInterval = setInterval(() => {
          this.progressPercent += Math.random() * 10
          if (this.progressPercent >= 90) {
            this.progressPercent = 90
          }
        }, 150)

        // Calculate expiration date from config
        const expirationMs = this.frontendConfig.payment_expiration_days * 24 * 60 * 60 * 1000

        // Prepare payment request data
        // Note: ClientToken and AccessToken are handled server-side for security
        const paymentRequestData = {
          Client: this.frontendConfig.client_name,
          PaymentRequests: [
            {
              AccountId: this.reservation.CustomerId,
              Amount: {
                Currency: this.frontendConfig.default_currency,
                Value: this.amount
              },
              Type: "Payment",
              Reason: "PaymentCardMissing",
              ExpirationUtc: new Date(Date.now() + expirationMs).toISOString(),
              Description: `Payment for reservation ${this.reservation.Identifier}`,
              ReservationId: this.reservation.Id
            }
          ]
        }

        // Make API call to create payment request
        const response = await fetch('/api/payment-request', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(paymentRequestData)
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()

        if (!data.PaymentRequests || !data.PaymentRequests[0] || !data.PaymentRequests[0].Id) {
          throw new Error('Invalid payment request response')
        }

        const paymentRequestId = data.PaymentRequests[0].Id
        this.paymentRequestId = paymentRequestId

        // Construct payment URL using config
        this.paymentUrl = `${this.frontendConfig.payment_base_url}/${paymentRequestId}?ccy=${this.frontendConfig.default_currency}&language=en-US`

        // Complete progress
        clearInterval(this.progressInterval)
        this.progressPercent = 100

        // Set payment ready state
        this.paymentReady = true

      } catch (error) {
        console.error('Error creating payment request:', error)
        clearInterval(this.progressInterval)
        this.hasError = true
        this.errorMessage = 'An error occurred while creating the payment request. Please try again.'
      }
    },


    openPayment() {
      // Open payment URL in new tab
      this.paymentWindow = window.open(this.paymentUrl, '_blank')

      // Set redirecting state to show payment in progress
      this.paymentReady = false
      this.isRedirecting = true
    },

    onPaymentCompleted() {
      // Reset the booking process to start over
      this.goHome()
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
  padding: 40px 20px;
}

.payment-init, .payment-redirect, .payment-error, .payment-ready {
  padding: 40px 20px;
}

.init-icon, .redirect-icon, .ready-icon {
  font-size: 48px;
  color: #007bff;
  margin-bottom: 20px;
}

.error-icon {
  font-size: 48px;
  color: #dc3545;
  margin-bottom: 20px;
}

.payment-init h2, .payment-redirect h2, .payment-error h2, .payment-ready h2 {
  color: #333;
  margin-bottom: 15px;
}

.payment-init p, .payment-redirect p, .payment-error p, .payment-ready p {
  color: #666;
  margin-bottom: 20px;
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
  background: #c9a961;
  border-radius: 4px;
  transition: width 0.3s ease;
}


.redirect-info {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.redirect-info a {
  color: #007bff;
  text-decoration: underline;
}

.redirect-info a:hover {
  color: #0056b3;
}

.error-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.retry-btn, .home-btn {
  padding: 12px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.retry-btn {
  background: #c9a961;
  color: white;
}

.retry-btn:hover {
  background: #b89851;
}

.home-btn {
  background: #6c757d;
  color: white;
}

.home-btn:hover {
  background: #5a6268;
}

.payment-actions {
  margin-top: 30px;
}

.pay-now-btn, .payment-complete-btn {
  padding: 12px 30px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 16px;
}

.pay-now-btn {
  background: #c9a961;
  color: white;
}

.pay-now-btn:hover {
  background: #b89851;
}

.payment-complete-btn {
  background: #28a745;
  color: white;
  margin-top: 15px;
}

.payment-complete-btn:hover {
  background: #218838;
}

/* Responsive */
@media (max-width: 768px) {
  .error-actions {
    flex-direction: column;
  }

  .retry-btn, .home-btn {
    width: 100%;
  }

  .payment-complete-btn {
    width: 100%;
    margin-top: 15px;
  }
}
</style>
