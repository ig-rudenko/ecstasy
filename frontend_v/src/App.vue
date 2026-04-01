<template>
  <Snow v-if="[0, 1, 11].indexOf((new Date()).getMonth()) !== -1 && decorConfig.winterDecor"/>
  <Toast>
    <template #message="slotProps">
      <div class="flex flex-col items-start" style="flex: 1">
        <div class="font-medium my-3" v-html="slotProps.message.summary"></div>
        <div class="font-medium my-3" v-html="slotProps.message.detail"></div>
      </div>
    </template>
  </Toast>
  <router-view/>
  <ScrollTop
      :threshold="100"
      :pt="{
        root: {
          class: 'group border-none! bg-transparent! shadow-none! right-5! bottom-5! md:right-8! md:bottom-8!'
        }
      }">
    <div
        class="flex h-13 w-13 items-center justify-center rounded-[1.35rem] border border-gray-200/80 bg-white/85 text-slate-700 shadow-[0_16px_40px_-24px_rgba(15,23,42,0.45)] backdrop-blur-md transition duration-200 group-hover:-translate-y-0.5 group-hover:border-indigo-200 group-hover:bg-white group-hover:text-indigo-600 dark:border-gray-700/70 dark:bg-gray-900/70 dark:text-gray-200 dark:ring-1 dark:ring-white/5 dark:group-hover:border-indigo-500/50 dark:group-hover:bg-gray-900/85 dark:group-hover:text-indigo-300">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
        <path fill-rule="evenodd" d="M8 12a.5.5 0 0 1-.354-.146l-4-4a.5.5 0 1 1 .708-.708L8 10.793l3.646-3.647a.5.5 0 0 1 .708.708l-4 4A.5.5 0 0 1 8 12"/>
        <path fill-rule="evenodd" d="M8 4a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0v-6A.5.5 0 0 1 8 4"/>
      </svg>
    </div>
  </ScrollTop>
</template>

<script setup lang="ts">
import Toast from "primevue/toast";
import Snow from "@/components/Snow.vue";
import decorConfig from "@/services/decor.ts";
</script>
