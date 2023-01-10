<template>
<table class="table table-striped">
  <thead>
    <tr>
      <th scope="col"></th>
      <th scope="col">Имя</th>
      <th scope="col">IP</th>
      <th scope="col">Тип</th>
      <th scope="col">Модель</th>
      <th scope="col">Группа</th>
    </tr>
  </thead>
  <tbody>
      <tr v-for="dev in devices">
        <td>
            <a class="badge rounded-pill bg-primary text-light text-decoration-none"
               style="font-family: 'Yu Gothic UI Semilight', monospace; font-size: 1rem"
               data-bs-toggle_help="tooltip" data-bs-placement="top"
               data-bs-title="Просканировать интерфейсы в реальном времени"
               :href="'/device/' + dev.name + '?current_status=1'"
            >I</a>

            <a v-if="dev.port_scan_protocol !== 'snmp'"
               class="badge rounded-pill bg-info text-dark text-decoration-none"
               style="font-family: 'Yu Gothic UI Semilight', monospace; font-size: 1rem"
               data-bs-toggle_help="tooltip" data-bs-placement="top"
               data-bs-title="Просканировать интерфейсы и VLANS в реальном времени"
               :href="'/device/' + dev.name + '?current_status=1&vlans=1'"
            >V</a>

            <a class="badge rounded-pill bg-secondary text-decoration-none"
               style="font-family: 'Yu Gothic UI Semilight', monospace; font-size: 1rem"
               data-bs-toggle_help="tooltip" data-bs-placement="top"
               data-bs-title="Последние сохраненные интерфейсы"
               :href="'/device/' + dev.name"
            >L</a>
        </td>
        <td><span class="nowrap">{{ dev.name }}</span></td>
        <td>{{ dev.ip }}</td>
        <td>{{ dev.vendor }}</td>
        <td>{{ dev.model }}</td>
        <td>{{ dev.group }}</td>
      </tr>
  </tbody>
</table>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  name: "devices-table",
  props: {
      devices: {
        required: true,
        type: Array,
        default: function () { return [] }
      }
  }
})
</script>