<template>
  <div class="row">

      <div class="col-md-6">
        <img src="/static/img/rj45-back.jpg" alt="RJ45-background" style="height: 100%; width: 100%;">
      </div>

      <div class="col-md-5">

        <div class="text-center">
          <button @click="startDiagnostic" class="btn btn-lg btn-outline-success py-3" id="modal-text">
            {{ diagnosticsStarted?'Диагностируем':'Запустить диагностику' }}
          </button>
        </div>

        <div v-if="diagInfo">
          <div v-if="diagInfo.len" class="py-3">
            Длина кабеля: {{diagInfo.len}}
          </div>

          <div class="py-3">
              Состояние: <span class="me-2">{{diagInfo.status}}</span>
              <svg :fill="statusColor(diagInfo.status)" xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 16 16">
                <path d="M14 13.5v-7a.5.5 0 0 0-.5-.5H12V4.5a.5.5 0 0 0-.5-.5h-1v-.5A.5.5 0 0 0 10 3H6a.5.5 0 0 0-.5.5V4h-1a.5.5 0 0 0-.5.5V6H2.5a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5ZM3.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm2 0h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5ZM9.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5Z"></path>
                <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2ZM1 2a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2Z"></path>
              </svg>
          </div>

          <div style="text-align: right;">

            <div v-if="diagInfo.pair1">
              Пара 1 - {{diagInfo.pair1.len}} м.
              <img title="open" style="vertical-align: middle; margin: 0 3px 0 10px; height: 40px"
                   :src="'/static/img/rj45-status-' + diagInfo.pair1.status + '-left.png'">
            </div>

            <div v-if="diagInfo.pair2">
              Пара 2 - {{diagInfo.pair2.len}} м.
              <img title="open" style="vertical-align: middle; margin-left: 12px; height: 40px"
                   :src="'/static/img/rj45-status-' + diagInfo.pair2.status + '-right.png'">
            </div>
          </div>
        </div>

        <div v-show="diagnosticsStarted" class="text-center">
            <div class="spinner-border spinner text-success" role="status"></div>
        </div>

      </div>
  </div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    port: {required: true, type: String}
  },
  data() {
    return {
      diagInfo: null,
      diagnosticsStarted: false
    }
  },
  methods: {
    async startDiagnostic() {
        this.diagInfo = null
        this.diagnosticsStarted = true
        let info = null
        try {
            let response = await fetch(
                "/device/api/" + this.deviceName + "/cable-diag?port=" + this.port
            )
            if (response.status === 200) info = await response.json()
        } catch (err) {
            console.log(err)
        }
        console.log(info)
        this.diagnosticsStarted = false
        this.diagInfo = info
    },
    statusColor(status) {
      let status_color = {
          'Up': '#39d286',
          'Down': '#ff4b4d',
          'Empty': '#19b7f4',
          'Open': '#c1c1c1',
          'Short': '#f4bd19',
          'Mismatch': '#1a1a1a',
      }
      return status_color[status]
    }
  },
})

</script>

<style scoped>
.spinner {
  height: 50px;
  width: 50px;
  margin: 20px;
}
</style>