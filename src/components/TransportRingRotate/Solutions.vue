<template>

  <div>

  </div>

<div class="rounded-4 list-group-item py-3 solutions" aria-current="true">

  <template v-for="(sol, index) in solutions">

<!--    INFO-->
    <div v-if="sol.hasOwnProperty('info')" class="alert alert-primary alert-solution">
      <div class="sol-index">{{index+1}}.</div>
      <div>{{sol.info.message}}</div>
    </div>

<!--    ERROR-->
    <div v-if="sol.hasOwnProperty('error')" class="alert alert-danger alert-solution">
      <div class="sol-index">{{index+1}}.</div>
      <div>{{sol.error.message}}</div>
    </div>

<!--    SET PORT STATUS-->
    <div v-if="sol.hasOwnProperty('set_port_status')" class="alert alert-solution">
      <div class="sol-index">{{index+1}}.</div>

      <div class="solution-content">

        <div v-if="sol.set_port_status.message.length" class="alert alert-primary alert-in-solution">{{sol.set_port_status.message}}</div>

        <div class="device-name">{{sol.set_port_status.device.name}}</div>

        <div style="padding: 5px">
          Изменяем состояние порта
          <span class="badge bg-primary sol-badge">{{sol.set_port_status.port}}</span>
          на
          <span :class="portStatusClasses(sol.set_port_status.status)">{{sol.set_port_status.status}}</span>
        </div>
      </div>
    </div>

<!--    VLANS -->
    <div v-if="sol.hasOwnProperty('set_port_vlans')" class="alert alert-solution">
      <div class="sol-index">{{index+1}}.</div>

      <div class="solution-content">

<!--        Описание действия-->
        <div v-if="sol.set_port_vlans.message.length" class="alert alert-primary alert-in-solution">{{sol.set_port_vlans.message}}</div>

<!--        Название оборудования-->
        <div class="device-name">
          {{sol.set_port_vlans.device.name}}
        </div>
        <div style="padding: 5px">

<!--          Добавляем/Удаляем-->
          <span :class="vlanStatusClasses(sol.set_port_vlans.status)">
            {{vlanAction(sol.set_port_vlans.status)}}
          </span>
          VLAN
          <span class="badge bg-secondary sol-badge" v-for="vlan in sol.set_port_vlans.vlans">{{vlan}} </span>
          на порту
          <span class="badge bg-primary sol-badge">{{sol.set_port_vlans.port}}</span>
        </div>
      </div>

    </div>

  </template>

<!--  Выполнить решения-->
  <div v-if="!rotatingNow && !safeSolutions" class="gap-3 py-3 rounded-4" aria-current="true">
    <div class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#submitSolutionModal">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-2" viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
        <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
      </svg>
      <span style="vertical-align: middle;">Выполнить решения!</span>
    </div>
  </div>

</div>


<!-- Modal -->
<div class="modal fade" id="submitSolutionModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h1 class="modal-title fs-5" id="exampleModalLabel">Вы хотите применить данные решения?</h1>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        Соглашаясь вы подтверждаете, что ознакомились с предложенным вам перечнем решений,
        а также с тем, что он удовлетворяет вашим требованиям.
        <br>
        Все действия выполнятся автоматически.
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
        <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="submitSolutions">Согласен</button>
      </div>
    </div>
  </div>
</div>

</template>

<script>
export default {
  name: "Solutions",
  props: {
    solutions: {required: true},
    rotatingNow: {required: true},  // Выполняются ли в данный момент решения
    safeSolutions: {required: true}  // Безопасны ли решения (т.е. информационные они или затрагивают работу кольца)
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