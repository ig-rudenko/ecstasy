<template>
<h2 style="margin-top: 10px;">

<!--  Оборудование Доступно-->
    <span v-if="status === 1" class="text-success">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
          <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
        </svg>
    </span>

<!--  Оборудование Недоступно-->
    <span v-else-if="status === 0" class="text-danger">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-x-circle-fill" viewBox="0 0 16 16">
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"></path>
        </svg>
    </span>

<!--  Неизвестное состояние-->
    <span v-else class="text-secondary">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-question-circle" viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
        <path d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286zm1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94z"/>
      </svg>
    </span>


<!--  Название оборудования-->
    <span style="padding: 10px; vertical-align: middle;">{{ deviceName }}</span>
    <span v-show="deviceIp" class="badge bg-primary" style="vertical-align: middle;">{{deviceIp}}</span>
    <span style="position: absolute;">
      <svg @click="copyIP" class="copy-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 32px; cursor: pointer;">
        <path d="M5.5028 4.62704L5.5 6.75V17.2542C5.5 19.0491 6.95507 20.5042 8.75 20.5042L17.3663 20.5045C17.0573 21.3782 16.224 22.0042 15.2444 22.0042H8.75C6.12665 22.0042 4 19.8776 4 17.2542V6.75C4 5.76929 4.62745 4.93512 5.5028 4.62704ZM17.75 2C18.9926 2 20 3.00736 20 4.25V17.25C20 18.4926 18.9926 19.5 17.75 19.5H8.75C7.50736 19.5 6.5 18.4926 6.5 17.25V4.25C6.5 3.00736 7.50736 2 8.75 2H17.75ZM17.75 3.5H8.75C8.33579 3.5 8 3.83579 8 4.25V17.25C8 17.6642 8.33579 18 8.75 18H17.75C18.1642 18 18.5 17.6642 18.5 17.25V4.25C18.5 3.83579 18.1642 3.5 17.75 3.5Z"></path>
      </svg>
      <span v-if="copied" class="card copy-tooltip p-1 p-2 shadow">Скопировано!</span>
    </span>

  <span v-if="consoleUrl && consoleUrl.length > 0" style="position: absolute;right: 20px;">
      <a :href="consoleUrl" target="_blank" class="text-dark">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
          <path d="M0 3a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm9.5 5.5h-3a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1m-6.354-.354a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2a.5.5 0 1 0-.708.708L4.793 6.5z"></path>
        </svg>
      </a>
    </span>

</h2>
</template>

<script lang="ts">
import {defineComponent} from "vue";


export default defineComponent({
  props: {
      status: { required: true, type: Number },
      deviceName: { required: true, type: String },
      deviceIp: { required: true, type: String },
      consoleUrl: {required: true, type: String},
  },
  data() {
    return {
      copied: false
    }
  },
  methods: {
    copyIP() {
      // @ts-ignore
      this.$copyText(this.deviceIp).then(() => {
        this.copied = true
        setTimeout(() => {this.copied = false}, 1000)
      })
    }
  }
})
</script>

<style scoped>
.copy-tooltip {
  font-size: 0.8rem;
  display: inline;
  position: absolute;
  top: 3px;
}
</style>