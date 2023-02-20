<template>
<div class="container" id="port-info">
    <button type="button" class="btn btn">
      Всего <span class="badge text-bg-primary">{{ total_count }}</span>
    </button>

    <button type="button" class="btn btn">
      Online <span class="badge text-bg-success">{{ online_count }}</span>
    </button>
    <br><br>
<div class="table-responsive-lg">
    <table class="table" style="text-align: center">
      <thead>
        <tr>
          <th scope="col">ONT ID</th>
          <th scope="col">Статус</th>
          <th scope="col">Equipment ID</th>
          <th scope="col">RSSI [dBm]</th>
          <th scope="col">Serial</th>
          <th scope="col">Описание</th>
        </tr>
      </thead>
      <tbody>

        <template v-for="line in data.onts_lines">
          <OLT_ONT_Detail_info
              @find-mac="findMacEvent"
              @session-mac="sessionEvent"
              :interface="interface"
              :register-interface-action="registerInterfaceAction"
              :permission-level="permissionLevel"
              :line="line"
          />
        </template>

      </tbody>
    </table>
</div>
</div>

</template>

<script>
import {defineComponent} from "vue";
import OLT_ONT_Detail_info from "./OLT-ONT-Detail-Info.vue"

export default defineComponent({
  props: {
    permissionLevel: {required: true, type: Number},
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
    OLT_ONT_Detail_info,
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