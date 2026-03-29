<template>
  <div class="inline-flex max-w-full items-center gap-3 rounded-2xl border border-gray-200/70 bg-white/80 px-4 py-3 text-sm text-gray-700 dark:border-gray-700/70 dark:bg-gray-950/40 dark:text-gray-200">
    <i class="pi pi-info-circle text-indigo-500 dark:text-indigo-300"/>

    <p v-if="deviceStatus === 1 && currentStatus && autoUpdate">
      Актуальное состояние интерфейсов
    </p>

    <div v-else-if="deviceStatus === -1 && autoUpdate">
      Опрашиваем интерфейсы
    </div>

    <p v-else-if="currentStatus && autoUpdate">
      Обновляем интерфейсы
    </p>

    <p v-else-if="currentStatus">
      Данные интерфейсы были опрошены {{ timePassed }}
    </p>

    <p v-else>
      Интерфейсы были взяты @{{ lastInterfaceUpdate || " которого не было" }}
    </p>
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
