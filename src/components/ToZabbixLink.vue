<template>
<div>
  <a
      v-if="zabbix_host_id"
      :href="'http://10.100.0.50/zabbix/hostinventories.php?hostid=' + zabbix_host_id"
      class="btn" target="_blank">
      <svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg"
           width="30" height="30" fill="currentColor" class="bi bi-signpost" viewBox="0 0 16 16">
        <path d="M7 1.414V4H2a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h5v6h2v-6h3.532a1 1 0 0 0 .768-.36l1.933-2.32a.5.5 0 0 0 0-.64L13.3 4.36a1 1 0 0 0-.768-.36H9V1.414a1 1 0 0 0-2 0zM12.532 5l1.666 2-1.666 2H2V5h10.532z"></path>
      </svg>
      <span style="margin-left: 10px">В Zabbix</span>
  </a>
</div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      zabbix_host_id: {
        required: true,
        type: Number,
        default: null
      }
  }
})
</script>