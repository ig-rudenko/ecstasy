<template>
<div class="container">
    <button type="button" class="btn btn">
      Всего <span class="badge text-bg-primary">{{ data.total_count }}</span>
    </button>

    <button type="button" class="btn btn">
      Online <span class="badge text-bg-success">{{ data.online_count }}</span>
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
        <template v-for="line in data.onts_lines" >

          <ONTDetailInfo
              @find-mac="findMacEvent"
              @session-mac="sessionEvent"
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

<script>
import {defineComponent} from "vue";
import ONTDetailInfo from "./ONTDetailInfo.vue";

export default defineComponent({
  props: {
    permissionLevel: {required: true, type: Number},
    registerCommentAction: {required: true, type: Function},
    registerInterfaceAction: {required: true, type: Function},
    data: {
      required: true,
      type: {
        total_count: String,
        online_count: String,
        onts_lines: []
      }
    },
    interface: {required: true, type: Object}
  },
  data() {
    return {
      showDetailInfo: false
    }
  },
  components: {
    ONTDetailInfo
  },
  methods: {

    findMacEvent: function (mac) {
      this.$emit("find-mac", mac)
    },

    sessionEvent: function (mac, port) {
      this.$emit("session-mac", mac, port)
    },

  }
})
</script>