<template>
  <div class="overflow-x-auto">

    <div class="flex flex-wrap gap-3 items-center">
      <div>
        Всего <span class="px-2 rounded-full bg-primary text-white">{{ gponData.total_count }}</span>
      </div>
      <div>
        Online <span class="px-2 rounded-full bg-green-500 text-white">{{ gponData.online_count }}</span>
      </div>
    </div>

    <div class=" w-full">
      <table class="w-full ">
        <thead>
        <tr>
          <th scope="col" class="px-3 py-2">ONT ID</th>
          <th scope="col" class="px-3 py-2">Статус</th>
          <th scope="col" class="px-3 py-2">Последнее подключение</th>
          <th scope="col" class="px-3 py-2">Последнее отключение</th>
          <th scope="col" class="px-3 py-2">Причина</th>
          <th scope="col" class="px-3 py-2">Дистанция</th>
          <th scope="col" class="px-3 py-2">Rx/Tx мощность</th>
        </tr>
        </thead>
        <tbody>
        <template v-for="line in gponData.onts_lines">

          <ONTDetailInfo
              @find-mac="findMacEvent"
              @session-mac="sessionEvent"
              :device-name="deviceName"
              :line="line"
              :interface="interface"
              :permission-level="permissionLevel"
              :register-comment-action="registerCommentAction"
              :register-interface-action="registerInterfaceAction"
          />

        </template>
        </tbody>
      </table>
    </div>
  </div>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import ONTDetailInfo from "./ONTDetailInfo.vue";
import {DeviceInterface, InterfaceComment} from "@/services/interfaces.ts";

type ontData = {
  total_count: string,
  online_count: string,
  onts_lines: any[]
}

export default defineComponent({
  components: {
    ONTDetailInfo
  },
  emits: ["find-mac", "session-mac"],
  props: {
    interface: {required: true, type: Object as PropType<DeviceInterface>},
    deviceName: {required: true, type: String},
    permissionLevel: {required: true, type: Number},
    gponData: {required: true, type: Object as PropType<ontData>},
  },
  data() {
    return {
      showDetailInfo: false
    }
  },
  methods: {

    findMacEvent(mac: string) {
      this.$emit("find-mac", mac)
    },

    sessionEvent(mac: string, port: string) {
      this.$emit("session-mac", mac, port)
    },

  }
})
</script>