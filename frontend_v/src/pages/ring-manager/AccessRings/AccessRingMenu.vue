<template>
  <div class="flex gap-3">
    <svg @click="backToAllRings" class="cursor-pointer me-4" xmlns="http://www.w3.org/2000/svg" width="32"
         height="32" fill="currentColor" viewBox="0 0 16 16">
      <path fill-rule="evenodd"
            d="M1.146 4.854a.5.5 0 0 1 0-.708l4-4a.5.5 0 1 1 .708.708L2.707 4H12.5A2.5 2.5 0 0 1 15 6.5v8a.5.5 0 0 1-1 0v-8A1.5 1.5 0 0 0 12.5 5H2.707l3.147 3.146a.5.5 0 1 1-.708.708l-4-4z"/>
    </svg>

    <svg v-if="points.length" @click="reloadRing" xmlns="http://www.w3.org/2000/svg" width="32"
         height="32" fill="currentColor" class="cursor-pointer" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
      <path
          d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
    </svg>
  </div>

  <div v-if="points.length" class="flex justify-center" style="margin: 20px">
    <RingView :points="points" :ports-color-always="true" :copy-head-to-tail="true"/>
  </div>

  <!--Загрузка-->
  <div v-else style="text-align: center;">
    <div class="text-2xl pb-5">Опрашиваем интерфейсы, пожалуйста, подождите</div>
    <div>
      <ProgressSpinner/>
    </div>
  </div>
</template>

<script>
import RingView from "../TransportRingRotate/RingView.vue";
import api from "@/services/api";

export default {
  name: "RingMenu",
  components: {RingView},
  props: {
    rings: {
      required: true,
      type: {
        list: Array,
        selectedRing: {head_name: String, ports: String, description: String}
      }
    }
  },
  data() {
    return {
      points: [],
      errors: [],
      infos: []
    }
  },
  async mounted() {
    await this.getRing()
  },

  computed: {
    reversedErrors() {
      return this.reverseArray(this.errors)
    },
    reversedInfos() {
      return this.reverseArray(this.infos)
    },

  },

  methods: {
    reverseArray(array) {
      let reversed = [];
      for (let i = array.length - 1; i >= 0; i--) {
        reversed.push(array[i]);
      }
      return reversed;
    },

    // Возвращает текущее время в формате «ЧЧ:ММ:СС» (часы, минуты, секунды).
    getTime() {
      let date = new Date()
      let padZero = n => n < 10 ? "0" + n : n
      return padZero(date.getHours()) + ":" + padZero(date.getMinutes()) + ":" + padZero(date.getSeconds())
    },

    // Принимает объект `Date` в качестве входных данных и возвращает отформатированную
    // строку, представляющую время в формате «ЧЧ:ММ:СС» (часы, минуты, секунды).
    formatDateToTime(date) {
      let padZero = n => n < 10 ? "0" + n : n
      return padZero(date.getHours()) + ":" + padZero(date.getMinutes()) + ":" + padZero(date.getSeconds())
    },

    async getRing() {
      try {
        const url = "/api/v1/ring-manager/access-ring/" +
            this.rings.selectedRing.head_name + "?ports=" +
            this.rings.selectedRing.ports
        let resp = await api.get(url)
        this.points = await resp.data.points

      } catch (e) {
        console.log(e)
        this.errors.push(
            {
              text: e,
              time: this.getTime()
            }
        )
      }
    },

    async reloadRing() {
      this.points = []
      await this.getRing()
    },

    backToAllRings() {
      this.rings.selectedRing = null;
    },
  },
}
</script>

<style scoped>

</style>
