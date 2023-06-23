<template>

  <div v-if="rings.selectedRing === null"
       class="container px-4" id="featured-3">

    <h2 class="pb-2">Доступные вам абонентские кольца ({{filteredRings.length}})</h2>

    <div class="py-2">
      <input class="form-control" placeholder="Поиск" v-model.trim="search">
    </div>

    <div class="form-check py-2">
      <input class="form-check-input" type="checkbox" v-model="onlyNonNormal" id="flexCheckChecked">
      <label class="form-check-label" for="flexCheckChecked">
        Отображать только неверно развернутые
      </label>
    </div>

    <div v-if="rings.list.length" class="row py-2 row-cols-1 row-cols-lg-3">

      <div v-for="ring in filteredRings" class="feature col py-2">
        <div class="h-100 ring-card">
          <div class="d-inline-flex justify-content-center mb-3 text-bg-primary icon-background">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-bounding-box-circles" viewBox="0 0 16 16">
              <path d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
          </div>
          <h4 class="ring-link" @click="chooseRing(ring)">{{ring.head_name}}<br>{{ring.ports}}</h4>
          <p>
            {{ring.description}}
            <span v-if="!ring.is_normal_rotate_status" class="badge bg-warning">
              Кольцо неверно развернуто
            </span>
          </p>
        </div>
      </div>
    </div>

<!--    Загрузка-->
    <div v-else style="text-align: center;">
      <div class="spinner-border" role="status" style="height: 200px; width: 200px;">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

  </div>


  <div v-else>
    <AccessRingMenu :rings="rings" />
  </div>
</template>

<script>

import AccessRingMenu from "./components/AccessRings/AccessRingMenu.vue";

export default {
  name: "App_transport_ring",
  components: { AccessRingMenu },
  data() {
    return {
      rings: {
        list: [],
        selectedRing: null,
      },
      search: "",
      onlyNonNormal: false,
    }
  },

  async mounted() {
    await this.getRings();
    document.CSRF_TOKEN = $("input[name=csrfmiddlewaretoken]")[0].value
  },

  computed: {
    filteredRings() {
      const search = this.search.toLowerCase()
      const onlyNonNormal = this.onlyNonNormal
      return  Array.from(this.rings.list).filter(
          (ring) => {
            const validByName = search.length < 3 || ring.head_name.toLowerCase().indexOf(search) > -1
            const validByStatus = onlyNonNormal && !ring.is_normal_rotate_status || !onlyNonNormal
            return validByName && validByStatus;
          }
      )
    }
  },

  methods: {
    async getRings() {
      try {
        let resp = await fetch(
            "/ring-manager/api/access-rings",
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