<script setup lang="ts">
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
</script>

<template>
  <Header/>

  <div class="container mx-auto">

    <div class="flex justify-center">
      <div class="xl:max-w-[70%] sm:grid sm:grid-cols-2 gap-10">

        <div class="p-4 sm:p-10 sm:pr-2 hover:scale-[1.02] group">
          <router-link :to="{name: 'gpon-subscribers-data'}" class="relative">
            <img class="w-full rounded-xl group-hover:shadow-xl" src="/img/gpon/left.png" alt="">
            <div class="absolute text-2xl font-bold top-8 left-8">Абонентские данные</div>
          </router-link>
        </div>

        <div class="p-4 sm:p-10 sm:pl-2 hover:scale-[1.02] group">
          <router-link :to="{name: 'gpon-tech-data'}" class="relative">
            <img class="w-full rounded-xl group-hover:shadow-xl" src="/img/gpon/right.png" alt="">
            <div class="absolute text-2xl font-bold top-8 left-8">Технические данные</div>
          </router-link>
        </div>

      </div>
    </div>

  </div>

  <Footer/>

</template>
