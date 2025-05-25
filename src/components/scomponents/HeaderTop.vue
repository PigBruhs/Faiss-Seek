<template>
   <div class="top">
        <div class="title">
            <h1>答而多图图</h1>
        </div>
         <div class="logo">
            <img src="/src/assets/images/logo.png" alt="logo" height="120px" id="logo">
         </div>
    </div>
</template>

<script>
export default {
    name: "ComponentTemplate",
    data() {
        return {
            title: "Component Template",
        };
    },
    methods: {
        // Add your methods here
    },
    watch: {
        // Add your watchers here
    },
    computed: {
        // Add your computed properties here
    },
    mounted() {
        console.log("Component mounted");
    },
};
</script>

<style scoped>
.top{
    width: 100vw;
    height: 120px;
    overflow: hidden;
    position: fixed; 
    background-color: rgba(255, 255, 255, 0.5);
    flex-direction: row-reverse;
    
    backdrop-filter: blur(1px);
    /* background-image: url("/src/assets/images/backgroundimg.jpg"); */
    background-size: cover;
    box-shadow: 0px 5px 15px rgba(94, 93, 93, 0.5);
    
    z-index: 999;
    box-sizing: border-box; /* 确保 padding 和 border 不会增加额外尺寸 */
    border-bottom: 1px solid rgba(255, 255, 255, 0.115); /* 添加底部边框 */
}
.title{
    width: 100%;


    position:absolute;
    bottom: 0;

    font-family: 'MyFont';
    color: rgb(44, 44, 44);
    margin-left: 50px;
    margin-bottom: 10px;
}
.logo{
    position:absolute;
    bottom: 0;
    right: 0;
    margin-right: 150px;
}
</style>
