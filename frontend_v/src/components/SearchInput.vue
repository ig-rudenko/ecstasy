<template>
<div :class="formClasses" :style="formStyles" class="focus-within:shadow-xl">
    <i class="pi pi-search text-2xl mr-4"/>
    <input type="text" v-model="text" class="search-input bg-transparent  text-gray-900 dark:text-gray-300"
           autofocus :placeholder="placeholder" @input="$emit('update:modelValue', text)"
           @keyup.enter="$emit('submit_input')">
</div>
</template>


<script lang="ts">
import {defineComponent, StyleValue} from "vue";

export default defineComponent({
  props: {
    activeMode: { required: false, type: Boolean, default: false },
    placeholder: { required: false, type: String },
  },
  data() {
    return {
      text: ""
    }
  },
  emits: ["submit_input", "update:modelValue"],
  computed: {
    formClasses(): Array<string> {
      if (this.activeMode) {
        return ['search-form']
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

<style scoped>
.search-input {
  border: none;
  outline: none;
  flex: 1 1 auto;
  width: 1%;
}
.search-form {
  padding: 10px 12px;
  margin: 10px;
  border-radius: 10px;
  display: flex;
}
</style>