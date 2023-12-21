<template>
<div class="offcanvas offcanvas-start" data-bs-scroll="true" data-bs-backdrop="false" tabindex="-1" id="offcanvasScrolling" aria-labelledby="offcanvasScrollingLabel">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title" id="offcanvasScrollingLabel">Информация с Zabbix</h5>
    <button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Закрыть"></button>
  </div>
  <div class="offcanvas-body">
    <div v-if="zabbixInfo">
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

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      zabbixInfo: {
        required: true,
        type: Object,
        default: function () {
          return {
            "description": null,
            "inventory": {}
          }
        }
      }
  }
})
</script>