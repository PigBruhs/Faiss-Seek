<template>
  <div id="registerContainer">
    <a-space direction="vertical" size="large" id="inputContainer">
      <!-- 用户名输入框 -->
      <a-input
        ref="IdInput"
        class="customInput"
        v-model="userId"
        placeholder="请输入用户名（ 不超过 10 个字 ）"
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
        placeholder="请输入密码（ 6-20 位数字 / 字母 ）"
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

      <!-- 确认密码输入框 -->
      <a-input
        ref="ConfirmPassword"
        class="customInput"
        v-model="confirmPassword"
        placeholder="请再次输入密码"
        allow-clear
        type="password"
        @input="validateConfirmPassword"
        @keydown="(e) => handleEnterKey(e, 'confirmpassword')"
      >
        <template #prefix>
          <icon-lock style="color:white;"/>
        </template>
      </a-input>
      <p v-if="confirmError" class="errorMessage">{{ confirmError }}</p>
    </a-space>

    <router-link to="/Login" class="link">返回登录</router-link>
    
    <!-- 注册按钮 -->
    <a-button
      type="primary"
      @click="submitRegister"
      id="registerButton"
    >
      注册
    </a-button>

    
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
      userId: "",
      password: "",
      confirmPassword: "",
      userIdError: "",
      passwordError: "",
      confirmError: "",
    };
  },
  methods: {
    validateUserId() {
      if (!this.userId) {
        this.userIdError = "用户名不能为空";
      } else if (this.userId.length > 10) {
        this.userIdError = "用户名不能超过10个字";
      } else {
        this.userIdError = "";
      }
    },
    validatePassword() {
      const regex = /^[a-zA-Z0-9]{6,20}$/;
      if (!this.password) {
        this.passwordError = "密码不能为空";
      } else if (!regex.test(this.password)) {
        this.passwordError = "密码需为6-20位数字或字母";
      } else {
        this.passwordError = "";
      }
    },
    validateConfirmPassword() {
      if (this.confirmPassword !== this.password) {
        this.confirmError = "两次输入的密码不一致";
      } else {
        this.confirmError = "";
      }
    },
    submitRegister() {
      this.validateUserId();
      this.validatePassword();
      this.validateConfirmPassword();

      if (this.userIdError || this.passwordError || this.confirmError) {
        this.$emit("set-message", "请检查输入的用户名和密码", "error");
        return;
      }

      const registerData = {
        userId: this.userId,
        password: this.password,
      };

      axios
        .post("http://localhost:19198/register", registerData)
        .then((response) => {
          if (response.data.success) {
           this.$emit("set-message", "注册成功！", "success");
                        this.$router.push("/Login");
          } else {
            this.$emit("set-message", response.data.message || "注册失败", "error");
          }
        })
        .catch((error) => {
          console.error("注册请求失败:", error);
          this.$emit("set-message", "注册请求失败，请稍后重试", "error");
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
            this.$refs.ConfirmPassword.focus();
            break;
          case 'confirmpassword':
            this.submitRegister();
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


#registerContainer {
  display: flex;
  flex-direction: column;
  /* align-items: center; */
  /* justify-content: center; */
  height: auto; /* 让容器根据内容自适应高度 */

}

.link {
  margin-top: 20px;
  margin-left: 60px;

  font-family:'MyFont';
  color: #1890ff;

  text-shadow: 0px 0px 10px rgba(0, 0, 0, 1);
  font-weight: bold;
}

.link:hover {
  text-decoration: underline;
  color: #40a9ff; /* 鼠标悬停时的颜色 */
}

#registerButton {
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

#registerButton:hover {
  box-shadow: 0 0 20px rgb(255, 81, 81);
}



</style>