<template>
<div>
  <button v-tooltip.bottom="'Подробная информация'" class="btn" type="button" style="width: 100%; text-align: left"
          data-bs-toggle="offcanvas" data-bs-target="#offcanvasScrolling"
          aria-controls="offcanvasScrolling">
      <svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-info-square" viewBox="0 0 16 16">
        <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"></path>
        <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"></path>
      </svg>
  </button>
</div>

<div class="offcanvas offcanvas-start" data-bs-scroll="true" data-bs-backdrop="false" tabindex="-1" id="offcanvasScrolling" aria-labelledby="offcanvasScrollingLabel">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title" id="offcanvasScrollingLabel">Информация с Zabbix</h5>
    <button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Закрыть"></button>
  </div>
  <div class="offcanvas-body">
    <div v-if="zabbixInfo">

      <div v-if="!zabbixInfo.monitoringAvailable" class="alert alert-danger mb-2">Снято с мониторинга</div>

      <div class="border d-flex flex-wrap mb-4 p-2 rounded-2">
        <div v-for="imageURL in images" class="p-3">
          <Image :src="imageURL" alt="Image" width="120" preview/>
        </div>
      </div>

      <div v-if="zabbixInfo.description" class="card card-body">
        {{ zabbixInfo.description }}
      </div>
      <div v-for="(value, key) in zabbixInfo.inventory">
        <p>{{ key }}:</p>
        <ul style="white-space: pre-line">{{ value }}</ul>
      </div>
    </div>
  </div>
</div>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import Image from "primevue/image";

import {ZabbixInfo} from "../GeneralInfo";
import api_request from "../../../api_request";
import {AxiosResponse} from "axios";

export default defineComponent({
  props: {
    zabbixInfo: {required: true, type: {} as PropType<ZabbixInfo>}
  },
  components: {Image},
  data() {
    return {
      images: [] as string[]
    }
  },
  async mounted() {
      await this.getImages();
  },
  methods: {
    async getImages() {
      if (!this.zabbixInfo.inventory?.vendor || !this.zabbixInfo.inventory?.model) return;

      for (let i = 1; i < 10; i++) {
        const url = "/static/img/devices/"+
            this.zabbixInfo.inventory.vendor.toLowerCase()+"/"+this.zabbixInfo.inventory.model.toUpperCase().replace("/", "-")
            + "_" + i + ".png"
        await api_request.head(url)
            .then((value: AxiosResponse<any>) => {
              if (value.status !== 200) i = 10;
              this.images.push(url)
            })
      }
    },
  }
})
</script>