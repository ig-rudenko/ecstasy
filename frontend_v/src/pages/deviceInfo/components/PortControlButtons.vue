<template>
  <div v-if="permissionLevel >= 2" class="flex flex-col gap-2 my-2">

    <!--     ВКЛЮЧИТЬ ПОРТ -->
    <Button class="text-green-600" text style="height: 16px; font-size: 10px;"
            @click="() => registerAction('up', interface.name, interface.description, deviceName)">
          <span data-bs-toggle="modal" data-bs-target="#modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                 class="bi bi-caret-up-fill" viewBox="0 0 16 16">
              <path
                  d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"></path>
            </svg>
          </span>
    </Button>

    <!--     ВЫКЛЮЧИТЬ ПОРТ -->
    <Button class="text-red-600" text style="height: 16px; font-size: 10px; padding: 0"
            @click="() => registerAction('down', interface.name, interface.description, deviceName)">
          <span data-bs-toggle="modal" data-bs-target="#modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                 class="bi bi-caret-down-fill" viewBox="0 0 16 16">
              <path
                  d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"></path>
            </svg>
          </span>
    </Button>
  </div>

  <!--     ПЕРЕЗАГРУЗКА ПОРТА -->
  <Button v-if="permissionLevel >= 1" text
          @click="() => registerAction('reload', interface.name, interface.description, deviceName)"
          class="text-orange-500">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="black" class="bi bi-arrow-clockwise"
         viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
      <path
          d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
    </svg>
  </Button>

</template>


<script lang="ts">
import {defineComponent, PropType} from "vue";

import {DeviceInterface} from "@/services/interfaces";
import interfaceControlService from "@/services/interface.control";

export default defineComponent({
  methods: {
    registerAction(action: "up" | "down" | "reload", port: string, description: string, device: string) {
      interfaceControlService.registerAction(action, port, description, device)
    }
  },
  props: {
    permissionLevel: {required: true, type: Number},
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
  },
})
</script>