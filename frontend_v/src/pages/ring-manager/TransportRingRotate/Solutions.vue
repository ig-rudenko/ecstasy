<template>

  <div class="rounded-xl list-item py-3 solutions" aria-current="true">

    <template v-for="(sol, index) in solutions">

      <!--    INFO-->
      <div v-if="sol.hasOwnProperty('info')" class="alert alert-primary alert-solution">
        <div class="sol-index">{{ index + 1 }}.</div>
        <Message severity="info">{{ sol.info.message }}</Message>
      </div>

      <!--    ERROR-->
      <div v-if="sol.hasOwnProperty('error')" class="alert alert-danger alert-solution">
        <div class="sol-index">{{ index + 1 }}.</div>
        <Message severity="error">{{ sol.error.message }}</Message>
      </div>

      <!--    SET PORT STATUS-->
      <div v-if="sol.hasOwnProperty('set_port_status')" class="alert alert-solution">
        <!--Номер решения (по порядку)-->
        <div v-if="!performed" class="sol-index">{{ index + 1 }}.</div>
        <!--Для выполненного решения (статус)-->
        <div v-else>
          <SolutionStatus
              :status="sol.set_port_status.perform_status"
              :error="sol.set_port_status.error"
          />
        </div>

        <div class="solution-content">

          <!--Описание действия-->
          <Message severity="info" v-if="sol.set_port_status.message.length">
            {{ sol.set_port_status.message }}
          </Message>

          <!--Название оборудования-->
          <div class="device-name">{{ sol.set_port_status.device.name }}</div>

          <div style="padding: 5px">
            Изменяем состояние порта
            <Badge>{{ sol.set_port_status.port }}</Badge>
            на
            <span :class="portStatusClasses(sol.set_port_status.status)">{{ sol.set_port_status.status }}</span>
          </div>
        </div>
      </div>

      <!--    VLANS -->
      <Message severity="info" v-if="sol.hasOwnProperty('set_port_vlans')">

        <!--Номер решения (по порядку)-->
        <div v-if="!performed" class="sol-index">{{ index + 1 }}.</div>
        <!--Для выполненного решения (статус)-->
        <div v-else>
          <SolutionStatus
              :status="sol.set_port_vlans.perform_status"
              :error="sol.set_port_vlans.error"
          />
        </div>

        <div class="solution-content">

          <!--Описание действия-->
          <Message severity="info" v-if="sol.set_port_vlans.message.length">
            {{ sol.set_port_vlans.message }}
          </Message>

          <!--Название оборудования-->
          <div class="device-name">
            {{ sol.set_port_vlans.device.name }}
          </div>
          <div style="padding: 5px">

            <!--Добавляем/Удаляем-->
            <span :class="vlanStatusClasses(sol.set_port_vlans.status)">
            {{ vlanAction(sol.set_port_vlans.status) }}
          </span>
            VLAN
            <Badge severity="secondary" v-for="vlan in sol.set_port_vlans.vlans">{{ vlan }}</Badge>
            на порту
            <Badge>{{ sol.set_port_vlans.port }}</Badge>
          </div>
        </div>

      </Message>

    </template>

    <!--  Выполнить решения-->
    <div v-if="displaySubmitButton" class="gap-3 py-3 rounded-4" aria-current="true">
      <Button severity="success" @click="showModal=!showModal" label="Выполнить решения!" icon="pi pi-check"/>
    </div>

  </div>


  <!-- Modal -->
  <Dialog v-model:visible="showModal" modal>
    <div class="text-xl">
      Соглашаясь вы подтверждаете, что ознакомились с предложенным вам перечнем решений,
      а также с тем, что он удовлетворяет вашим требованиям.
      <br>
      Все действия выполнятся автоматически.
    </div>
    <div class="flex gap-3 py-3 justify-end">
      <Button severity="danger" icon="pi pi-times" autofocus @click="showModal=false" label="Отмена"/>
      <Button severity="success" icon="pi pi-check" @click="async () => {showModal=false; submitSolutions();}"
              label="Согласен, выполняй!"/>
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
    rotatingNow: {required: true},  // Выполняются ли в данный момент решения
    safeSolutions: {required: true},  // Безопасны ли решения (т.е. информационные они или затрагивают работу кольца)
    performed: {required: true},  // Отображаемые решения уже были выполнены
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
      if (status === "up") return ["badge", "bg-success", "sol-badge"]
      return ["badge", "bg-danger", "sol-badge"]
    },
    vlanAction(status) {
      if (status === "delete") return "Удаляем"
      return "Добавляем"
    },

    vlanStatusClasses(status) {
      if (status === "delete") return ["badge", "bg-danger", "sol-badge"]
      return ["badge", "bg-success", "sol-badge"]
    },
    submitSolutions() {
      this.$emit("submitSolutions")
    }
  },
}
</script>

<style scoped>
.solutions {
  display: flex;
  flex-direction: column;
}

.sol-index {
  text-align: left;
  padding-right: 10px;
}

.device-name {
  padding: 5px;
}

.sol-badge {
  font-size: 0.9rem;
}

.alert-solution {
  display: flex;
  flex-direction: row;
  border: 1px solid #d3d3d3;
}

.alert-in-solution {
  padding: 5px 10px;
  width: 100%;
  margin-bottom: 5px;
}

.solution-content {
  display: flex;
  flex-wrap: wrap;
}

</style>
