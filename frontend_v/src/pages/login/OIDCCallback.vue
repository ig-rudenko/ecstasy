<script setup lang="ts">
import {onMounted, ref} from "vue";
import {useStore} from "vuex";

import router from "@/router";
import {completeOIDCLogin} from "@/oidc";

const store = useStore();
const errorMessage = ref("");

onMounted(async () => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  const state = params.get("state");
  const error = params.get("error");

  if (error) {
    errorMessage.value = params.get("error_description") || error;
    return;
  }

  if (!code || !state) {
    errorMessage.value = "OIDC-провайдер не вернул код авторизации.";
    return;
  }

  try {
    const redirectPath = await completeOIDCLogin(code, state);
    await store.dispatch("auth/oidcLogin");
    await router.replace(redirectPath);
  } catch (reason) {
    errorMessage.value = reason instanceof Error ? reason.message : String(reason);
  }
});
</script>

<template>
  <div class="flex h-screen items-center justify-center bg-gray-950 text-gray-200">
    <div class="flex w-full max-w-sm flex-col items-center gap-4 px-6 text-center">
      <ProgressSpinner v-if="!errorMessage"/>
      <Message v-else severity="error" icon="pi pi-exclamation-triangle">
        {{ errorMessage }}
      </Message>
      <Button v-if="errorMessage" label="Вернуться ко входу" icon="pi pi-sign-in" @click="router.replace('/account/login')"/>
    </div>
  </div>
</template>
