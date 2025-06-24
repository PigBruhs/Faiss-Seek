<template>
    <div class="fixed-right-btn-container">
        <div class="custom-vertical-btn" @click="handleClick">
            <span class="vertical-text">选择搜索图源</span>
        </div>
    </div>

    <a-drawer :width="540" :visible="visible" @ok="handleOk" @cancel="handleCancel" unmountOnClose>
        <template #title>
            <span>选择搜索图源</span>
        </template>
        <div class="web-list">
            <div v-for="web in webList" :key="web.id" class="web-item">
                <label>
                    <input type="radio" :value="web.name" v-model="selectedWeb" />
                    图源:{{ web.name }}|图源类型:{{ web.type }}|图片数量:{{ web.index_count+1 }}|
                </label>
                <!-- 如果用户是 admin，则显示删除按钮 -->
                <a-button type="outline" @click="showConfirm(web)" v-if="role === 'admin'" size="mini" shape="round"
                    status="danger" class="delete-btn">
                    <template #icon>
                        <icon-delete />
                    </template>
                    <template #default>Delete</template>
                </a-button>
            </div>
        </div>
    </a-drawer>

    <!-- 弹出的删除确认对话框 -->
    <a-modal v-model:visible="confirmVisible" title="删除确认" @ok="confirmDelete" @cancel="cancelDelete"
        :ok-button-props="{ disabled: confirmInput.trim() !== '我确认' }" destroy-on-close>
        <p>⚠️ 此操作不可逆，请在下方输入 <strong>“我确认”</strong> 三个字以确认删除。</p>
        <!-- 直接用 v-model，更加稳定 -->
        <a-input v-model="confirmInput" placeholder="请输入：我确认" style="margin-top: 10px;" @keyup.enter="confirmDelete" />
    </a-modal>
</template>

<script>
import axios from "axios";
import { ref } from "vue";
import { IconPlus, IconDelete } from "@arco-design/web-vue/es/icon";

export default {
    components: {
        IconPlus,
        IconDelete,
    },
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
        const role = localStorage.getItem("role") || "user";

        // 用于删除确认弹框相关的 ref
        const confirmVisible = ref(false);       // 是否显示确认弹框
        const confirmInput = ref("");            // 用户输入内容
        const currentDeleteWeb = ref(null);       // 当前准备删除的Web对象

        const handleClick = () => {
            visible.value = true;
            fetchWebList();
        };

        const handleOk = () => {
            visible.value = false;
            if (selectedWeb.value) {
                props.onSelectWeb(selectedWeb.value);
            } else {
                props.setMessage("未改变选择", "warning");
            }
        };

        const handleCancel = () => {
            visible.value = false;
        };

        const fetchWebList = async () => {
            try {
                const response = await axios.post(
                    "http://localhost:19198/getWebList",
                    {},
                    {
                        headers: {
                            Authorization: `Bearer ${localStorage.getItem("token")}`,
                        },
                    }
                );
                if (response.data.success) {
                    webList.value = response.data.webList;
                    console.log("获取网页列表成功:", webList.value);
                } else {
                    console.error("获取网页列表失败:", response.data.message);
                }
            } catch (error) {
                console.error("获取网页列表失败:", error);
            }
        };

        /***
         * 点击 Delete 按钮时先弹出确认框
         * @param {number|string} webId 要删除的 id
         */
        const showConfirm = (web) => {
            currentDeleteWeb.value = web;
            confirmInput.value = "";
            confirmVisible.value = true;
        };

        /***
         * 当用户在对话框中点击“确定”时，若输入框内容正好是“我确认”才去真正调用删除接口
         */
        const confirmDelete = () => {
            if (confirmInput.value === "我确认") {
                if (!currentDeleteWeb.value) {
                    props.setMessage("删除失败，未找到要删除的图源", "error");
                    return;
                }
                deleteWeb(currentDeleteWeb.value);
                confirmVisible.value = false;
                currentDeleteWeb.value = null;
            } else {
                props.setMessage("请输入正确的“我确认”才能删除", "warning");
            }
        };

        // 点击取消或关闭弹框
        const cancelDelete = () => {
            confirmVisible.value = false;
            currentDeleteWeb.value = null;
        };

        const deleteWeb = async (currentDeleteWeb) => {
            if (!currentDeleteWeb) {
                console.error("删除失败：currentDeleteWeb 未定义");
                props.setMessage("删除失败，未找到要删除的图源", "error");
                return;
            }
            try {
                console.log("准备删除的Web对象:", currentDeleteWeb);
                const response = await axios.post(
                    "http://localhost:19198/deleteWeb",
                    {
                        name: currentDeleteWeb.name,
                        id: currentDeleteWeb.id,
                    },
                    {
                        headers: {
                            Authorization: `Bearer ${localStorage.getItem("token")}`,
                        },
                    }
                );
                if (response.data.success) {
                    props.setMessage("删除成功", "success");
                    fetchWebList();
                } else {
                    props.setMessage(response.data.message || "删除失败", "error");
                }
            } catch (error) {
                console.error("删除失败:", error);
                props.setMessage("删除失败，请稍后重试", "error");
            }
        };

        return {
            visible,
            handleClick,
            handleOk,
            handleCancel,
            webList,
            selectedWeb,
            role,
            showConfirm,
            confirmVisible,
            confirmInput,
            confirmDelete,
            cancelDelete,
        };
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
    width: 60px;
}

.custom-vertical-btn {
    background-color: #1890ff;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 30px;
    height: 120px;
    transition: background-color 0.2s;
}

.custom-vertical-btn:hover {
    background-color: #40a9ff;
}

.vertical-text {
    writing-mode: vertical-rl;
    text-orientation: upright;
    color: white;
    font-size: 14px;
    line-height: 1.4;
    user-select: none;
}

.web-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    border-bottom: 1px solid #ddd;
}

.delete-btn {
    margin-left: auto;
}
</style>
