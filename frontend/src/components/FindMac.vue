<template>
<div class="modal fade" id="modal-find-mac" tabindex="-1" aria-labelledby="ModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">

<!--      HEADER-->
      <div class="modal-header">
        <svg class="bi me-2" width="24" height="24" role="img"><use xlink:href="#search-icon"></use></svg>

        <h1 class="modal-title fs-5 text-center" id="modalLabel" style="padding-left: 10px">
            MAC: "<span id="modal-mac-str">{{mac}}</span>"
        </h1>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>

<!--      TEXT-->
      <div class="modal-body">
        <h4 id="modal-mac-content" class="fs-5">
            <svg style="vertical-align: top" xmlns="http://www.w3.org/2000/svg" width="24" height="28" fill="currentColor" class="bi bi-ethernet" viewBox="0 0 16 16">
              <path d="M14 13.5v-7a.5.5 0 0 0-.5-.5H12V4.5a.5.5 0 0 0-.5-.5h-1v-.5A.5.5 0 0 0 10 3H6a.5.5 0 0 0-.5.5V4h-1a.5.5 0 0 0-.5.5V6H2.5a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5ZM3.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm2 0h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5ZM9.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5Z"></path>
              <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2ZM1 2a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2Z"></path>
            </svg> Vendor: <small>{{vendor}}</small>
        </h4>

        <div id="modal-mac-result" class="py-3" style="text-align: center;">

          <div v-if="detailInfo.length" v-html="detailInfo"></div>
          <div v-else class="spinner-border" role="status"></div>

        </div>

      </div>

    </div>
  </div>
</div>
</template>


<script lang="ts">
import {defineComponent} from "vue";
import api_request from "../api_request";
import {AxiosResponse} from "axios";

type MACDetail = {
  vendor: string,
  address: string
}

export default defineComponent({
  props: {
    mac: {required: true, type: String}
  },
  data() {
    return {
      oldMac: "",
      vendor: "",
      detailInfo: ""
    }
  },
  updated() {
    // Если МАС адрес остался прежним, то не обновляем информацию
    if (this.oldMac === this.mac) return
    this.oldMac = this.mac
    // Очищаем старый вендор
    this.vendor = ""
    // Очищаем старую информацию
    this.detailInfo = ""
    // Ищем вендор
    this.getVendor()
    // Ищем детальную информацию
    this.macDetail()
  },

  methods: {
    getVendor() {
      if (!this.mac) return;
      api_request.get("/tools/ajax/mac_vendor/" + this.mac)
          .then(
              (value: AxiosResponse<MACDetail>) => {
                this.vendor = value.data.vendor
              },
              () => {this.vendor = "Не удалось определить"}
          )
          .catch(() => {this.vendor = "Не удалось определить"})
    },

    macDetail() {
      if (!this.mac) return;
      api_request.get("/tools/ajax/ip-mac-info/" + this.mac)
          .then(
              (value: AxiosResponse<string>) => {
                this.detailInfo = value.data
              },
              () => {this.detailInfo = "Не удалось определить"}
          )
          .catch(() => {this.detailInfo = "Не удалось определить"})
    }
  }
})
</script>