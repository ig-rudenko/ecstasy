<template>

  <Header/>

  <div v-if="rings.selectedRing === null" class="container mx-auto my-8">

    <div class="text-2xl pb-5 border-bottom">Доступные вам транспортные кольца</div>

    <div class="grid sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">

      <div v-for="ring in rings.list">
        <div class="border p-4 rounded-xl">
          <div class="inline justify-center mb-3 text-primary icon-background">
            <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
          </div>
          <h3 class="text-2xl ring-link w-fit" @click="chooseRing(ring)">{{ ring.name }}</h3>
          <p>{{ ring.description }}</p>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="container mx-auto my-8">
    <RingMenu :rings="rings"/>
  </div>

  <Footer/>

</template>

<script>
import RingMenu from "./TransportRingRotate/RingMenu.vue";
import api from "@/services/api";
import permissions from "@/services/permissions";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "TransportRing",
  components: {Footer, Header, RingMenu},
  data() {
    return {
      rings: {
        list: [],
        selectedRing: null
      },
    }
  },

  async mounted() {
    if (!permissions.has('auth.access_transport_rings')) {
      location.href = '/';
      return
    }
    await this.getRings();
  },

  methods: {
    async getRings() {
      try {
        const resp = await api.get("/api/v1/ring-manager/transport-rings")
        this.rings.list = resp.data;
      } catch (e) {
        console.log(e);
      }
    },
    chooseRing(ringName) {
      this.rings.selectedRing = ringName;
    }
  }
}
</script>

<style scoped>
.icon-background {
  padding: 10px;
  border-radius: 10px;
}

.ring-link {
  cursor: pointer;
}
</style>
