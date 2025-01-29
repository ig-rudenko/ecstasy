<template>

  <Header/>

  <div v-if="rings.selectedRing === null" class="container mx-auto my-8">

    <div class="text-2xl pb-2">Доступные вам абонентские кольца: {{ filteredRings.length || '' }}</div>

    <div class="py-2">
      <InputText class="w-full" placeholder="Поиск" v-model.trim="search"/>
    </div>

    <label class="cursor-pointer w-fit flex items-center gap-2 mb-5" for="onlyNonNormal">
      <Checkbox class="form-check-input" v-model="onlyNonNormal" binary input-id="onlyNonNormal"/>
      Отображать только неверно развернутые
    </label>

    <div v-if="rings.list.length" class="grid sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">

      <div v-for="ring in filteredRings">
        <div class="h-full ring-card">
          <div class="inline justify-center mb-3 text-indigo-400 p-8">
            <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
          </div>
          <div class="text-xl font-mono cursor-pointer w-fit" @click="chooseRing(ring)">{{
              ring.head_name
            }}<br>{{ ring.ports }}
          </div>
          <div class="mt-4">
            {{ ring.description }}
            <Badge severity="warn" v-if="!ring.is_normal_rotate_status">Кольцо неверно развернуто</Badge>
          </div>
        </div>
      </div>
    </div>

    <!--    Загрузка-->
    <div v-else class="text-center">
      <ProgressSpinner/>
    </div>

  </div>

  <div v-else class="container mx-auto my-8">
    <AccessRingMenu :rings="rings"/>
  </div>

  <Footer/>

</template>

<script>
import AccessRingMenu from "./AccessRings/AccessRingMenu.vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import permissions from "@/services/permissions.ts";
import api from "@/services/api";

export default {
  name: "AccessRing",
  components: {Footer, Header, AccessRingMenu},
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
    if (!permissions.has('auth.access_rings')) {
      location.href = '/';
      return;
    }
    await this.getRings();
  },

  computed: {
    filteredRings() {
      const search = this.search.toLowerCase()
      const onlyNonNormal = this.onlyNonNormal
      return Array.from(this.rings.list).filter(
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
        const resp = await api.get("/api/v1/ring-manager/access-rings");
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
.ring-card {
  border: 1px solid #cdcdcd;
  padding: 20px;
  border-radius: 20px;
}

.ring-link {
  cursor: pointer;
}
</style>
