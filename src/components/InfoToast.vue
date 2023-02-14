<template>
<div aria-live="polite" aria-atomic="true" class="sticky-top">
  <div class="toast-container position-absolute top-0 end-0 p-3">

    <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <svg class="bd-placeholder-img rounded me-2" width="20" height="20" xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true" preserveAspectRatio="xMidYMid slice" focusable="false">
            <rect id="toast_color"  width="100%" height="100%"
                  :fill="toast.color"></rect>
        </svg>
        <strong id="toast_title" class="me-auto">
          {{ toast.title }}
        </strong>
        <small id="toast_extra" class="text-muted">только что</small>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Закрыть"></button>
      </div>
      <div id="toast_message" class="toast-body">
        {{ toast.message }}
      </div>
    </div>

  </div>
</div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
    toast: {
      required: true,
      type: { color: "", title: "", message: "" }
    }
  }
})
</script>