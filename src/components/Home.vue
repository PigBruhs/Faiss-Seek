<template>
    <div class="background">
        <HeaderTopAfterLogin :userId="userId" :role="role" @logout="logout" />
        <div v-if="message" class="message-box" :class="messageType">
            {{ message }}
        </div>
        <div class="home-container">
            <SelectWeb :onSelectWeb="handleWebSelection" :setMessage="setMessage" />
            <AddWeb :setMessage="setMessage" />
            <div class="upload-section">
                <div class="shangbian">

                    <div class="dual-box-wrapper">
                        <div class="left-box">
                            <h3 class="font" style="margin-bottom: 10px;">选择模型</h3>
                        </div>
                        <!-- <section-divider text="选择搜索模型" /> -->
                        <PopBottom @onTitleClick="handleTitleClick" />  
                    </div>
                    

                    <!-- <section-divider text="上传图片进行搜索" /> -->
                    <div class="dual-box-wrapper">
                        <div class="left-box">
                            <h3 class="font" style="margin: auto;">选择图片数量</h3>
                            <ImgSlide v-model="selectPectureNum" :max="100" :height="300" />
                        </div>
                        <div class="right-box">
                            <input type="file" accept="image/*" @change="onFileChange" ref="fileInput" />
                            <div v-if="imageUrl" class="preview">
                                <img :src="imageUrl" alt="预览" class="preview-img" />
                                
                            </div>
                            
                        </div>
                        <div class="rightrightbox">
                            <a-button class="font" @click="removeImage" type="primary" size="large">删除图片</a-button>
                            <div v-if="!isMatching">
                                <a-button class="font" :disabled="!imageUrl" @click="startMatching" type="primary" size="large">开始搜索</a-button>
                            </div>
                            <div v-else>
                                <img :src="matchingImageUrl" alt="搜索中" class="matching-img" />
                            </div>
                        </div>
                    </div>
                    
                </div>
                <section-divider class="font" text="搜索结果" />
                <div class="image-gallery" v-if="imageList.length > 0">
                    <h2 class="font">搜索结果：</h2>
                    <div class="image-grid">
                        <ImageDiv v-for="(image, index) in imageList" :key="index" :imageSrc1="image.name"
                            :imageTitle="image.name" :imageDescription="'相似度: ' + image.score.toFixed(2)"
                            :tooltipContent="'图片名称: ' + image.name" />
                    </div>
                </div>
            </div>
            <!-- 添加一个空的 div 容器 -->
            <div class="bottom-space"></div>
        </div>
    </div>
</template>

<script>
import ImgSlide from "./scomponents/ImgSlide.vue";
import SectionDivider from "./scomponents/SectionDivider.vue";
import PopBottom from "./scomponents/PopBottom.vue";
import AddWeb from "./scomponents/AddWeb.vue";
import ImageDiv from "./scomponents/ImageDiv.vue";
import HeaderTopAfterLogin from "./scomponents/HeaderTopAfterLogin.vue";
import axios from "axios";
import SelectWeb from "./scomponents/SelectWeb.vue";

export default {
    components: { ImageDiv, HeaderTopAfterLogin, SelectWeb, AddWeb, PopBottom, SectionDivider, ImgSlide },
    data() {
        return {
            imageFile: null, // 存储上传的图片文件
            imageUrl: null, // 存储图片预览的 URL
            imageList: [], // 存储后端返回的搜索结果
            isMatching: false, // 是否正在搜索
            matchingImageUrl: "", // 搜索中显示的图片 URL
            message: "",
            messageType: "",
            userId: "", // 用户 ID
            selectWeb: "", // 选择的网页
            selectModel: "vgg16", // 选择的模型
            selectPectureNum: 10, // 选择的图片数量
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
        handleWebSelection(webName) {
            this.selectWeb = webName; // 接收子组件传递的网页名字
            this.setMessage(`已选择网页: ${webName}`, "success");
        },
        setMessage(content, type) {
            this.message = content;
            this.messageType = type; // 设置消息类型
            setTimeout(() => {
                this.message = "";
                this.messageType = "";
            }, 3000); // 3秒后清除消息提示
        },
        handleTitleClick(title) {
            console.log('接收到的 title:', title);
            this.selectModel = title; // 更新选择的模型
            this.setMessage(`已选择模型: ${title}`, "success");
        },
        onFileChange(e) {
            const file = e.target.files[0];
            if (file) {
                this.imageFile = file;
                this.imageUrl = URL.createObjectURL(file);
                this.isMatching = false; // 上传新图片时重置搜索状态
            }
        },
        removeImage() {
            this.imageFile = null;
            this.imageUrl = null;
            this.isMatching = false; // 删除图片时重置搜索状态
            this.$refs.fileInput.value = "";
        },
        async startMatching() {
            if (!this.imageFile) return;

            // 设置搜索状态为 true，显示占位图片
            this.isMatching = true;
            this.matchingImageUrl = "/src/assets/images/search.gif"; // 设置搜索中占位图片

            const formData = new FormData();
            formData.append("image", this.imageFile);
            formData.append("selectWeb", this.selectWeb); // 将选择的网页类型添加到 FormData 中
            formData.append("selectModel", this.selectModel); // 将选择的模型添加到 FormData 中
            formData.append("selectPectureNum", this.selectPectureNum); // 将选择的图片数量添加到 FormData 中
            try {
                const res = await axios.post("http://localhost:19198/match", formData, {
                    headers: {
                        "Content-Type": "multipart/form-data",
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });

                if (res.data.success) {
                    this.imageList = res.data.results;
                    this.setMessage("搜索成功", "success");
                    console.log("搜索结果:", this.imageList);
                    this.matchingImageUrl = "/src/assets/images/searchfinished.gif"; // 设置搜索完成的图片
                } else {
                    this.setMessage(res.data.message || "搜索失败", "error");
                    this.resetMatching();
                }
            } catch (err) {
                console.error("搜索失败:", err);
                this.setMessage("搜索失败，请稍后重试", "error");
                this.resetMatching();
            }
        },
        resetMatching() {
            // 恢复搜索按钮
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
    position: relative;
}

.upload-section {
    margin-top: 40px;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 80vw;
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
    margin-top: 20px;
    border: 2px dashed #007bff;
    border-radius: 10px;

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

.message-box {
    position: fixed;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    padding: 10px;
    border-radius: 5px;
    font-size: 14px;
    text-align: center;
    width: 80%;
    max-width: 600px;
    color: white;
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

.imgslide-wrapper {
    position: absolute;
    top: 750px;
    /* ✅ 这个数值你根据视觉位置微调 */
    left: 40px;
    width: 600px;
    /* 控制组件最大宽度 */
    z-index: 10;
}
.dual-box-wrapper {
    display: flex;

    justify-content: space-evenly; /* 让两边分开 */
    align-items: center; /* 垂直居中矮的盒子 */
    margin-top: 20px;
    margin-bottom: 20px;
}

.left-box {
    flex: 0 0 10%; /* 固定宽度可调 */
    display: flex;
    justify-content: center;
}

.right-box {
    flex: 0 0 90%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.shangbian {
    display: flex;
    justify-content: center;
    align-items: center;
    column-gap: 70px;
    position: relative;
    left: -80px;
}

.rightrightbox {
    display: flex;
    margin-left: 60px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 20px;

    max-width: 40px;
}
.font{
    font-family: 'MCFont';
}
</style>