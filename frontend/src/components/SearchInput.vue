<template>
<div :class="formClasses" :style="formStyles">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="grey" viewBox="0 0 16 16"
         class="bi bi-search" style="margin-right: 10px;">
      <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"></path>
    </svg>
    <input type="text" class="search-input" autofocus
           :placeholder="placeholder"
           @input="updateSearch"
           @keyup.enter="$emit('submit_input')">
</div>
</template>


<script lang="ts">
import {defineComponent, PropType, StyleValue} from "vue";

export default defineComponent({
  props: {
    updateSearch: { required: true, type: Function as PropType<(event: Event) => void> },
    activeMode: { required: false, type: Boolean, default: false },
    placeholder: { required: false, type: String },
  },
  emits: ["submit_input"],
  computed: {
    formClasses(): Array<string> {
      if (this.activeMode) {
        return ['search-form', 'shadow']
      }
      return ['search-form']
    },
    formStyles(): StyleValue {
      if (this.activeMode) {
        return {"color": "#9f9f9f", "border": "2px solid"}
      }
      return {}
    }
  }
})
</script>

<style>
.search-input {
  background-color: #efefef;
  border: none;
  outline: none;
  flex: 1 1 auto;
  width: 1%;
}
.search-form {
  padding: 10px 12px;
  margin: 10px;
  background-color: #efefef;
  border-radius: 10px;
  display: flex;
}
</style>