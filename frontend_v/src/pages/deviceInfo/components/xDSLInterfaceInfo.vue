<template>
  <div class="container" id="port-info">
    <div class="row table-responsive-lg">
      <div class="col">
        <p>Profile name: <strong id="profile-name">{{ data.profile_name }}</strong>
          <button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#modal-change-profile"
                  style="vertical-align: initial;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#0fb0f5" class="bi bi-gear-fill"
                 viewBox="0 0 16 16">
              <path
                  d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"></path>
            </svg>
          </button>
        </p>

        <p v-for="line in data.first_col">{{ line }}</p>
      </div>

      <div class="col">
        <table class="table">
          <thead>
          <tr>
            <th></th>
            <th scope="col" style="text-align: center;">Downstream</th>
            <th scope="col" style="text-align: center;">Upstream</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="line in data.streams">
            <td style="text-align: right">{{ line.name }}</td>
            <td style="text-align: center;" :style="{'background-color': line.down.color}">{{ line.down.value }}</td>
            <td style="text-align: center;" :style="{'background-color': line.up.color}">{{ line.up.value }}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Modal CHANGE PROFILE -->
  <div class="modal fade" id="modal-change-profile" data-bs-backdrop="static" tabindex="-1" aria-labelledby="ModalLabel"
       aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
      <div class="modal-content">

        <div class="modal-header">
          <h1 class="modal-title fs-5 text-center" id="exampleModalLabel" style="padding-left: 10px">
            Выберите новый профиль для порта
          </h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>

        <!--      TEXT-->
        <div class="modal-body" style="text-align: right; padding: 0 16px;">
          <div class="row table-responsive-lg">
            <table class="table table-striped">
              <thead>
              <tr>
                <th></th>
                <th scope="col" style="text-align: center;">Profile name</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="profile in data.profiles">
                <td style="text-align: center;">{{ profile[0] }}</td>
                <td style="text-align: center;">
                  <button type="button" class="btn" @click="changePortProfile(profile[0], profile[1])">
                    {{ profile[1] }}
                  </button>
                </td>
              </tr>

              </tbody>
            </table>
          </div>
        </div>

        <!--      STATUS -->
        <div class="modal-open">
          <div class="text-center" hidden>
            <div class="spinner-border" role="status">
            </div>
          </div>
          <div v-if="changeSuccess!==null" :class="changeRespClasses">
            {{ changeText }}
          </div>
        </div>


      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import api from "@/services/api";
import {DeviceInterface} from "@/services/interfaces";

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
      changeSuccess: null as (boolean | null),
      changeText: ""
    }
  },

  computed: {
    changeRespClasses() {
      if (this.changeSuccess === true) return ['alert', 'alert-success']
      if (this.changeSuccess === false) return ['alert', 'alert-danger']
    }
  },

  methods: {

    changePortProfile(profile_index: string, profile_name: string) {

      let data = {
        port: this.interface.name,
        index: profile_index
      }

      api.post("/device/api/" + this.deviceName + "/change-dsl-profile", data)
          .then(
              () => {
                this.changeSuccess = true
                this.changeText = 'Профиль был изменен на ' + profile_name
              },
              () => {
                this.changeSuccess = false
                this.changeText = 'Ошибка'
              }
          )
          .catch(() => {
            this.changeSuccess = false
            this.changeText = 'Ошибка'
          })
    }
  }
})
</script>