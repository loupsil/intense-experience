<template>
  <div class="customer-form">
    <form @submit.prevent="submitForm">
      <div class="form-section">
        <h3>Informations personnelles</h3>

        <div class="form-row">
          <div class="form-group">
            <label for="firstName">Prénom *</label>
            <input
              id="firstName"
              type="text"
              v-model="form.firstName"
              required
              placeholder="Votre prénom"
            >
          </div>

          <div class="form-group">
            <label for="lastName">Nom *</label>
            <input
              id="lastName"
              type="text"
              v-model="form.lastName"
              required
              placeholder="Votre nom"
            >
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="email">Email *</label>
            <input
              id="email"
              type="email"
              v-model="form.email"
              required
              placeholder="votre.email@exemple.com"
            >
          </div>

          <div class="form-group">
            <label for="phone">Téléphone</label>
            <input
              id="phone"
              type="tel"
              v-model="form.phone"
              placeholder="+32 123 456 789"
            >
          </div>
        </div>
      </div>


      <div class="form-section">
        <div class="consent-section">

          <div class="consent-item">
            <input
              id="terms"
              type="checkbox"
              v-model="form.acceptTerms"
              required
            >
            <label for="terms">
              J'accepte les <a href="#" @click.prevent="showTerms">conditions générales</a> et la <a href="#" @click.prevent="showPrivacy">politique de confidentialité</a> *
            </label>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button
          type="submit"
          class="submit-btn"
          :disabled="!isFormValid"
        >
          Continuer vers le paiement
        </button>
      </div>
    </form>

    <!-- Terms Modal (simplified) -->
    <div v-if="showTermsModal" class="modal-overlay" @click="closeModals">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Conditions générales</h3>
          <button class="close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="modal-body">
          <p>Conditions générales simplifiées pour la démonstration...</p>
          <p>• Annulation gratuite jusqu'à 48h avant l'arrivée</p>
          <p>• Paiement intégral requis à la confirmation</p>
          <p>• Arrivée et départ selon les horaires convenus</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CustomerForm',
  data() {
    return {
      form: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        specialRequests: '',
        newsletter: false,
        acceptTerms: false
      },
      showTermsModal: false,
      showPrivacyModal: false
    }
  },
  computed: {
    isFormValid() {
      return this.form.firstName.trim() &&
             this.form.lastName.trim() &&
             this.form.email.trim() &&
             this.form.acceptTerms
    }
  },
  methods: {
    submitForm() {
      if (this.isFormValid) {
        this.$emit('customer-info', { ...this.form })
      }
    },

    showTerms() {
      this.showTermsModal = true
    },

    showPrivacy() {
      // In a real implementation, this would show privacy policy
      alert('Politique de confidentialité - Fonctionnalité à implémenter')
    },

    closeModals() {
      this.showTermsModal = false
      this.showPrivacyModal = false
    }
  }
}
</script>

<style scoped>
.customer-form {
  max-width: 600px;
  margin: 0 auto;
}

.form-section {
  margin-bottom: 30px;
  padding: 25px;
  background: #f8f9fa;
  border-radius: 12px;
}

.form-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.consent-section {
  margin-top: 20px;
}

.consent-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 15px;
}

.consent-item input[type="checkbox"] {
  margin-top: 4px;
  width: 16px;
  height: 16px;
}

.consent-item label {
  flex: 1;
  line-height: 1.5;
  color: #666;
  cursor: pointer;
}

.consent-item label a {
  color: #007bff;
  text-decoration: none;
}

.consent-item label a:hover {
  text-decoration: underline;
}

.form-actions {
  text-align: center;
  margin-top: 30px;
}

.submit-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 15px 40px;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #218838;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  padding: 20px 25px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 25px;
  line-height: 1.6;
  color: #666;
}

/* Responsive */
@media (max-width: 768px) {
  .form-section {
    padding: 20px;
  }

  .form-row {
    flex-direction: column;
    gap: 15px;
  }

  .consent-item {
    align-items: flex-start;
  }

  .submit-btn {
    width: 100%;
    padding: 15px;
  }
}
</style>
