<script setup lang="ts">
import {onMounted, ref} from "vue";

import {LoginUser} from "@/services/user";
import {useStore} from "vuex";
import getVerboseAxiosError from "@/errorFmt";
import router from "@/router.ts";
import keycloakConnector from "@/keycloak.ts";

const store = useStore();

onMounted(() => {
  if (store.state.auth.status.loggedIn) router.push({name: 'home'});
})

const user = ref(new LoginUser());
const processing = ref(false);
const userError = ref('');

function handleLogin() {
  if (!user.value.isValid) return;

  processing.value = true;
  userError.value = '';
  store.dispatch('auth/login', user.value)
      .then(
          value => {
            if (value.status != 200) {
              userError.value = value.message;
            } else {
              console.log("login success")
              setTimeout(() => router.push({name: 'home'}))
            }
            processing.value = false;
          }
      )
      .catch(
          reason => {
            userError.value = getVerboseAxiosError(reason)
            processing.value = false;
          }
      )
}

function handleOIDCLogin() {
  keycloakConnector.keycloakLoginState.setAutoLogin();
  keycloakConnector.keycloak.login();
}

async function logout() {
  await store.dispatch("auth/logout");
  location.href = "/account/login";
}

</script>

<template>
  <video id="background-video" autoplay loop muted poster="/img/login-background-video-preview.png">
    <source src="/video/welcome.mp4" type="video/mp4">
  </video>

  <div class="flex justify-start items-center h-screen">
    <div class="flex flex-col gap-3 mx-6 w-full md:mx-20 md:w-[20rem]">
      <h1 class="mb-4 text-2xl md:w-[20rem] text-center text-gray-200">Пожалуйста, войдите в систему Ecstasy</h1>

      <Message v-if="userError" severity="error" icon="pi pi-exclamation-triangle" class="text-center my-4">
        {{ userError }}
      </Message>

      <div>
        <IftaLabel>
          <InputText id="username" class="bg-gray-950 text-gray-200 font-mono" @keydown.enter="handleLogin" fluid
                     :invalid="!user.valid.username" v-model="user.username"/>
          <label class="text-[0.85rem]" for="username">Логин</label>
        </IftaLabel>
        <Message v-if="!user.valid.username" severity="error" icon="pi pi-exclamation-triangle" class="text-center">
          <div class="text-xs">{{ user.valid.usernameError }}</div>
        </Message>

      </div>

      <div>
        <IftaLabel>
          <Password id="password" input-class="bg-gray-950 text-gray-200 font-mono" @keydown.enter="handleLogin" fluid
                    :feedback="false" v-model="user.password"/>
          <label class="text-[0.85rem]" for="username">Пароль</label>
        </IftaLabel>
        <Message v-if="!user.valid.password" severity="error" icon="pi pi-exclamation-triangle" class="text-center">
          <div class="text-xs">{{ user.valid.passwordError }}</div>
        </Message>
      </div>

      <Button type="button" @click="handleLogin" :disabled="processing" :loading="processing" icon="pi pi-sign-in"
              label="Войти" fluid outlined class="w-full mt-4 hover:bg-primary hover:text-primary-contrast"/>
      <Button v-if="keycloakConnector.enabled" type="button" @click="handleOIDCLogin" :disabled="processing" :loading="processing" icon="pi pi-sign-in"
              label="Войти через OIDC" fluid text class="w-full hover:bg-primary hover:text-primary-contrast"/>
      <div>
        <i v-tooltip="'Перезапросить'" @click="logout" class="pi pi-wrench text-gray-400 hover:text-gray-100 cursor-pointer"/>
      </div>

      <p class="mt-5 text-muted-color text-center">Ecstasy &copy; 2022-{{ new Date().getFullYear() }}</p>
    </div>

  </div>

</template>

<style scoped>
#background-video {
  height: 100vh;
  width: 100vw;
  object-fit: cover;
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: -1;
  user-select: none;
}
</style>
