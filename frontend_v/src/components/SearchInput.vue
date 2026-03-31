<template>
  <IconField>
    <InputIcon class="pi pi-search" />
    <InputText type="text" v-model="text" fluid class="rounded-2xl"
           autofocus
           :placeholder="placeholder" @input="$emit('update:modelValue', text)"
           @keyup.enter="$emit('submit_input')" />
  </IconField>
</template>


<script lang="ts">
import {defineComponent, PropType} from "vue";

export default defineComponent({
  props: {
    initSearch: {required: false, type: String, default: ""},
    activeMode: {required: false, type: Boolean, default: false},
    placeholder: {required: false, type: String},
    inputClass: {required: false, type: Object as PropType<String|Object|string[]>},
  },
  data() {
    return {
      text: "",
    }
  },
  mounted() {
    if (this.initSearch) {
      this.text = this.initSearch
    }
  },
  emits: ["submit_input", "update:modelValue"],
})
</script>
