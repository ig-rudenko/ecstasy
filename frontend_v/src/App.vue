<template>
  <Toast>
    <template #message="slotProps">
      <div class="flex flex-col items-start" style="flex: 1">
        <div class="font-medium my-3" v-html="slotProps.message.summary"></div>
        <div class="font-medium my-3" v-html="slotProps.message.detail"></div>
      </div>
    </template>
  </Toast>
  <router-view/>
  <ScrollTop :threshold="100"/>
</template>

<script setup>
import Toast from "primevue/toast";
</script>