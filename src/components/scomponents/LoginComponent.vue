<template>
  <div id="loginContainer">
    <a-space direction="vertical" size="large" id="inputContainer">
      <!-- 用户名输入框 -->
      <a-input
        ref="IdInput"
        class="customInput"
        v-model="userId"
        placeholder="请输入用户名（不超过 10 个字）"
        allow-clear
        @input="validateUserId"
        @keydown="(e) => handleEnterKey(e, 'username')"
      >
        <template #prefix>
          <icon-user style="color:white;"/>
        </template>
      </a-input>
      <p v-if="userIdError" class="errorMessage">{{ userIdError }}</p>

      <!-- 密码输入框 -->
      <a-input
        ref="PasswordInput"
        class="customInput"
        v-model="password"
        placeholder="请输入密码（6-20 位数字/字母）"
        allow-clear
        type="password"
        @input="validatePassword"
        @keydown="(e) => handleEnterKey(e, 'password')"
      >
        <template #prefix>
          <icon-lock style="color:white;"/>
        </template>
      </a-input>

      <p v-if="passwordError" class="errorMessage">{{ passwordError }}</p>

    </a-space>

    <div class="loginAndRegister">
      <router-link to="/Register" class="link" >注册账号</router-link>
      <a-button
        type="primary"
        @click="submitLogin"
        id="loginButton"
      >
        登录
      </a-button>
    </div>
    
  </div>
</template>

<script>
import { IconUser, IconLock } from "@arco-design/web-vue/es/icon";
import axios from "axios";

export default {
  components: {
    IconUser,
    IconLock,
  },
  data() {
    return {
      userId: "", // 用户名
      password: "", // 密码
      userIdError: "", // 用户名错误提示
      passwordError: "", // 密码错误提示
    };
  },
  methods: {
    // 验证用户名
    validateUserId() {
      if (!this.userId) {
        this.userIdError = "用户名不能为空";
      } else if (this.userId.length > 10) {
        this.userIdError = "用户名不能超过10个字";
      } else {
        this.userIdError = "";
      }
    },
    // 验证密码
    validatePassword() {
      const passwordRegex = /^[a-zA-Z0-9]*$/; // 仅允许数字和英文字符
      if (!this.password) {
        this.passwordError = "密码不能为空";
      } else if (!passwordRegex.test(this.password)) {
        this.passwordError = "密码只能包含数字和英文字符";
      } else if (this.password.length > 20) {
        this.passwordError = "密码不能超过20个字";
      } else if (this.password.length < 6) {
        this.passwordError = "密码不能少于6个字";
      } else {
        this.passwordError = "";
      }
    },
    // 提交登录
    submitLogin() {
      this.validateUserId();
      this.validatePassword();
      if (this.userIdError || this.passwordError) {
        this.$emit("set-message", "请检查输入的用户名和密码", "error");
        return;
      }

      const loginData = {
        userId: this.userId,
        password: this.password,
      };

      axios
        .post("http://localhost:19198/login", loginData)
        .then((response) => {
          if (response.data && response.data.success) {
            this.$emit("set-message", "登录成功！", "success");
            response.data.userId = this.userId; // 获取用户名
            localStorage.setItem("userId", this.userId); // 将用户名存储
            localStorage.setItem("token", response.data.token); // 将用户标识存储
            localStorage.setItem("role", response.data.role); // 将用户组存储
            this.$router.push({ path: "/Home" }); // 登录成功后跳转到主页并传入用户名参数
          } else {
            this.$emit("set-message", response.data.message || "登录失败", "error");
          }
        })
        .catch((error) => {
          this.$router.push({ path: "/Home" }); // 登录成功后跳转到主页并传入用户名参数
          if (error.response) {
            this.$emit("set-message", error.response.data.message || "登录失败", "error");
          } else {
            this.$emit("set-message", "网络错误，请稍后重试", "error");
          }
        });
    },
    // 新增方法：处理回车事件
    handleEnterKey(event, field) {
      if (event.key === 'Enter') { 
        event.preventDefault();
        switch(field) {
          case 'username':
            this.$refs.PasswordInput.focus();
            break;
          case 'password':
            this.submitLogin();
            break;
        }
      }
    },
  },
  mounted() {
    // 自动聚焦用户名输入框
    this.$refs.IdInput.focus();
  }
};
</script>

<style scoped>
/* @import "../../assets/styles/common.css"; */
/* 公共的css文件 */

#loginContainer {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* 两个输入框的容器 */
#inputContainer {
  width: 100%;
  margin-bottom: 20px; /* 输入框和按钮之间的间距 */
}


.customInput {
  box-sizing: border-box;
  width: 60%;
  height: 50px;
  border: 0;
  margin-left: 60px;
  
  border-width: 2px 0;
  border-style: solid;
  background-color: rgba(118, 118, 118, 0.563);
  border-color:rgba(199, 199, 199, 0.455);
  border-radius: 30px; /* Example border radius */
  box-shadow: 0 4px 80px rgba(201, 200, 200, 0.5); 
  padding-left: 20px;
  color: rgb(0, 0, 0);
  text-transform: scaleX(2);

  transition: 0.3s;
}
.customInput:deep(.arco-input) { /* 字节的按钮要这样才能完全改样式，挺麻烦的 */
  font-family:'MyFont';
  color: #ffffff;       
  font-size: 14px;   
}
.customInput:deep(.arco-input::placeholder) {
  color: #ffffff;      
  font-weight: normal;
  font-size: 14px;    
  opacity: 0.5;      
  font-style: italic; 
}
/* 聚焦样式 */
.customInput:hover, .customInput:focus-within {
  border-color: #ffffffcb;
  background-color: rgba(176, 176, 176, 0.563);
  /* box-shadow: 0 0 20px rgba(255, 255, 255, 0.5); */
}
  
  /* 错误提示样式 */
.errorMessage {
  margin: -10px 0 -10px 80px;
  color: red;
  font-size: 12px;
  text-shadow: 0px 0px 10px rgba(0, 0, 0, 1);
}

/* 注册链接 */
.link {
  color: #0084ff;

  font-family:'MyFont';
  font-weight: bold;

  margin-left: 60px;
  display: block; /* 块级元素，方便点击 */
  text-shadow: 0px 0px 10px rgb(189, 188, 188);

}
.link:hover {
  text-decoration: underline;
  color: #69bbff; /* 鼠标悬停时的颜色 */
}

/* 登录按钮样式 */
#loginButton {
  box-sizing: border-box;
  width: 150px;
  height: 45px;

  margin-left: 60px;
  margin-top: 20px;

  font-family:'MyFont';
  font-size: 16px ;
  font-weight: bold;
  color: rgb(255, 255, 255);
  background-color: rgba(255, 27, 27, 0.403);


  border-width: 2px 0;
  border-style: solid;
  border-color:rgba(255, 113, 113, 0.455);
  border-radius: 20px; /* Example border radius */


  transition-duration: 0.5s;
}

#loginButton:hover {
  box-shadow: 0 0 20px rgb(255, 81, 81);
}

</style>