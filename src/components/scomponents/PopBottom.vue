<template>
  <div class="popover-container">
    <a-popover
      v-for="(item, index) in items"
      :key="index"
      :title="item.title"
      trigger="hover"
      position="bottom"
      content-class="fade-pop transparent-pop"
    >
      <div class="popover-trigger" @click="handleClick(item.title)">
        <span class="title">{{ item.title }}</span>
        <a-divider direction="vertical" />
        <img :src="item.icon" class="icon" />
      </div>

      <template #content>
        <p>{{ item.content }}</p>
      </template>
    </a-popover>
  </div>
</template>

<script setup>
const items = [
  {
    title: 'Vit-B-16',
    icon: '//iconfont.alicdn.com/p/illus_3d/file/ZsWruISgVCKK/ec58813a-76ab-4735-8075-a1e99da18859.png',
    content: 'Vit-B-16 是一个用于图像分类的深度学习模型，具有较高的准确率和效率。',
  },
  {
    title: 'resnet50',
    icon: 'https://iconfont.alicdn.com/p/illus_3d/file/ZsWruISgVCKK/891ec5dc-e187-4e0d-95db-10736ade1893.png',
    content: 'resNet50 是一个经典的卷积神经网络模型，广泛应用于图像识别任务。',
  },
  {
    title: 'vgg16',
    icon: 'https://iconfont.alicdn.com/p/illus_3d/file/ZsWruISgVCKK/cf27cffe-8935-4d26-a8a4-cac8dda98478.png',
    content: 'vgg16 是一个深度卷积神经网络，以其简单的结构和高效的性能著称。',
  },
];

// 向父组件传递点击的 title
const emit = defineEmits(['onTitleClick']);
const handleClick = (title) => {
  emit('onTitleClick', title);
};
</script>

<style scoped>
/* 样式保持不变 */
.popover-container {
  display: flex;
  width: 100vw;
  height: 200px;
}

.popover-container > * {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.popover-trigger {
  cursor: pointer;
  padding: 10px;
  transition: transform 0.2s ease;
}
.popover-trigger:hover {
  transform: scale(1.1);
}
.icon {
  width: 160px;
  height: 160px;
}

.fade-pop {
  animation: fadeIn 0.3s ease-out;
}

.transparent-pop {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  color: #333;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>