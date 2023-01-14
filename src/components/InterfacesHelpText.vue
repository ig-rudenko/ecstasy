<template>
<div style="padding: 0 10px">
    <blockquote class="blockquote">
        <p v-if="device_status === 1 && current_status && auto_update">Актуальное состояние интерфейсов</p>
        <p v-else-if="device_status === -1 && auto_update">Опрашиваем интерфейсы</p>
        <p v-else-if="current_status && auto_update">Обновляем интерфейсы</p>
        <p v-else-if="current_status">Данные интерфейсы были опрошены <br>{{ time_passed }} назад</p>
        <p v-else>Интерфейсы были взяты <br>@{{ last_interface_update || " которого не было" }}</p>
    </blockquote>

    <div v-if="!current_status">
      <a class="btn" style="background-color: #93c4ff" data-bs-toggle="modal" data-bs-target="#staticBackdrop"
         @click="updateCurrentStatus">
          Посмотреть текущее состояние портов
      </a>
    </div>

</div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      device_status: {
        required: true,
        type: Number
      },
      auto_update: {
        required: true,
        type: Boolean
      },
      current_status: {
        required: true,
        type: Boolean
      },
      time_passed: {
        required: true,
        type: String,
      },
      last_interface_update: {
        type: String,
      },
      updateCurrentStatus: {
        required: true,
        type: Function
      }
  }
})
</script>