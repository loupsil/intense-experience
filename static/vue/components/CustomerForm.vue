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
              :disabled="loading"
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
              :disabled="loading"
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
              :disabled="loading"
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
              :disabled="loading"
              placeholder="+32 123 456 789"
            >
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button
          type="submit"
          class="submit-btn"
          :disabled="!isFormValid || loading"
        >
          {{ loading ? 'Création du profil...' : 'Continuer' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: 'CustomerForm',
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      form: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        specialRequests: '',
      }
    }
  },
  computed: {
    isFormValid() {
      return this.form.firstName.trim() &&
             this.form.lastName.trim() &&
             this.form.email.trim()
    }
  },
  methods: {
    submitForm() {
      if (this.isFormValid) {
        this.$emit('customer-info', { ...this.form })
      }
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


/* Responsive */
@media (max-width: 768px) {
  .form-section {
    padding: 20px;
  }

  .form-row {
    flex-direction: column;
    gap: 15px;
  }

  .submit-btn {
    width: 100%;
    padding: 15px;
  }
}
</style>
