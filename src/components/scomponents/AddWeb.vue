<template>
    <a-button type="primary" @click="handleClick">上传图源信息</a-button>
    <a-drawer :width="500" :visible="visible" @ok="handleOk" @cancel="handleCancel" :placement="position"
        unmountOnClose>
        <template #title>
            <span v-if="role === 'user'">填写可选图源</span>
            <span v-else>审核图源请求</span>
        </template>
        <div v-if="role === 'user'" class="user-form">
            <div class="form-item">
                <label>网站名字：</label>
                <a-input v-model="webName" placeholder="请输入网站名字" />
            </div>
            <div class="form-item">
                <label>网址：</label>
                <a-input v-model="webUrl" placeholder="请输入网址" />
            </div>
            <div class="form-item">
                <label>其他信息：</label>
                <a-textarea v-model="webInfo" :max-length="400" placeholder="请输入不超过400字的信息" />
            </div>
        </div>
        <div v-else class="admin-list">
            <div v-for="web in webRequestList" :key="web.id" class="web-item">
                <div>
                    <p><strong>名字：</strong>{{ web.name }}</p>
                    <p><strong>网址：</strong>{{ web.url }}</p>
                    <p><strong>信息：</strong>{{ web.info }}</p>
                </div>
                <div class="admin-actions">
                    <a-button type="primary" @click="approveWeb(web)">审核通过</a-button>
                    <a-button type="danger" @click="rejectWeb(web)">拒绝</a-button>
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import axios from "axios";

export default {
    props: {
        addWebRequest: {
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
        const position = ref('left');
        const role = localStorage.getItem("role") || "user"; // 获取用户角色
        const webName = ref("");
        const webUrl = ref("");
        const webInfo = ref("");
        const webRequestList = ref([]); // 存储后端返回的 webRequestList

        const handleClick = () => {
            visible.value = true;
            if (role === "admin") {
                fetchWebRequestList(); // 如果是 admin，获取 webRequestList
            }
        };

        const handleOk = () => {
            visible.value = false;
            if (role == "user" && webName.value && webUrl.value) {
                props.addWebRequest(webName.value, webUrl.value, webInfo.value); // 调用父组件传递的回调函数
            } else if (role === "admin") {
                fetchWebRequestList(); // 如果是 admin，重新获取请求列表
            }
        };

        const handleCancel = () => {
            visible.value = false;
        };

        const submitWebInfo = async () => {
            try {
                const response = await axios.post("http://localhost:19198/addWeb", {
                    name: webName.value,
                    url: webUrl.value,
                    info: webInfo.value,
                }, {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });
                if (response.data.success) {
                    props.setMessage("提交成功，请等待管理员审核!", "success");
                    visible.value = false;
                } else {
                    props.setMessage("提交失败：" + response.data.message, "error");
                }
            } catch (error) {
                props.setMessage("提交失败，网络异常！", "error");
                console.error("提交失败:", error);
            }
        };

        const fetchWebRequestList = async () => {
            try {
                const response = await axios.get("http://localhost:19198/webRequestList", {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });
                if (response.data.success) {
                    webRequestList.value = response.data.webRequestList;
                } else {
                    console.error("获取请求列表失败:", response.data.message);
                    props.setMessage("获取请求列表失败：" + response.data.message, "error");
                }
            } catch (error) {
                console.error("获取请求列表失败:", error);
                props.setMessage("获取请求列表失败，网络异常！", "error");
            }
        };

        const approveWeb = async (web) => {
            const siteType = prompt("请输入网站类型：");
            if (!siteType || siteType.trim() === "") {
                props.setMessage("网站类型不能为空！", "error");
                return;
            }
            try {
                const response = await axios.post("http://localhost:19198/approveWeb", {
                    name: web.name,
                    url: web.url,
                    type: siteType,
                    },{
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });
                if (response.data.success) {
                    props.setMessage("审核通过成功！", "success");
                    fetchWebRequestList(); // 重新获取列表
                } else {
                    props.setMessage("审核失败,网站已存在或其他错误：" + response.data.message, "error");
                }
            } catch (error) {
                console.error("审核失败:", error);
                props.setMessage("审核失败，网络异常！", "error");
            }
        };

        const rejectWeb = async (web) => {
            try {
                const response = await axios.post("http://localhost:19198/rejectWeb", {
                    name: web.name,
                    url: web.url,},{
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });
                if (response.data.success) {
                    props.setMessage("拒绝成功！", "success");
                    fetchWebRequestList(); // 重新获取列表
                } else {
                    props.setMessage("拒绝失败：" + response.data.message, "error");
                }
            } catch (error) {
                console.error("拒绝失败:", error);
                props.setMessage("拒绝失败，网络异常！", "error");
            }
        };

        return {
            position,
            visible,
            role,
            webName,
            webUrl,
            webInfo,
            webRequestList,
            handleClick,
            handleOk,
            handleCancel,
            submitWebInfo,
            approveWeb,
            rejectWeb,
        };
    },
};
</script>

<style scoped>
.user-form {
    padding: 20px;
}

.admin-list {
    padding: 20px;
}

.web-item {
    border: 1px solid #ddd;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 5px;
}

.admin-actions {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}
</style>