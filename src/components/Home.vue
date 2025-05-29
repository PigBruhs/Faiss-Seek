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
            <div class="image-gallery" v-if="imageList.length > 0">
                <h3>匹配结果：</h3>
                <div class="image-grid">
                    <ImageDiv v-for="(image, index) in imageList" :key="index" :imageSrc="image.url" :imageTitle="image.name" />
                </div>
            </div>
        </div>

    </div>
</template>

<script>
import HeaderTopAfterLogin from "./scomponents/HeaderTopAfterLogin.vue";
import axios from "axios";
import ImageDiv from "./scomponents/ImageDiv.vue";

export default {
    components: { HeaderTopAfterLogin, ImageDiv },
    data() {
        return {
            message: "",
            imageFile: null,
            imageUrl: null,
            imageList: [], // 用于存储后端返回的图片列表
            userId: "",
            role: "",
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
            this.message = content;
            this.messageType = type; // 设置消息类型
            setTimeout(() => {
                this.message = "";
                this.messageType = "";
            }, 3000); // 3秒后清除消息提示
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

                // 检查后端返回的数据
                if (res.data.success && res.data.results.length > 0) {
                    this.imageList = res.data.results; // 将返回的图片列表存储到 imageList
                    this.setMessage("图片匹配成功", "success");
                } else if (res.data.success && res.data.results.length === 0) {
                    this.setMessage("未找到匹配的图片", "warning");
                } else {
                    this.setMessage(res.data.message || "图片匹配失败", "error");
                }

                console.log("匹配结果:", this.imageList); // 打印匹配结果
            } catch (err) {
                console.error("图片匹配失败:", err);
                this.setMessage("图片匹配失败，请稍后重试", "error");
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
                    headers: { Authorization: `Bearer ${token}` },
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
        this.role = localStorage.getItem("role") || "user"; // 从 localStorage 获取用户组
        this.userId = localStorage.getItem("userId") || "未知用户"; // 从 localStorage 获取 userId
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

.image-gallery {
    margin-top: 40px;
    width: 95%; /* 增加容器宽度 */
}

.image-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr); /* 每行展示 3 张图片 */
    gap: 150px; /* 缩小图片之间的间距 */
}

.image-item {
    display: flex;
    flex-direction: column; /* 让图片和文字垂直排列 */
    justify-content: center; /* 水平居中图片 */
    align-items: center; /* 垂直居中图片 */
    text-align: center;
    width: 100%; /* 占满父容器 */
    height: 500px; /* 固定容器高度 */
    overflow: hidden; /* 隐藏超出容器的部分 */
}

.image-item img {
    width: auto; /* 图片宽度自适应 */
    height: 100%; /* 图片高度占满容器 */
    object-fit: contain; /* 保持图片长宽比，显示完整内容 */
    border: 1px solid #ccc;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.image-item p {
    margin-top: 30px; /* 文字与图片之间的间距 */
    font-size: 14px;
    color: #333;
    text-align: center;
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