<script setup lang="ts">
import {ref} from "vue";
import {useStore} from "vuex";

const store = useStore()
const logoutVisible = ref(false);

async function logout() {
  await store.dispatch("auth/logout");
  location.href = "/account/login";
}

</script>

<template>
  <Button v-tooltip.left="'Выйти'" icon="pi pi-sign-out" @click="logoutVisible=true"
          class="dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-100 dark:hover:bg-gray-600 bg-opacity-10"
          text/>

  <Dialog v-model:visible="logoutVisible" modal
          pt:root:class="border-0 bg-surface-200 dark:bg-surface-800 rounded-xl p-2"
          pt:mask:class="backdrop-blur-sm">
    <template #container="{ closeCallback }">
      <div class="p-4 text-xl font-semibold text-surface-800 dark:text-surface-200">Вы уверены, что хотите выйти?</div>
      <div class="flex justify-end gap-2 p-2">
        <Button type="button" label="Нет" severity="secondary" autofocus @click="closeCallback"></Button>
        <Button type="button" label="Выйти" severity="danger" @click="logout"></Button>
      </div>
    </template>
  </Dialog>

</template>
