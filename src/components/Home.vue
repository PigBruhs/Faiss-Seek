<template>
    <div class="background">
        <HeaderTopAfterLogin :userId="userId" :role="role" @logout="logout" />
        <div v-if="message" class="message-box" :class="messageType">
            {{ message }}
        </div>
        <div class="home-container">
            <div class="upload-section">
                <input type="file" accept="image/*" @change="onFileChange" ref="fileInput" />
                <div v-if="imageUrl" class="preview">
                    <img :src="imageUrl" alt="预览" class="preview-img" />
                    <button @click="removeImage">删除图片</button>
                </div>
                <button :disabled="!imageFile" @click="matchImage">匹配</button>
            </div>
        </div>
    </div>
</template>

<script>
import HeaderTopAfterLogin from "./scomponents/HeaderTopAfterLogin.vue";
import axios from "axios";

export default {
    components: { HeaderTopAfterLogin },
    data() {
        return {
            message: "",
            imageFile: null,
            imageUrl: null,
            imageList: [], // 用于存储后端返回的图片列表
            userId: "",
        };
    },
    methods: {
        logout() {
            localStorage.removeItem("token"); // 清除 token
            localStorage.removeItem("userId"); // 清除用户 ID
            localStorage.removeItem("role"); // 清除用户组
            this.updateUserId(); // 更新用户信息
            this.$router.push({ path: "/Login" }); // 跳转到登录页面
        },
        setMessage(content, type) {
            this.$emit("set-message", content, type);
        },
        onFileChange(e) {
            const file = e.target.files[0];
            if (file) {
                this.imageFile = file;
                this.imageUrl = URL.createObjectURL(file);
            }
        },
        removeImage() {
            this.imageFile = null;
            this.imageUrl = null;
            this.$refs.fileInput.value = "";
        },
        async matchImage() {
            if (!this.imageFile) return;
            const formData = new FormData();
            formData.append("image", this.imageFile);

            try {
                // 获取 token
                const token = localStorage.getItem("token");
                // POST 请求发送图片，附带 token
                const res = await axios.post("http://localhost:19198/match", formData, {
                    headers: {
                        "Content-Type": "multipart/form-data",
                        "Authorization": `Bearer ${token}`, // 添加 token 到请求头
                    },
                });

                // 假设后端返回的数据格式为 { images: [...] }
                this.imageList = res.data.images || [];
                this.$emit("set-message", "图片获取成功", "success");
            } catch (err) {
                this.$emit("set-message", "图片获取失败", "error");
            }
        },
        async checkTokenValidity() {
            const token = localStorage.getItem("token");
            if (!token) {
                this.$router.push({ path: "/Login" });
                return;
            }
            try {
                const response = await axios.get("http://localhost:19198/protected", {
                    headers: { Authorization: token },
                });

                // 根据 response.data.success 判断
                if (!response.data.success) {
                    console.error("Token 验证失败:", response.data.message);
                    this.setMessage(response.data.message || "Token 验证失败", "error");
                    localStorage.removeItem("token");
                    localStorage.removeItem("userId"); // 清除用户 ID
                    localStorage.removeItem("role"); // 清除用户组
                    this.$router.push({ path: "/Login" });
                }
            } catch (error) {
                if (!error.response) {
                    console.error("网络错误:", error);
                    this.setMessage("网络连接失败，请检查您的网络", "error");
                } else {
                    console.error("Token 验证失败:", error.response.data.message);
                    this.setMessage(error.response.data.message || "Token 验证失败", "error");
                }
                localStorage.removeItem("token");
                localStorage.removeItem("userId"); // 清除用户 ID
                localStorage.removeItem("role"); // 清除用户组
                this.$router.push({ path: "/Login" });
            }
        }
    },
    mounted() {
        this.userId = localStorage.getItem("userId") || "未知"; // 从 localStorage 获取 userId
        // 检查用户是否登录
        if (!localStorage.getItem("token")) {
            this.$router.push({ path: "/Login" });
        }
        // 检查 token 有效性
        this.checkTokenValidity();
    },
};
</script>

<style scoped>
.background {
    min-height: 100vh;
    width: 100vw;
    /* 你的背景图片等样式可继续保留 */
}

.home-container {
    padding-top: 140px;
    /* 预留HeaderTop高度+间距 */
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: calc(100vh - 140px);
}

.upload-section {
    margin-top: 40px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.preview {
    margin: 20px 0;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.preview-img {
    max-width: 300px;
    max-height: 300px;
    display: block;
    margin-bottom: 10px;
}

.message-box.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.message-box.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.message-box.warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeeba;
}

button {
    margin-right: 10px;
}
</style>