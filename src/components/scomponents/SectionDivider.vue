<template>
  <div class="divider-container">
    <div class="divider">
      <div class="line"></div>
      <div class="line"></div>
    </div>
    <span class="divider-text">{{ text }}</span>
    <div class="divider">
      <div class="line"></div>
      <div class="line"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
  }
})
</script>

<style scoped>
.divider-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.divider {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.line {
  margin-top: 1px;
  height: 1px;
  background-color: rgba(0, 0, 0, 0.4); /* 半透明黑 */
}

.divider-text {
  padding: 0 12px;
  font-weight: bold;
  font-size: 14px;
  color: black;
  white-space: nowrap; /* 防止文字换行 */
}
</style>