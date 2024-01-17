<template>
  <div class="row" v-if="displayMode">
    <div v-if="dynamicDescription.length" class="col-auto" v-html="dynamicDescription"></div>
    <div class="col-auto">
      <svg @click="startEditDesc" style="cursor: pointer;"
           xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="grey" class="bi bi-pencil-square" viewBox="0 0 16 16">
        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
      </svg>
    </div>
  </div>

  <div v-else class="input-group">

    <span class="input-group-text btn-float">
      <svg @click="displayMode=true"
           xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="grey" class="bi-check-circle-fill" viewBox="0 0 16 16">
        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
      </svg>
    </span>

    <span class="input-group-text btn-float" style="border-left: none">

      <svg v-show="!loading" @click="setDescription" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#198754" class="bi-check-circle-fill" viewBox="0 0 16 16">
        <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
      </svg>

      <span v-show="loading" class="spinner-border" style="height: 24px;width: 24px;"></span>

    </span>

    <input type="text" v-model="newDesc" :class="inputClasses" style="min-width: 130px;">
    <div class="invalid-feedback">{{ errors }}</div>

  </div>
</template>


<script lang="ts">
import {defineComponent, PropType} from "vue";
import Interface from "../../../types/interfaces";
import api_request from "../../../api_request";
import {AxiosResponse} from "axios";

export default defineComponent({
  props: {
    deviceName: { required: true, type: String },
    interface: { required: true, type: Object as PropType<Interface> }
  },
  data() {
    return {
      displayMode: true,
      newDesc: this.interface.description,
      errors: null as any,
      loading: false
    }
  },
  computed: {
    dynamicDescription(): string {
      if (!this.interface.link) return this.interface.description || "";

      return this.interface.description.replace(
          new RegExp(this.interface.link.deviceName, 'ig'),
          s => `<mark><a class="text-dark text-decoration-none" href="${this.interface.link!.url}">${s}</a></mark>`
      )
    },
    inputClasses(): string[] {
      let classes = ["form-control"]
      if (this.errors) { classes.push("is-invalid") }
      return classes
    }
  },
  methods: {

    startEditDesc(): void {
      this.newDesc = this.interface.description;
      this.displayMode = false;
    },

    setDescription(): void {
      // Начинаем отправку
      this.loading = true;
      let data = {
        port: this.interface.name,
        description: this.newDesc,
      }
      
      api_request.post("/device/api/" + this.deviceName + "/change-description", data)
          .then(
              (value: AxiosResponse<{description: string}>) => {
                // Отображаем новое описание
                this.interface.description = value.data.description;
                // Выходим из режима редактирования
                this.displayMode = true;
                // Ошибок нет
                this.errors = null;
                this.loading = false;
              },
              reason => {this.errors = reason.response.data?reason.response.data.detail:reason.response;this.loading = false;}
          )
          .catch(reason => {this.errors = reason.response.data?reason.response.data.detail:reason.response;this.loading = false;})
    },
  }
})
</script>

<style>
.btn-float {
  cursor: pointer;
  padding: 0 0.3rem;
  background-color: white;
}
</style>