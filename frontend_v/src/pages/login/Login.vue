<script setup lang="ts">
import {ref} from "vue";

import {LoginUser} from "@/services/user";
import {useStore} from "vuex";
import getVerboseAxiosError from "@/errorFmt";
import router from "@/router.ts";

const store = useStore();

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
              router.push({name: 'home'});
            }
            processing.value = false;
          },
          () => {
            userError.value = 'Неверный логин или пароль'
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

</script>

<template>
  <video id="background-video" autoplay loop muted poster="/img/login-background-video-preview.png">
    <source src="/video/welcome.mp4" type="video/mp4">
  </video>

  <div class="flex justify-start items-center h-screen">
    <div class="flex flex-col gap-3 mx-6 w-full md:mx-20 md:w-[20rem]">
      <h1 class="mb-4 text-2xl md:w-[20rem] text-center">Пожалуйста, войдите в систему Ecstasy</h1>

      <Message v-if="userError" severity="error" icon="pi pi-exclamation-triangle" class="text-center my-4">{{userError}}</Message>

      <div>
        <IftaLabel>
          <InputText id="username" @keydown.enter="handleLogin" fluid :invalid="!user.valid.username" v-model="user.username"/>
          <label class="text-[0.85rem]" for="username">Логин</label>
        </IftaLabel>
        <Message v-if="!user.valid.username" severity="error" icon="pi pi-exclamation-triangle" class="text-center"><div class="text-xs">{{user.valid.usernameError}}</div></Message>

      </div>

      <div>
        <IftaLabel>
          <Password id="password" @keydown.enter="handleLogin" fluid :feedback="false" v-model="user.password"/>
          <label class="text-[0.85rem]" for="username">Пароль</label>
        </IftaLabel>
        <Message v-if="!user.valid.password" severity="error" icon="pi pi-exclamation-triangle" class="text-center"><div class="text-xs">{{user.valid.passwordError}}</div></Message>
      </div>

      <Button type="button" @click="handleLogin" :disabled="processing" :loading="processing" icon="pi pi-sign-in"
              label="Войти" fluid outlined class="w-full my-4 hover:bg-primary hover:text-primary-contrast"/>

      <p class="mt-5 text-muted-color text-center">Ecstasy &copy; 2022-{{new Date().getFullYear()}}</p>
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