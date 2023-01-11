<template>
<table class="table table-striped">
  <thead>
    <tr>
      <th scope="col">IP</th>
      <th scope="col">Имя</th>
      <th scope="col">Тип</th>
      <th scope="col">Модель</th>
      <th scope="col">Группа</th>
    </tr>
  </thead>
  <tbody>
      <tr v-for="dev in devices">
        <td>{{ dev.ip }}</td>
        <td>
          <span class="nowrap">
            <a class="text-decoration-none" :href="'/device/' + dev.name"
               style="color: black;">
              {{ dev.name }}
            </a>
          </span>
        </td>
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
  props: {
      devices: {
        required: true,
        type: Array,
        default: function () { return [] }
      }
  }
})
</script>