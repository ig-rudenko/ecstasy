<template>
<div class="container">
    <button type="button" class="btn btn">
      Всего <span class="badge text-bg-primary">{{ gponData.total_count }}</span>
    </button>

    <button type="button" class="btn btn">
      Online <span class="badge text-bg-success">{{ gponData.online_count }}</span>
    </button>
    <br>
    <br>
<div class="table-responsive-lg">
    <table class="table" style="text-align: center">
      <thead>
        <tr>
          <th scope="col"></th>
          <th scope="col">ONT ID</th>
          <th scope="col">Статус</th>
          <th scope="col">Последнее подключение</th>
          <th scope="col">Последнее отключение</th>
          <th scope="col">Причина</th>
          <th scope="col">Дистанция</th>
          <th scope="col">Rx/Tx мощность</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="line in gponData.onts_lines" >

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
import Interface from "../types/interfaces";
import InterfaceComment from "../types/comments";

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
    interface: {required: true, type: Object as PropType<Interface>},
    deviceName: {required: true, type: String},
    permissionLevel: {required: true, type: Number},
    gponData: {required: true, type: Object as PropType<ontData>},
    registerCommentAction: {
      required: true,
      type: Function as PropType<(action:("add"|"update"|"delete"), comment: InterfaceComment, interfaceName: string) => void>
    },
    registerInterfaceAction: {
      required: true,
      type: Function as PropType<(action:("up"|"down"|"reload"), port: string, description: string) => void>
    }
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