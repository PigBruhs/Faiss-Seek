<template>
   <div class="top">
        <!-- 网站标题和退出登录 -->
        <div class="left-section">
            <h1 class="webTitle">Senario X</h1>
            <div class="user-actions">
                <h2>欢迎，{{ role === 'admin' ? '管理员' : '用户' }} {{ userId }}</h2>
                <a-button type="primary" border-radius="10px" @click="logout">退出登录</a-button>
            </div>
        </div>

        <!-- 阿米娅图片 -->
        <div class="amiya">
            <img src="/src/assets/images/logo.png" alt="阿米娅" height="150px" id="amiyaimg">
        </div>

        <!-- 网站 Logo -->
        <div class="webLogo">
            <!-- <img id="logo" src="/src/assets/images/logo.png" alt="logo" height="275px"> -->
        </div>
    </div>
</template>

<script>
import { Button } from "@arco-design/web-vue";

export default {
    name: "HeaderTopAfterLogin",
    components: {
        AButton: Button,
    },
    props: {
        userId: {
            type: String,
            default: "未登录用户",
        },
        role: {
            type: String,
            required: true,
        },
    },
    methods: {
        logout() {
      localStorage.removeItem("token"); // 清除 token
      localStorage.removeItem("userId"); // 清除用户 ID
      localStorage.removeItem("role"); // 清除用户组
      this.$router.push({ path: "/Login" }); // 跳转到登录页面
    },
},
};
</script>

<style scoped>
.top {
    width: 100vw;
    height: 120px;
    overflow: hidden;
    position: fixed; 
    background-color: rgba(65, 65, 65, 0.15);
    flex-direction: row-reverse;
    backdrop-filter: blur(5px) brightness(200%) contrast(110%);
    /* background-image: url("/src/assets/images/backgroundimg.jpg"); */
    background-size: cover;
    box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.5);
    z-index: 999;
    box-sizing: border-box; /* 确保 padding 和 border 不会增加额外尺寸 */
    border-bottom: 1px solid rgba(255, 255, 255, 0.115); /* 添加底部边框 */
}

.left-section {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    gap: 10px;
}

.webTitle {
    position: absolute;
    bottom: 0;
    margin-bottom: 17px;
    margin-left: 50px; 
    color: #ffffff;

    font-family:'MyFont';
    font-weight: bold; /* 设置字体加粗 */
    line-height: 2;
    display: inline-block;
}

.user-actions {
    margin-top: 18px;
    margin-left: 50px;
    font-family:'MyFont';
    color: #ffffffbc;
    display: flex;
    align-items: center;
    gap: 10px;
}

.webLogo {
    position: relative;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

.amiya {
    position: absolute; /* 改为绝对定位 */
    right: 20px; /* 距离右侧 20px */
    top: 50%; /* 距离顶部 50% */
    transform: translateY(-50%); /* 垂直居中 */
    opacity: 0;
    transition: opacity 1300ms;
}
.amiya:hover {
    opacity: 1;
}
</style>