<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button text rounded icon="pi pi-arrow-left" @click="backToAllRings"/>
        <div>
          <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ rings.selectedRing.head_name }}</div>
          <div class="font-mono text-sm text-gray-500 dark:text-gray-400">{{ rings.selectedRing.ports }}</div>
        </div>
      </div>

      <Button
          v-if="points.length"
          outlined
          severity="secondary"
          icon="pi pi-refresh"
          label="Обновить"
          class="rounded-2xl"
          @click="reloadRing"/>
    </div>

    <div v-if="points.length" class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/50 dark:bg-gray-950/20 p-4 sm:p-6">
      <RingView :points="points" :ports-color-always="true" :copy-head-to-tail="true"/>
    </div>

    <div v-else class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 px-6 py-12 text-center backdrop-blur">
      <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">Опрашиваем интерфейсы, пожалуйста, подождите</div>
      <div class="mt-5">
        <ProgressSpinner/>
      </div>
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

    getTime() {
      let date = new Date()
      let padZero = n => n < 10 ? "0" + n : n
      return padZero(date.getHours()) + ":" + padZero(date.getMinutes()) + ":" + padZero(date.getSeconds())
    },

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
