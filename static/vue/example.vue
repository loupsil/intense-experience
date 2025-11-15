<template>
  <div class="container">
    <h1>Example Component</h1>
    <p>{{ message }}</p>
  </div>
</template>

<script>
export default {
  name: 'ExampleComponent',
  data() {
    return {
      message: 'Hello World'
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20px;
}

h1 {
  color: #333;
}

p {
  color: #666;
}
</style>