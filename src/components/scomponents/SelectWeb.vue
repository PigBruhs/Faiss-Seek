<template>
    <div class="fixed-right-btn-container">
    <div class="custom-vertical-btn" @click="handleClick">
        <span class="vertical-text">选择匹配网页</span>
        </div>
     </div>
    <a-drawer :width="340" :visible="visible" @ok="handleOk" @cancel="handleCancel" unmountOnClose>
        <template #title>
            <span>选择匹配网页</span>
        </template>
        <div class="web-list">
            <div v-for="web in webList" :key="web.id" class="web-item">
                <label>
                    <input type="radio" :value="web.name" v-model="selectedWeb" />
                    {{ web.name }}网站类型{{ web.type }}
                </label>
            </div>
        </div>
    </a-drawer>
</template>
<script>
import axios from "axios";
export default {
    props: {
        onSelectWeb: {
            type: Function,
            required: true, // 父组件传递回调函数
        },
        setMessage: {
            type: Function,
            required: true, // 父组件传递回调函数
        },
    },
    setup(props) {
        const visible = ref(false);
        const webList = ref([]);
        const selectedWeb = ref("");
        const handleClick = () => {
            visible.value = true;
            fetchWebList(); // 打开抽屉时获取网页列表
        };
        const handleOk = () => {
            visible.value = false;
            if (selectedWeb.value){
                props.onSelectWeb(selectedWeb.value); // 调用父组件传递的回调函数
            }
            else{
                props.setMessage("未改变选择","warning"); // 设置消息
            }
        };
        const handleCancel = () => {
            visible.value = false;
        }
        const fetchWebList = async () => {
            try {
                const response = await axios.post("http://localhost:19198/getWebList",
                 {},//请求体为空对象
                 {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });
                if (response.success) {
                    webList.value = response.data.webList; // 假设返回的数据是一个数组
                }
                else {
                    console.error("获取网页列表失败:", response.message);
                }
            } catch (error) {
                console.error("获取网页列表失败:", error);
            }
        };
        return {
            visible,
            handleClick,
            handleOk,
            handleCancel,
            webList,
            selectedWeb,
        }
    },
};
</script>
<style scoped>
.fixed-right-btn-container {
  position: fixed;
  top: 50%;
  right: -30px;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1000;
  /* 给容器一个固定宽度，保证按钮能完整展示 */
  width: 60px;
}
/* 自定义一个“看起来像按钮”的 div */
.custom-vertical-btn {
  background-color: #1890ff;    /* Antd primary 颜色 */
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  /* 下面宽高根据文字多少调整，确保文字不会溢出 */
  width: 30px;
  height: 120px;
  transition: background-color 0.2s;
}
.custom-vertical-btn:hover {
  background-color: #40a9ff;
}
/* 竖排文字 */
.vertical-text {
  writing-mode: vertical-rl;
  text-orientation: upright;
  color: white;
  font-size: 14px;
  line-height: 1.4;
  user-select: none;
}
</style>