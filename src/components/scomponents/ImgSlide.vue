<template>
  <div class="slider-wrapper">
    <a-slider
      v-model="localValue"
      direction="vertical"
      :min="min"
      :max="max"
      :step="step"
      :marks="marks"
      :show-tooltip="true"
      :style="{ height: height + 'px' }"
      @change="emitChange"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

// Props 接收参数
const props = defineProps({
  modelValue: {
    type: Number,
    default: 10,
  },
  min: {
    type: Number,
    default: 1,
  },
  max: {
    type: Number,
    default: 100,
  },
  step: {
    type: Number,
    default: 1,
  },
  height: {
    type: Number,
    default: 200,
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 内部数据绑定（局部值）
const localValue = ref(props.modelValue)

// 双向同步：父 -> 子
watch(() => props.modelValue, (newVal) => {
  localValue.value = newVal
})

// 子 -> 父
const emitChange = (val) => {
  emit('update:modelValue', val)
  emit('change', val)
}

// 自定义标签
const marks = {
  [props.min]: '1',
  [props.max]: '100'
}
</script>

<style scoped>
.slider-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}
</style>