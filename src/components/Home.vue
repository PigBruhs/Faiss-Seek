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
                <div v-if="!isMatching">
                    <button :disabled="!imageUrl" @click="startMatching">匹配</button>
                </div>
                <div v-else>
                    <img :src="matchingImageUrl" alt="匹配中" class="matching-img" />
                </div>
            </div>
            <div class="image-gallery" v-if="imageList.length > 0">
                <h3>匹配结果：</h3>
                <div class="image-grid">
                    <ImageDiv v-for="(image, index) in imageList" :key="index" :imageSrc1="image.url"
                        :imageTitle="image.name" :imageDescription="'匹配分数: ' + image.score.toFixed(2)"
                        :tooltipContent="'图片名称: ' + image.name" />
                </div>
            </div>
        </div>
        <!-- 添加一个空的 div 容器 -->
        <div class="bottom-space"></div>
    </div>
</template>

<script>
import ImageDiv from "./scomponents/ImageDiv.vue";
import HeaderTopAfterLogin from "./scomponents/HeaderTopAfterLogin.vue";
import axios from "axios";

export default {
    components: { ImageDiv, HeaderTopAfterLogin },
    data() {
        return {
            imageFile: null, // 存储上传的图片文件
            imageUrl: null, // 存储图片预览的 URL
            imageList: [], // 存储后端返回的匹配结果
            isMatching: false, // 是否正在匹配
            matchingImageUrl: "", // 匹配中显示的图片 URL
            message: "",
            messageType: "",
            userId:"", // 用户 ID
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
                this.isMatching = false; // 上传新图片时重置匹配状态
            }
        },
        removeImage() {
            this.imageFile = null;
            this.imageUrl = null;
            this.isMatching = false; // 删除图片时重置匹配状态
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
        async startMatching() {
            if (!this.imageFile) return;

            // 设置匹配状态为 true，显示占位图片
            this.isMatching = true;
            this.matchingImageUrl = "/src/assets/images/search.gif"; // 设置匹配中占位图片

            const formData = new FormData();
            formData.append("image", this.imageFile);

            try {
                const res = await axios.post("http://localhost:19198/match", formData, {
                    headers: {
                        "Content-Type": "multipart/form-data",
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });

                if (res.data.success) {
                    this.imageList = res.data.results;
                    this.matchingImageUrl = "/src/assets/images/searchfinished.gif"; // 设置匹配完成的图片
                } else {
                    this.setMessage(res.data.message || "匹配失败", "error");
                    this.resetMatching();
                }
            } catch (err) {
                console.error("匹配失败:", err);
                this.setMessage("匹配失败，请稍后重试", "error");
                this.resetMatching();
            }
        },
        resetMatching() {
            // 恢复匹配按钮
            this.isMatching = false;
            this.matchingImageUrl = "";
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
}

.home-container {
    padding-top: 140px;
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

.matching-img {
    max-width: 100%;
    height: auto;
    margin-top: 20px;
    border: 2px dashed #007bff;
    border-radius: 10px;
    padding: 10px;
    background-color: #f8f9fa;
}

.image-gallery {
    margin-top: 40px;
    width: 90%;
}

button {
    padding: 10px 20px;
    font-size: 14px;
    color: #ffffff;
    background-color: #007bff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

button:hover {
    background-color: #0056b3;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

input[type="file"] {
    display: block;
    margin-bottom: 20px;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 14px;
    cursor: pointer;
}

.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
    justify-items: center;
    align-items: start;
}

.bottom-space {
    height: 200px;
    /* 设置底部空白区域的高度 */
}
</style>