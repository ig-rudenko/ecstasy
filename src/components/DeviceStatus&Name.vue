<template>
<h2 style="margin-bottom: 10px;">

    <span v-if="status === 1" class="text-success">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
          <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
        </svg>
    </span>

    <span v-else-if="status === 0" class="text-danger">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-x-circle-fill" viewBox="0 0 16 16">
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"></path>
        </svg>
    </span>

    <span v-if="deviceName"><name style="word-wrap: break-word">{{ deviceName }}</name> ({{ deviceIp }})</span>
    <span v-else><name class="placeholder col-6"></name></span>
</h2>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      status: {
        required: true,
        type: Number,
        default: -1
      },
      deviceName: {
        required: true,
        type: String,
        default: ""
      },
      deviceIp: {
        required: true,
        type: String,
        default: ""
      }
  }
})
</script>