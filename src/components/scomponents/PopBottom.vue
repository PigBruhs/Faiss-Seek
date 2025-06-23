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
      <div class="popover-trigger" @click="handleClick(index,item.title)":class="{ active: activeIndex === index }">
        <img :src="item.icon" class="icon" />
        <span class="title">{{ item.title }}</span>
      </div>

      <template #content>
        <p class="font">{{ item.content }}</p>
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
const activeIndex = ref(null);
// 向父组件传递点击的 title
const emit = defineEmits(['onTitleClick']);
const handleClick = (index,title) => {
  activeIndex.value = index;
  emit('onTitleClick', title);
};
</script>

<style scoped>
/* 样式保持不变 */
.popover-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  row-gap: -50px;
}

.popover-container > * {
  flex: 1;
  display: flex;
  justify-content: left;
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
.popover-trigger.active {
  border: 4px dashed transparent; /* 激活状态的虚线边框 */
  border-image: linear-gradient(45deg, #ff0000, #00ff00, #0000ff, #ff00ff);
  border-image-slice: 1;
  animation: rotate-border 2s linear infinite; /* 添加旋转动画 */
}
.icon {
  width: 120px;
  height: 120px;
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

.title {
  font-weight: bold;
  font-family: 'MCFont';
}
.font{
  font-family: 'MCFont';
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
@keyframes rotate-border {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>