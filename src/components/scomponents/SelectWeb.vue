<template>
    <a-button type="primary" @click="handleClick">选择匹配网页</a-button>
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