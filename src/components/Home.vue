<template>
    <div class="background" style="font-family: 'MyFont';">
        <HeaderTopAfterLogin />
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
        };
    },
    methods: {
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
                // POST 请求发送图片，获取图片列表
                const res = await axios.post("http://localhost:19198/match", formData, {
                    headers: { "Content-Type": "multipart/form-data" },
                });
                // 假设后端返回的数据格式为 { images: [...] }
                this.imageList = res.data.images || [];
                this.$emit("set-message", "图片获取成功", "success");
            } catch (err) {
                this.$emit("set-message", "图片获取失败", "error");
            }
        },
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