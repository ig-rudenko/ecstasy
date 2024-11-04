<template>
<div style="padding: 0 10px">

    <blockquote class="blockquote">

        <p v-if="deviceStatus === 1 && currentStatus && autoUpdate">
          Актуальное состояние интерфейсов
        </p>

        <div v-else-if="deviceStatus === -1 && autoUpdate" style="text-align: center">
          <div>
            Опрашиваем интерфейсы
          </div>
          <div class="spinner-grow text-primary" role="status" style="height: 80px; width: 80px;">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>

        <p v-else-if="currentStatus && autoUpdate">
          Обновляем интерфейсы
        </p>

        <p v-else-if="currentStatus">
          Данные интерфейсы были опрошены <br>{{ timePassed }}
        </p>

        <p v-else>
          Интерфейсы были взяты <br>@{{ lastInterfaceUpdate || " которого не было" }}
        </p>
    </blockquote>

    <div v-if="!currentStatus">
      <a class="btn" style="background-color: #93c4ff" data-bs-toggle="modal" data-bs-target="#staticBackdrop"
         @click="$emit('update')">
          Посмотреть текущее состояние портов
      </a>
    </div>

</div>
</template>

<script lang="ts">
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      deviceStatus: { required: true, type: Number},
      autoUpdate: { required: true, type: Boolean },
      currentStatus: { required: true, type: Boolean },
      timePassed: { required: true, type: String, },
      lastInterfaceUpdate: { required: false, type: null as any, default: null },
  },
  emits: ["update"]
})
</script>