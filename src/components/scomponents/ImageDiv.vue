<template>
  <a-image
    :src="imageSrc1"
    :title="imageTitle"
    :description="imageDescription"
    width="260"
    style="margin-right: 67px; vertical-align: top;"
    :preview-visible="visible1"
    @preview-visible-change="() => { visible1 = false }"
  >
    <template #extra>
      <div class="actions">
        <span class="action" @click="() => { visible1 = true }"><icon-eye /></span>
        <span class="action" @click="onDownLoad"><icon-download /></span>
        <a-tooltip :content="tooltipContent">
          <span class="action"><icon-info-circle /></span>
        </a-tooltip>
      </div>
    </template>
  </a-image>
  <a-image
    :src="imageSrc2"
    :title="imageTitle"
    :description="imageDescription"
    width="260"
    footer-position="outer"
    :preview-visible="visible2"
    @preview-visible-change="() => { visible2 = false }"
  >
    <template #extra>
      <div class="actions actions-outer">
        <span class="action" @click="() => { visible2 = true }"><icon-eye /></span>
        <span class="action" @click="onDownLoad"><icon-download /></span>
        <a-tooltip :content="tooltipContent">
          <span class="action"><icon-info-circle /></span>
        </a-tooltip>
      </div>
    </template>
  </a-image>
</template>
<script>
  import { ref } from 'vue';
  import { IconEye, IconDownload, IconInfoCircle } from '@arco-design/web-vue/es/icon';

  export default {
    components: {
      IconEye, IconDownload, IconInfoCircle
    },
    setup() {
      const visible1 = ref(false);
      const visible2 = ref(false);

      // 定义变量
      const imageSrc1 = ref('');
      const imageSrc2 = ref('https://p1-arco.byteimg.com/tos-cn-i-uwbnlip3yd/a8c8cdb109cb051163646151a4a5083b.png~tplv-uwbnlip3yd-webp.webp');
      const imageTitle = ref('A user’s avatar');
      const imageDescription = ref('Present by Arco Design');
      const tooltipContent = ref('A user’s avatar');

      return {
        visible1,
        visible2,
        imageSrc1,
        imageSrc2,
        imageTitle,
        imageDescription,
        tooltipContent,
        onDownLoad() {
          console.log('download');
        },
      }
    }
  }
</script>
<style scoped>
  .actions {
    display: flex;
    align-items: center;
  }
  .action {
    padding: 5px 4px;
    font-size: 14px;
    margin-left: 12px;
    border-radius: 2px;
    line-height: 1;
    cursor: pointer;
  }
  .action:first-child {
    margin-left: 0;
  }

  .action:hover {
    background: rgba(0,0,0,.5);
  }
  .actions-outer {
    .action {
      &:hover {
        color: #ffffff;
      }
    }
  }
</style>