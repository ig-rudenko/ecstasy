<template>

  <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
    <symbol id="port-down-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="red" class="bi bi-arrow-bar-down"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M1 3.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5zM8 6a.5.5 0 0 1 .5.5v5.793l2.146-2.147a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 .708-.708L7.5 12.293V6.5A.5.5 0 0 1 8 6z"></path>
      </svg>
    </symbol>
    <symbol id="port-up-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="green" class="bi bi-arrow-bar-up"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M8 10a.5.5 0 0 0 .5-.5V3.707l2.146 2.147a.5.5 0 0 0 .708-.708l-3-3a.5.5 0 0 0-.708 0l-3 3a.5.5 0 1 0 .708.708L7.5 3.707V9.5a.5.5 0 0 0 .5.5zm-7 2.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5z"></path>
      </svg>
    </symbol>
    <symbol id="port-reload-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="orange" class="bi bi-arrow-repeat"
           viewBox="0 0 16 16">
        <path
            d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"></path>
        <path fill-rule="evenodd"
              d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"></path>
      </svg>
    </symbol>
  </svg>


  <!-- Modal -->
  <Dialog modal v-model:visible="interfaceControlService.dialogVisible" header="Внимание">
    <template #header>
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" class="fill-red-500" viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
        <path
            d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"></path>
      </svg>
      <div class="text-center text-2xl" style="padding-left: 10px">
        Внимание
      </div>
    </template>
    <div>
      <div class="flex flex-wrap gap-2 py-6 justify-center text-2xl" v-if="interfaceControlService.portAction.action">
        <div>Вы уверены, что хотите {{ interfaceControlService.portAction.name }}</div>
        <svg class="" width="24" height="24">
          <use v-if="interfaceControlService.portAction.name === 'включить'" xlink:href="#port-up-icon"></use>
          <use v-else-if="interfaceControlService.portAction.name === 'выключить'" xlink:href="#port-down-icon"></use>
          <use v-else-if="interfaceControlService.portAction.name === 'перезагрузить'" xlink:href="#port-reload-icon"></use>
        </svg>
        <div>{{ interfaceControlService.portAction.port }}</div>
        <div>{{ interfaceControlService.portAction.desc }}?</div>
      </div>
      <div v-else class="text-center textl-xl">
        Неверное действие
      </div>

      <!--      BUTTONS-->
      <div class="flex flex-wrap gap-2 justify-end">

        <Button icon="pi pi-times" label="Отмена" severity="secondary"
                @click="() => interfaceControlService.closeDialog()"/>

        <Button icon="pi pi-check" v-show="interfaceControlService.portAction.action" @click="() => submitPortAction(false)"
                label="Без сохранения конфигурации"/>

        <Button icon="pi pi-check" severity="success" label="Сохранить конфигурацию после" v-show="interfaceControlService.portAction.action"
                @click="() => submitPortAction(true)"/>
      </div>
    </div>
  </Dialog>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import interfaceControlService from "@/services/interface.control";


export default defineComponent({
  data() {
    return {
      interfaceControlService: interfaceControlService
    }
  },
  methods: {
    submitPortAction(save: boolean) {
      interfaceControlService.submitPortAction(save);
    }
  }
})
</script>