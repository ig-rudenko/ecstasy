<template>
  <div v-if="displayMode" class="flex gap-2 items-center px-2">
    <div v-if="dynamicDescription.length" class="font-mono" v-html="dynamicDescription"></div>
    <div>
      <svg @click="startEditDesc" style="cursor: pointer;" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="grey" viewBox="0 0 16 16">
        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
      </svg>
    </div>
  </div>

  <div v-else class="px-2">

    <InputGroup>
      <Button outlined severity="secondary" size="small" icon="pi pi-times" @click="displayMode=true" />

      <Button outlined :loading="loading" size="small" icon="pi pi-check" severity="success" @click="setDescription"/>

      <InputText type="text" v-model="newDesc" :class="inputClasses" style="min-width: 130px;" class="w-full" />
    </InputGroup>

    <Message @click="errors=''" v-if="errors" severity="error" :pt="{content: {class: 'py-0'}}">{{ errors }}</Message>

  </div>
</template>


<script lang="ts">
import {defineComponent, PropType} from "vue";
import api from "@/services/api";
import {AxiosResponse} from "axios";
import {DeviceInterface} from "@/services/interfaces.ts";

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<DeviceInterface>}
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
          s => `<span class="bg-yellow-200 dark:bg-yellow-900 dark:bg-opacity-70"><a class="text-dark text-decoration-none" href="${this.interface.link!.url}">${s}</a></span>`
      )
    },
    inputClasses(): string[] {
      let classes = ["form-control"]
      if (this.errors) {
        classes.push("is-invalid")
      }
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

      api.post("/device/api/" + this.deviceName + "/change-description", data)
          .then(
              (value: AxiosResponse<{ description: string }>) => {
                // Отображаем новое описание
                this.interface.description = value.data.description;
                // Выходим из режима редактирования
                this.displayMode = true;
                // Ошибок нет
                this.errors = null;
                this.loading = false;
              },
              reason => {
                this.errors = reason.response.data ? reason.response.data.detail : reason.response;
                this.loading = false;
              }
          )
          .catch(reason => {
            this.errors = reason.response.data ? reason.response.data.detail : reason.response;
            this.loading = false;
          })
    },
  }
})
</script>
