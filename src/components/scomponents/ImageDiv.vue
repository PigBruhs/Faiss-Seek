<template>
  <a-image
  referrerpolicy="no-referrer"
    :src="imageSrc1"
    :title="truncatedTitle"
    :description="imageDescription"
    width="260"
    height="269"
    fit="cover"
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
</template>
<script>
import { ref, computed } from 'vue';
import { IconEye, IconDownload, IconInfoCircle } from '@arco-design/web-vue/es/icon';

export default {
  components: {
    IconEye, IconDownload, IconInfoCircle
  },
  props: {
    imageSrc1: {
      type: String,
      required: true
    },
    imageTitle: {
      type: String,
      required: true
    },
    imageDescription: {
      type: String,
      required: true
    },
    tooltipContent: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const visible1 = ref(false);

    // 处理图片标题，超过 8 个字时省略至 5 个字加 "..."
    const truncatedTitle = computed(() => {
      return props.imageTitle.length > 15
        ? props.imageTitle.slice(0, 12) + '...'
        : props.imageTitle;
    });

    const onDownLoad = () => {
      console.log('download');
    };

    return {
      visible1,
      truncatedTitle,
      ...props,
      onDownLoad
    };
  }
};
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
  ::v-deep .arco-image-img {
  object-fit: cover !important;
}
</style>