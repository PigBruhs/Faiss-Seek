<template>
    <div class="background">
        <HeaderTop></HeaderTop>
        <div v-if="message" class="message-box" :class="messageType">
                    {{ message }}
                </div>
        <div class="panel">
            <div id="logincomponents" class="glass">
                <LoginComponent @set-message="setMessage"></LoginComponent>
            </div>
        </div>
    </div>
</template>

<script>
import HeaderTop from "./scomponents/HeaderTop.vue";
import LoginComponent from "./scomponents/LoginComponent.vue";

export default {
    data() {
        return {
            // Your data properties go here
            message: "",
      messageType: "", // 用于存储消息类型
        };
    },
    methods: {
        setMessage(content, type) {
            this.message = content;
            this.messageType = type; // 设置消息类型
            setTimeout(() => {
                this.message = "";
                this.messageType = "";
            }, 3000); // 3秒后清除消息提示
        },
        // Your methods go here
    },
    computed: {
        // Your computed properties go here
    },
    mounted() {
        // Lifecycle hook
    },
    components: {
        HeaderTop,
        LoginComponent,
    },
};
</script>

<style scoped>
/* 父容器设置相对定位 */
#container {
    background-image: linear-gradient(90deg,rgba(0,0,0,0.7),rgba(0,0,0,0.1)),url('/src/assets/images/终末地视频帧.png');
    background-size: cover; /* 确保背景图覆盖整个容器 */
    background-position: center; /* 居中显示背景图 */
    overflow: hidden; /* 隐藏溢出部分 */
}



.panel{
    
    top: 140px;
    box-sizing: border-box;
    width: 100vw;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    
}

/* 子元素居中 */
#logincomponents {
    
    width: 70vw;
    min-width: 500px;
    height: auto;
    padding: 60px 0 50px 0;
    transform: scale(0.9);
    position: absolute;
    top: 30vh;

    transition-duration: 0.5s;
    transition-timing-function: cubic-bezier(0,.68,.12,1);

    display: flex;
    flex-direction: column;
    justify-content: center;
    
}
 
.panel:hover #logincomponents{
    transform: scale(1);


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
/* .panel:hover .loginPanelShadow{
    transform: scale(1);
    opacity: 1 ;
} */


/* .loginPanelShadow{
    box-sizing: border-box;
    width: 50vw;
    height: 400px;
    position: relative;

    margin-left: 25vw;
    margin-top: 15px;
    z-index: 0;

    background-image: linear-gradient(to top, transparent 65%, rgba(255, 255, 255, 0.15));
    border-radius: 30px;
    filter: blur(5px);

    transform: scale(0.9);
    opacity: 0;

    transition-duration: 0.5s;


} */

</style>