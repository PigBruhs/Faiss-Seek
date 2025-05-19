<template>
   <div class="top">
        <div class="left-section">
            <h1 class="webTitle">答而多图图</h1>
            <div class="user-actions">
                <h2>欢迎，{{ role === 'admin' ? '管理员' : '用户' }} {{ userId }}</h2>
                <a-button type="primary" @click="logout">退出登录</a-button>
            </div>
            <div class="logo">
                <img src="/src/assets/images/logo.png" alt="logo" height="120px" id="logo">
            </div>
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
            localStorage.removeItem("token");
            localStorage.removeItem("userId");
            localStorage.removeItem("role");
            this.$router.push({ path: "/Login" });
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
    background-color: rgba(255, 255, 255, 0.5);
    flex-direction: row-reverse;
    
    backdrop-filter: blur(1px);
    background-size: cover;
    box-shadow: 0px 5px 15px rgba(94, 93, 93, 0.5);
    z-index: 999;
    box-sizing: border-box;
    border-bottom: 1px solid rgba(255, 255, 255, 0.115);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
}
.left-section {
    display: flex;
    align-items: center;
    width: 100%;
}
.webTitle {
    margin-right: 40px;
    font-family: 'MyFont';
    color: rgb(44, 44, 44);
}
.user-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}
.user-actions h2 {
    margin: 0;
    font-size: 20px;
    font-weight: normal;
}
.logo{
    position:absolute;
    bottom: 0;
    right: 0;
    margin-right: 150px;
}
</style>