<template>
  <div class="customer-form" ref="customerForm">
    <form @submit.prevent="submitForm">
      <div class="form-section">
        <h3>Personal Information</h3>

        <div class="form-row">
          <div class="form-group">
            <label for="firstName">First Name *</label>
            <input
              id="firstName"
              type="text"
              v-model="form.firstName"
              :disabled="loading"
              required
              placeholder="Your first name"
            >
          </div>

          <div class="form-group">
            <label for="lastName">Last Name *</label>
            <input
              id="lastName"
              type="text"
              v-model="form.lastName"
              :disabled="loading"
              required
              placeholder="Your last name"
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
              placeholder="your.email@example.com"
            >
          </div>

          <div class="form-group">
            <label for="phone">Phone</label>
            <input
              id="phone"
              type="tel"
              v-model="form.phone"
              :disabled="loading"
              placeholder="+1 123 456 789"
            >
          </div>
        </div>
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
    },
    bookingType: {
      type: String,
      required: true,
      validator: value => ['day', 'night'].includes(value)
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
  mounted() {
    this.$nextTick(() => {
      this.updateBackgroundColors()
    })
  },
  watch: {
    bookingType() {
      this.$nextTick(() => {
        this.updateBackgroundColors()
      })
    }
  },
  methods: {
    updateBackgroundColors() {
      // Check if component is mounted and $el exists
      if (!this.$el || !this.$el.style) {
        return
      }

      if (this.bookingType === 'night') {
        this.$el.style.setProperty('--form-background', '#161616')
        this.$el.style.setProperty('--form-text-color', '#ffffff')
        this.$el.style.setProperty('--form-input-bg', '#2d2d2d')
        this.$el.style.setProperty('--form-border-color', 'rgba(255, 255, 255, 0.2)')
      } else if (this.bookingType === 'day') {
        this.$el.style.setProperty('--form-background', '#E9E9DF')
        this.$el.style.setProperty('--form-text-color', '#333')
        this.$el.style.setProperty('--form-input-bg', '#E0E0D8')
        this.$el.style.setProperty('--form-border-color', '#e0e0e0')
      }
    },
    submitForm() {
      if (this.isFormValid) {
        this.$emit('customer-info', { ...this.form })
      }
    },
    getFormData() {
      return this.isFormValid ? { ...this.form } : null
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
  background: var(--form-background, #E9E9DF);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.form-section h3 {
  margin: 0 0 20px 0;
  color: var(--form-text-color, #333);
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
  color: var(--form-text-color, #333);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--form-border-color, #e0e0e0);
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s ease;
  background: var(--form-input-bg, #E9E9DF);
  color: var(--form-text-color, #333);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #c9a961;
  box-shadow: 0 0 0 2px rgba(201, 169, 97, 0.25);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
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
}
</style>
