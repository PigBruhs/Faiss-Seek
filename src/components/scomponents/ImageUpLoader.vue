<!-- src/components/scomponents/PhotoWallUpload.vue -->
<template>
  <a-upload
    list-type="picture-card"
    :file-list="uploadList"
    :before-upload="handleBeforeUpload"
    :on-remove="handleRemove"
    accept="image/*"
    multiple
  >
    <a-space direction="vertical" :style="{ width: '100%' }">
    <a-upload action="/" />
    <a-upload action="/" disabled style="margin-top: 40px;"/>
  </a-space>
  </a-upload>
</template>

<script setup>
import { ref, watch } from 'vue';

// 接收 v-model 传入的 imageFiles 数组
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
});
const emit = defineEmits(['update:modelValue']);

// 本地 file-list，用于 a-upload 渲染预览
const uploadList = ref([]);

// 当父组件通过 v-model 直接给 modelValue 传了初始值时，把它转换成 uploadList
watch(
  () => props.modelValue,
  (files) => {
    uploadList.value = files.map((file, idx) => ({
      uid: file.uid || `init-${idx}`,
      name: file.name,
      url: file.url || URL.createObjectURL(file)
    }));
  },
  { immediate: true }
);

// 拦截上传，手动把 File 推给父组件
function handleBeforeUpload(file) {
  // 通知父组件更新 modelValue（imageFiles）
  emit('update:modelValue', [...props.modelValue, file]);

  // 把这个 file 转成可预览的项，push 到本地 uploadList
  const reader = new FileReader();
  reader.onload = (e) => {
    uploadList.value.push({
      uid: file.uid || file.name + Date.now(),
      name: file.name,
      url: e.target.result
    });
  };
  reader.readAsDataURL(file);

  // 阻止 a-upload 自动上传
  return false;
}

// 删除图片时，从本地和父组件里都移除
function handleRemove(fileItem) {
  // 本地 preview list
  const idx = uploadList.value.findIndex((item) => item.uid === fileItem.uid);
  if (idx >= 0) uploadList.value.splice(idx, 1);

  // 父组件的文件数组
  const newFiles = props.modelValue.slice();
  newFiles.splice(idx, 1);
  emit('update:modelValue', newFiles);
}
</script>

<style scoped>
.upload-container {
  width: 100%;
  max-width: 600px;
  margin: 20px auto;
}

.upload-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
  color: #999;
  border: 1px dashed #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.upload-placeholder:hover {
  border-color: #1890ff;
  color: #1890ff;
}
</style>
