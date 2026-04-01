<template>
  <div class="flex flex-col gap-3">
    <template v-for="(sol, index) in solutions" :key="index">
      <div v-if="sol.hasOwnProperty('info')" class="solution-card">
        <div class="solution-index">{{ index + 1 }}.</div>
        <div class="flex-1">
          <Message severity="info">{{ sol.info.message }}</Message>
        </div>
      </div>

      <div v-if="sol.hasOwnProperty('error')" class="solution-card">
        <div class="solution-index">{{ index + 1 }}.</div>
        <div class="flex-1">
          <Message severity="error">{{ sol.error.message }}</Message>
        </div>
      </div>

      <div v-if="sol.hasOwnProperty('set_port_status')" class="solution-card">
        <div v-if="!performed" class="solution-index">{{ index + 1 }}.</div>
        <div v-else class="shrink-0">
          <SolutionStatus
              :status="sol.set_port_status.perform_status"
              :error="sol.set_port_status.error"
          />
        </div>

        <div class="flex-1">
          <Message severity="info" v-if="sol.set_port_status.message.length">
            {{ sol.set_port_status.message }}
          </Message>

          <div class="mt-3 font-semibold text-gray-900 dark:text-gray-100">{{ sol.set_port_status.device.name }}</div>
          <div class="mt-2 flex flex-wrap items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <span>Изменяем состояние порта</span>
            <Badge>{{ sol.set_port_status.port }}</Badge>
            <span>на</span>
            <span :class="portStatusClasses(sol.set_port_status.status)">{{ sol.set_port_status.status }}</span>
          </div>
        </div>
      </div>

      <div v-if="sol.hasOwnProperty('set_port_vlans')" class="solution-card">
        <div v-if="!performed" class="solution-index">{{ index + 1 }}.</div>
        <div v-else class="shrink-0">
          <SolutionStatus
              :status="sol.set_port_vlans.perform_status"
              :error="sol.set_port_vlans.error"
          />
        </div>

        <div class="flex-1">
          <Message severity="info" v-if="sol.set_port_vlans.message.length">
            {{ sol.set_port_vlans.message }}
          </Message>

          <div class="mt-3 font-semibold text-gray-900 dark:text-gray-100">
            {{ sol.set_port_vlans.device.name }}
          </div>
          <div class="mt-2 flex flex-wrap items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <span :class="vlanStatusClasses(sol.set_port_vlans.status)">
              {{ vlanAction(sol.set_port_vlans.status) }}
            </span>
            <span>VLAN</span>
            <Badge severity="secondary" v-for="vlan in sol.set_port_vlans.vlans" :key="vlan">{{ vlan }}</Badge>
            <span>на порту</span>
            <Badge>{{ sol.set_port_vlans.port }}</Badge>
          </div>
        </div>
      </div>
    </template>

    <div v-if="displaySubmitButton" class="pt-2">
      <Button severity="success" @click="showModal=!showModal" label="Выполнить решения" icon="pi pi-check"/>
    </div>
  </div>

  <Dialog v-model:visible="showModal" modal>
    <div class="text-base leading-relaxed text-gray-800 dark:text-gray-100">
      Соглашаясь, вы подтверждаете, что ознакомились с перечнем решений и он соответствует вашим требованиям.
      Все действия выполнятся автоматически.
    </div>
    <div class="mt-5 flex gap-3 justify-end">
      <Button severity="danger" icon="pi pi-times" autofocus @click="showModal=false" label="Отмена"/>
      <Button severity="success" icon="pi pi-check" @click="async () => {showModal=false; submitSolutions();}"
              label="Согласен, выполняй"/>
    </div>
  </Dialog>
</template>

<script>
import SolutionStatus from "./SolutionStatus.vue";

export default {
  name: "Solutions",
  components: {SolutionStatus},
  props: {
    solutions: {required: true},
    rotatingNow: {required: true},
    safeSolutions: {required: true},
    performed: {required: true},
  },
  data() {
    return {
      showModal: false,
    }
  },
  computed: {
    displaySubmitButton() {
      return !this.rotatingNow && !this.safeSolutions && !this.performed
    }
  },
  methods: {
    portStatusClasses(status) {
      if (status === "up") return ["inline-flex", "items-center", "rounded-xl", "bg-emerald-100", "px-2.5", "py-1", "font-medium", "text-emerald-700", "dark:bg-emerald-500/15", "dark:text-emerald-300"]
      return ["inline-flex", "items-center", "rounded-xl", "bg-red-100", "px-2.5", "py-1", "font-medium", "text-red-700", "dark:bg-red-500/15", "dark:text-red-300"]
    },
    vlanAction(status) {
      if (status === "delete") return "Удаляем"
      return "Добавляем"
    },

    vlanStatusClasses(status) {
      if (status === "delete") return ["inline-flex", "items-center", "rounded-xl", "bg-red-100", "px-2.5", "py-1", "font-medium", "text-red-700", "dark:bg-red-500/15", "dark:text-red-300"]
      return ["inline-flex", "items-center", "rounded-xl", "bg-emerald-100", "px-2.5", "py-1", "font-medium", "text-emerald-700", "dark:bg-emerald-500/15", "dark:text-emerald-300"]
    },
    submitSolutions() {
      this.$emit("submitSolutions")
    }
  },
}
</script>

<style scoped>
.solution-card {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 1.25rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.62);
}

.dark .solution-card {
  background: rgba(15, 23, 42, 0.35);
  border-color: rgba(71, 85, 105, 0.45);
}

.solution-index {
  min-width: 2rem;
  padding-top: 0.35rem;
  font-weight: 600;
  color: rgb(99 102 241);
}
</style>
