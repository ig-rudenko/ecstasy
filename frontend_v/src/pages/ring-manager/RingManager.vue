<script setup lang="ts">
import permissions from "@/services/permissions";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
</script>

<template>

  <Header/>

  <div class="flex flex-wrap items-center justify-center gap-8 my-8">

    <div v-if="permissions.has('auth.access_transport_rings')" class="flex flex-col items-center">
      <div class="text-2xl">
        Транспортные кольца
      </div>
      <router-link to="/ring-manager/transport-ring" class="text-center h-full p-4 rounded-xl shadow-xl"
                   style="background-image: url('/img/ring_manager/background/transport_ring.jpg');
                             background-size: cover; padding: 180px 200px;">
      </router-link>
      <span>
          Кольца агрегаций, используются для разворота VLAN
      </span>
    </div>

    <div v-if="permissions.has('auth.access_rings')" class="flex flex-col items-center">
      <div class="text-2xl">
        Абонентские кольца
      </div>
      <router-link to="/ring-manager/access-ring" class="text-center h-100 p-4 rounded-xl shadow"
                   style="background-image: url('/img/ring_manager/background/access_ring.jpg');
                             background-size: cover; padding: 180px 200px;">
      </router-link>
      <span>
          Оборудование доступа, которые имею топологию "кольцо".
      </span>
    </div>

  </div>

  <Footer/>
</template>
