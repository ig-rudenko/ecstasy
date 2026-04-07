<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button text rounded icon="pi pi-arrow-left" @click="backToAllRings"/>
        <div>
          <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ rings.selectedRing.name }}</div>
          <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">{{ rings.selectedRing.description }}</div>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Tag :severity="ringActive ? 'success' : 'danger'" :value="ringActive ? 'Активно' : 'Неактивно'"/>
        <Tag :severity="rotatingNow ? 'warn' : 'secondary'" :value="rotatingNow ? 'Идёт разворот' : 'Ожидание'"/>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,26rem),minmax(0,1fr)]">
      <div class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 p-5 sm:p-6 backdrop-blur">
        <div class="rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/50 dark:bg-gray-950/20 p-4">
          <div class="text-sm uppercase tracking-wide text-gray-500 dark:text-gray-400">Разворот кольца</div>
          <div class="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">{{ rings.selectedRing.name }}</div>
          <div class="mt-4 text-sm text-gray-600 dark:text-gray-300">VLAN для разворота:</div>
          <div class="mt-2 flex flex-wrap gap-2">
            <Badge v-for="vlan in rings.selectedRing.vlans" :key="vlan" severity="secondary">{{ vlan }}</Badge>
          </div>
        </div>

        <Button
            class="mt-5 !rounded-2xl w-full"
            :loading="getSolutionsActive || rotatingNow"
            loading-icon=""
            @click="getSolutions"
            :disabled="rotatingNow">
          <span v-if="getSolutionsActive || rotatingNow" class="flex items-center gap-2">
            <i class="pi pi-spin pi-spinner"/>
            Ожидайте
          </span>
          <span v-else class="flex items-center justify-center gap-2">
            <i class="pi pi-sitemap"/>
            {{ !solutions.length ? "Проверить статус и построить план решений" : "Обновить статус и построить новый план" }}
          </span>
        </Button>

        <div v-if="reversedErrors.length" class="mt-5 space-y-3">
          <template v-for="error in reversedErrors" :key="`${error.time}-${error.text}`">
            <div class="text-xs font-mono text-gray-500 dark:text-gray-400"># {{ error.time }}</div>
            <Message severity="error">{{ error.text }}</Message>
          </template>
        </div>

        <div v-if="reversedInfos.length" class="mt-5 space-y-3">
          <template v-for="info in reversedInfos" :key="`${info.time}-${info.text}`">
            <div class="text-xs font-mono text-gray-500 dark:text-gray-400"># {{ info.time }}</div>
            <Message severity="info">{{ info.text }}</Message>
          </template>
        </div>

        <div v-if="solutions.length" class="mt-5">
          <div class="mb-3 text-xs font-mono text-gray-500 dark:text-gray-400"># {{ solutionsTime }}</div>
          <Solutions
              :solutions="solutions"
              :safe-solutions="safeSolutions"
              :rotating-now="rotatingNow"
              :performed="solutionsPerformed"
              @submitSolutions="submitSolutions"
          />
        </div>
      </div>

      <div class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/50 dark:bg-gray-950/20 p-4 sm:p-6">
        <RingView :points="points"/>
      </div>
    </div>
  </div>
</template>

<script>
import RingView from "./RingView.vue";
import Solutions from "./Solutions.vue";
import api from "@/services/api";
import errorFmt from "@/errorFmt.ts";

export default {
  name: "RingMenu",
  components: {Solutions, RingView},
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
      points: [],
      solutions: [],
      safeSolutions: true,
      solutionsTime: "",
      solutionsPerformed: false,
      getSolutionsActive: false,
      rotatingNow: true,
      ringActive: true,
      errors: [],
      infos: []
    }
  },
  async mounted() {
    await this.getRing()
    await this.getLastSolutions()
    await this.periodicalRingCheck()
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
        let resp = await api.get("/api/v1/ring-manager/transport-ring/" + this.rings.selectedRing.name)
        this.points = resp.data.points;
        this.rotatingNow = resp.data.rotating;
        this.ringActive = resp.data.active;
      } catch (e) {
        console.log(e)
        this.errors.push(
            {
              text: errorFmt(e),
              time: this.getTime()
            }
        )
      }
    },

    async periodicalRingCheck() {
      try {
        let resp = await api.get("/api/v1/ring-manager/transport-ring/" + this.rings.selectedRing.name + "/status")
        this.rotatingNow = resp.data.rotating
        this.ringActive = resp.data.active
      } catch (e) {
        console.log(e)
        this.errors.push(
            {
              text: errorFmt(e),
              time: this.getTime()
            }
        )
      }
      setTimeout(this.periodicalRingCheck, 5000)
    },

    async getLastSolutions() {
      try {
        const resp = await api.get("/api/v1/ring-manager/transport-ring/" + this.rings.selectedRing.name + "/solutions/last")
        this.solutions = resp.data.solutions
        this.safeSolutions = resp.data.safeSolutions
        if (resp.data.solutionsTime) {
          this.solutionsTime = this.formatDateToTime(new Date(resp.data.solutionsTime * 1000))
        }
      } catch (error) {
        console.log(error)
        this.errors.push(
            {
              text: errorFmt(error),
              time: this.getTime()
            }
        )
      }
    },

    async getSolutions() {
      if (this.getSolutionsActive) return;

      this.getSolutionsActive = true
      this.solutions = []
      this.solutionsPerformed = false
      this.solutionsTime = ""
      this.errors = []
      this.infos = []

      try {
        const resp = await api.get("/api/v1/ring-manager/transport-ring/" + this.rings.selectedRing.name + "/solutions")
        this.points = resp.data.points
        this.solutions = resp.data.solutions
        this.safeSolutions = resp.data.safeSolutions
        this.solutionsTime = this.getTime()

      } catch (e) {
        console.log(e)
        this.errors.push(
            {
              text: errorFmt(e),
              time: this.getTime()
            }
        )
      }
      this.getSolutionsActive = false
    },

    async submitSolutions() {
      if (this.rotatingNow) return;
      this.rotatingNow = true
      this.errors = []
      this.infos = []

      try {
        const resp = await api.post("/api/v1/ring-manager/transport-ring/" + this.rings.selectedRing.name + "/solutions")

        this.solutions = await resp.data.solutions
        this.points = resp.data.points
        this.solutionsPerformed = true
        this.solutionsTime = this.getTime()
        this.rotatingNow = false

      } catch (e) {
        console.log(e)
        this.errors.push(
            {
              text: errorFmt(e),
              time: this.getTime()
            }
        )
        this.rotatingNow = false
      }
    },

    backToAllRings() {
      this.rings.selectedRing = null;
    },
  },
}
</script>
