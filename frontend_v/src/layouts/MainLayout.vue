<script setup lang="ts">
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import GlobalNews from "@/components/GlobalNews.vue";
</script>

<template>
    <Header />
    <GlobalNews />
    <router-view />
    <Footer />
</template>
