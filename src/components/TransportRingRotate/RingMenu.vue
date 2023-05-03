<template>
<svg @click="backToAllRings" style="cursor: pointer" xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M1.146 4.854a.5.5 0 0 1 0-.708l4-4a.5.5 0 1 1 .708.708L2.707 4H12.5A2.5 2.5 0 0 1 15 6.5v8a.5.5 0 0 1-1 0v-8A1.5 1.5 0 0 0 12.5 5H2.707l3.147 3.146a.5.5 0 1 1-.708.708l-4-4z"/>
</svg>

<div class="row row-cols-1 row-cols-md-2 mb-3 text-center" style="margin: 20px">

  <div class="col" style="margin-top: 20px">
      <div class="list-group">
          <div class="rounded-4 list-group-item gap-3 py-3" aria-current="true">
              <p>Разворот кольца {{rings.selectedRing.name}}</p>
              <p>VLAN's для разворота:</p>
              <p>{{rings.selectedRing.vlans.join(",")}}</p>
          </div>
      </div>
  </div>

  <div class="col">
      <RingView :points="points" />
  </div>

</div>
</template>

<script>
import RingView from "./RingView.vue";

export default {
  name: "RingMenu",
  components: {RingView},
  props: {
    rings: {
      required: true,
      type: {
        list: Array,
        selectedRing: {name: String, description: String, vlans: Array}
      }
    }
  },
  data() {
    return {
      points: []
    }
  },
  async mounted() {
    await this.getRing()
  },
  methods: {
    async getRing() {
      try {
        let resp = await fetch(
            "/ring-manager/api/transport-ring/" + this.rings.selectedRing.name,
            {method: "get", credentials: "include"}
        )
        this.points = await resp.json()
      } catch (e) {
        console.log(e)
      }
    },
    backToAllRings() {
      this.rings.selectedRing = null;
    },
  },
}
</script>

<style scoped>

</style>