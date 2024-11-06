<template>
  <div class="container flex flex-wrap gap-10 p-4" id="port-info">
    <div class="font-mono">
      <div class="flex gap-2 items-center">
        <div>Profile name: <strong id="profile-name">{{ data.profile_name }}</strong></div>
        <Button @click="dialogVisible=true" text severity="info" size="small">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#0fb0f5" class="bi bi-gear-fill"
               viewBox="0 0 16 16">
            <path
                d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"></path>
          </svg>
        </Button>
      </div>

      <p v-for="line in data.first_col">{{ line }}</p>
    </div>

    <div v-if="data.streams.length">
      <table class="table">
        <thead>
        <tr>
          <th></th>
          <th scope="col" class="text-center px-2 font-mono">Downstream</th>
          <th scope="col" class="text-center px-2 font-mono">Upstream</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="line in data.streams">
          <td class="px-2" style="text-align: right">{{ line.name }}</td>
          <td class="px-2 font-mono" style="text-align: center;" :style="{'background-color': line.down.color}">{{ line.down.value }}</td>
          <td class="px-2 font-mono" style="text-align: center;" :style="{'background-color': line.up.color}">{{ line.up.value }}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Modal CHANGE PROFILE -->
  <Dialog modal v-model:visible="dialogVisible" header="Выберите новый профиль для порта">

    <!--      TEXT-->
    <div class="modal-body" style="text-align: right; padding: 0 16px;">
      <div class="flex justify-center">
        <table class="table table-striped">
          <thead>
          <tr>
            <th></th>
            <th scope="col" class="font-mono text-center">Profile name</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="profile in data.profiles">
            <td class="p-2 text-left">{{ profile[0] }}</td>
            <td class="p-2 text-left">
              <button type="button" @click="changePortProfile(profile[0], profile[1])">
                {{ profile[1] }}
              </button>
            </td>
          </tr>

          </tbody>
        </table>
      </div>
    </div>
  </Dialog>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import api from "@/services/api";
import {DeviceInterface} from "@/services/interfaces";
import {errorToast, successToast} from "@/services/my.toast.ts";
import errorFmt from "@/errorFmt.ts";

type xDLSData = {
  profile_name: string,
  first_col: string[],
  streams: [
    {
      name: string,
      down: { color: string, value: string },
      up: { color: string, value: string }
    }
  ],
  profiles: Array<[string, string]>
}

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    data: {required: true, type: Object as PropType<xDLSData>},
    interface: {required: true, type: Object as PropType<DeviceInterface>}
  },
  data() {
    return {
      dialogVisible: false,
    }
  },

  methods: {

    async changePortProfile(profile_index: string, profile_name: string) {
      this.dialogVisible = false

      let data = {
        port: this.interface.name,
        index: profile_index
      }

      try {
        await api.post("/device/api/" + this.deviceName + "/change-dsl-profile", data)
        successToast("OK", 'Профиль был изменен на ' + profile_name)
      } catch (error: any) {
        errorToast("Ошибка при изменении профиля", errorFmt(error))
      }
    }
  }
})
</script>