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

        <div v-if="sol.set_port_vlans.message.length" class="alert alert-primary alert-in-solution">{{sol.set_port_vlans.message}}</div>

        <div class="device-name">
          {{sol.set_port_vlans.device.name}}
        </div>
        <div style="padding: 5px">
          <span :class="vlanStatusClasses(sol.set_port_vlans.status)">
            {{vlanAction(sol.set_port_vlans.status)}}
          </span>
          VLAN
          <span class="badge bg-primary sol-badge" v-for="vlan in sol.set_port_vlans.vlans">{{vlan}} </span>
          на порту
          <span class="badge bg-primary sol-badge">{{sol.set_port_vlans.port}}</span>
        </div>
      </div>

    </div>

  </template>

</div>
</template>

<script>
export default {
  name: "Solutions",
  props: {
    solutions: {required: true}
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
  font-size: 1rem;
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