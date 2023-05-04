<template>

  <div v-if="rings.selectedRing === null"
       class="container px-4" id="featured-3">

    <h2 class="pb-2 border-bottom">Доступные вам транспортные кольца</h2>

    <div class="row g-4 py-5 row-cols-1 row-cols-lg-3">

      <div v-for="ring in rings.list" class="feature col">
        <div class="ring-card">
          <div class="d-inline-flex justify-content-center mb-3 text-bg-primary icon-background">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-bounding-box-circles" viewBox="0 0 16 16">
              <path d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
          </div>
          <h3 class="fs-2 ring-link" @click="chooseRing(ring)">{{ring.name}}</h3>
          <p>{{ring.description}}</p>
        </div>
      </div>
    </div>
  </div>


  <div v-else>
    <RingMenu :rings="rings" />
  </div>

</template>

<script>

import RingMenu from "./components/TransportRingRotate/RingMenu.vue";

export default {
  name: "App_transport_ring",
  components: { RingMenu },
  data() {
    return {
      rings: {
        list: [],
        selectedRing: null
      },
    }
  },

  async mounted() {
    await this.getRings();
  },

  methods: {
    async getRings() {
      try {
        let resp = await fetch(
            "/ring-manager/api/transport-rings",
            {method: "get", credentials: "include"}
        );
        this.rings.list = await resp.json();
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
.ring-card {
  border: 1px solid #cdcdcd;
  padding: 20px;
  border-radius: 20px;
}

.icon-background {
  padding: 10px;
  border-radius: 10px;
}

.ring-link {
  cursor: pointer;
}
</style>