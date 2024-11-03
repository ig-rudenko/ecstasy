<template>
  <Toast/>
  <router-view/>
  <ScrollTop :threshold="100"/>
</template>

<script setup>
import Toast from "primevue/toast";
</script>