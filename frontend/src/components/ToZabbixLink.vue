<template>
<div>
  <a  style="width: 100%; text-align: left"
      v-if="zabbix_host_id"
      :href="zabbix_url + '/hostinventories.php?hostid=' + zabbix_host_id"
      class="btn" target="_blank">
      <svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 64 64">
        <path d="M0 0h64v64H0z" fill="#d31f26"/>
        <path d="M18.8 15.382h26.393v3.424l-21.24 26.027h21.744v3.784H18.293v-3.43l21.24-26.02H18.8z" fill="#fff"/>
      </svg>
      <span style="margin-left: 10px">В Zabbix</span>
  </a>
</div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      zabbix_host_id: { required: true, type: Number, default: null },
      zabbix_url: { required: true, type: Number, default: null }
  }
})
</script>