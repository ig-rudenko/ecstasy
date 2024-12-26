<template>
<div class="pb-2">

    <div class="text-sm">

        <p v-if="deviceStatus === 1 && currentStatus && autoUpdate">
          Актуальное состояние интерфейсов
        </p>

        <div v-else-if="deviceStatus === -1 && autoUpdate" style="text-align: center">
          <div>
            Опрашиваем интерфейсы
          </div>
        </div>

        <p v-else-if="currentStatus && autoUpdate">
          Обновляем интерфейсы
        </p>

        <p v-else-if="currentStatus">
          Данные интерфейсы были опрошены {{ timePassed }}
        </p>

        <p v-else>
          Интерфейсы были взяты <br>@{{ lastInterfaceUpdate || " которого не было" }}
        </p>
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