<template>
  <div v-if="showError" class="py-1 text-center">
    <div class="alert alert-danger">
      <svg @click="showError=false" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor"
           class="close-icon" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/>
      </svg>
      Можно добавить только {{ maxLimit }}
    </div>
  </div>
  <div class="d-flex flex-wrap py-4 justify-content-center">
    <div v-for="(sp, index) in initial" class="card p-3 m-2">

      <!-- Удаление -->
      <svg @click="initial.splice(index, 1)" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
           fill="currentColor" class="close-icon" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/>
      </svg>

      <div v-if="end3Type==='splitter'" class="me-2">
        <h6>Адрес
          <Asterisk/>
          <div class="flex align-items-center py-2">
            <Checkbox id="address" v-model="sp.buildAddress" :binary="true" class="me-2"/>
            <label for="address" class="ml-2">Использовать адрес дома</label>
          </div>
        </h6>
        <AddressGetCreate v-if="!sp.buildAddress && end3Type==='splitter'" :is-mobile="false" :data="sp">
        </AddressGetCreate>
      </div>

      <div class="me-3 py-3">
        <h6 class="px-2">Локация
          <Asterisk/>
        </h6>
        <InputText v-model.trim="sp.location" type="text" placeholder="5 подъезд 4 этаж" class="w-100"/>
      </div>

    </div>
  </div>
  <div>
    <button @click="addNew" class="btn btn-outline-primary">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1zm-6 8A1.5 1.5 0 0 1 1.5 10h1A1.5 1.5 0 0 1 4 11.5v1A1.5 1.5 0 0 1 2.5 14h-1A1.5 1.5 0 0 1 0 12.5v-1zm6 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm6 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>
      </svg>
      Добавить
    </button>
  </div>
</template>

<script>
import InputText from "primevue/inputtext/InputText.vue"
import Checkbox from "primevue/checkbox/Checkbox.vue"
import Asterisk from "./Asterisk.vue"
import AddressGetCreate from "./AddressGetCreate.vue";

export default {
  name: "SplitterAddForm.vue",
  components: {
    AddressGetCreate,
    Asterisk,
    Checkbox,
    InputText,
  },
  props: {
    initial: {required: true, type: Array},
    end3Type: {required: true, type: String},
    maxLimit: {required: false, default: -1}
  },
  data() {
    return {
      showError: false,
    }
  },
  methods: {
    addNew() {
      if (this.maxLimit > 0 && this.initial.length >= this.maxLimit) {
        this.showError = true
        return
      }
      this.initial.push(
          {
            buildAddress: true,
            address: null,
            location: ""
          }
      )
    }
  }
}
</script>

<style scoped>
.close-icon {
  text-align: right;
  position: absolute;
  top: -11px;
  right: -11px;
  cursor: pointer;
}
</style>