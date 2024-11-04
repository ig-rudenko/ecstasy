<template>
  <div class="py-1">
  <span style="cursor: pointer" data-bs-toggle="modal" data-bs-target="#userActionsModal">
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
      <path
          d="M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm-5 6s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H1zM11 3.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 0 1h-4a.5.5 0 0 1-.5-.5zm.5 2.5a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1h-4zm2 3a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1h-2zm0 3a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1h-2z"></path>
    </svg>
    <span>Actions</span>
  </span>
  </div>


  <!-- Modal -->
  <div class="modal fade" id="userActionsModal" tabindex="-1" aria-labelledby="userActionsModalLabel"
       aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="userActionsModalLabel">User actions</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="error.status" class="alert alert-danger">
            Ошибка загрузки:<br>
            Статус: {{ error.status }}<br>
            {{ error.msg }}
          </div>

          <div v-for="act in actions" class="card p-3 mb-2 shadow-sm">

            <div class="d-flex align-items-center py-2">
              <img
                  :src="'https://ui-avatars.com/api/?size=32&name='+act.user+'&font-size=0.33&background=random&rounded=true'"
                  class="me-2" :alt="act.user">
              <span>{{ act.user }}</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="mx-2"
                   viewBox="0 0 16 16">
                <path
                    d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
              </svg>
              <span>{{ formatTime(act.time) }}</span>
            </div>

            <div>
              <span v-html="formatActionPrefix(act.action)"></span>
              {{ act.action }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script lang="ts">
import api from "@/services/api";
import {defineComponent} from "vue";

import {AxiosResponse} from "axios";

interface UserAction {
  action: string
  time: string
  user: string
}

export default defineComponent({
  name: "UserActionsButton",
  props: {
    deviceName: {required: true, type: String},
  },
  data() {
    return {
      actions: [] as UserAction[],
      error: {
        status: null,
        msg: null,
      }
    }
  },

  mounted() {
    if (!this.actions.length) {
      api.get("/device/api/" + this.deviceName + "/actions").then(
          (resp: AxiosResponse<UserAction[]>) => {
            this.actions = resp.data
          }
      ).catch(
          reason => {
            this.error.status = reason.response.status;
            this.error.msg = reason.response.data;
          }
      )
    }
  },

  methods: {
    formatActionPrefix(action: string): string {
      let prefix = ""
      // Статус порта
      if (action.match("up port")) {
        prefix = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="green" class="me-2" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 10a.5.5 0 0 0 .5-.5V3.707l2.146 2.147a.5.5 0 0 0 .708-.708l-3-3a.5.5 0 0 0-.708 0l-3 3a.5.5 0 1 0 .708.708L7.5 3.707V9.5a.5.5 0 0 0 .5.5zm-7 2.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5z"/>
                  </svg>`;
      } else if (action.match("down port")) {
        prefix = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="red" class="me-2" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M1 3.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5zM8 6a.5.5 0 0 1 .5.5v5.793l2.146-2.147a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 .708-.708L7.5 12.293V6.5A.5.5 0 0 1 8 6z"/>
                  </svg>`;
      } else if (action.match("reload port")) {
        prefix = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#ffc107" class="me-2" viewBox="0 0 16 16">
                    <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"/>
                    <path fill-rule="evenodd" d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"/>
                  </svg>`;
      }

      // Статус сохранения
      if (action.match("Without saving")) {
        prefix += `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#8b8b8b" class="me-2" viewBox="0 0 16 16">
                     <path d="M1.5 0h11.586a1.5 1.5 0 0 1 1.06.44l1.415 1.414A1.5 1.5 0 0 1 16 2.914V14.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5v-13A1.5 1.5 0 0 1 1.5 0ZM1 1.5v13a.5.5 0 0 0 .5.5H2v-4.5A1.5 1.5 0 0 1 3.5 9h9a1.5 1.5 0 0 1 1.5 1.5V15h.5a.5.5 0 0 0 .5-.5V2.914a.5.5 0 0 0-.146-.353l-1.415-1.415A.5.5 0 0 0 13.086 1H13v3.5A1.5 1.5 0 0 1 11.5 6h-7A1.5 1.5 0 0 1 3 4.5V1H1.5a.5.5 0 0 0-.5.5Zm9.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-1Z"/>
                   </svg>`
      } else if (action.match("Saved ERROR")) {
        prefix += `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#ff959f" class="me-2" viewBox="0 0 16 16">
                     <path d="M1.5 0h11.586a1.5 1.5 0 0 1 1.06.44l1.415 1.414A1.5 1.5 0 0 1 16 2.914V14.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5v-13A1.5 1.5 0 0 1 1.5 0ZM1 1.5v13a.5.5 0 0 0 .5.5H2v-4.5A1.5 1.5 0 0 1 3.5 9h9a1.5 1.5 0 0 1 1.5 1.5V15h.5a.5.5 0 0 0 .5-.5V2.914a.5.5 0 0 0-.146-.353l-1.415-1.415A.5.5 0 0 0 13.086 1H13v3.5A1.5 1.5 0 0 1 11.5 6h-7A1.5 1.5 0 0 1 3 4.5V1H1.5a.5.5 0 0 0-.5.5Zm9.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-1Z"/>
                   </svg>`
      } else if (action.match("Saved OK")) {
        prefix += `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#34ba7c" class="me-2" viewBox="0 0 16 16">
                     <path d="M1.5 0h11.586a1.5 1.5 0 0 1 1.06.44l1.415 1.414A1.5 1.5 0 0 1 16 2.914V14.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5v-13A1.5 1.5 0 0 1 1.5 0ZM1 1.5v13a.5.5 0 0 0 .5.5H2v-4.5A1.5 1.5 0 0 1 3.5 9h9a1.5 1.5 0 0 1 1.5 1.5V15h.5a.5.5 0 0 0 .5-.5V2.914a.5.5 0 0 0-.146-.353l-1.415-1.415A.5.5 0 0 0 13.086 1H13v3.5A1.5 1.5 0 0 1 11.5 6h-7A1.5 1.5 0 0 1 3 4.5V1H1.5a.5.5 0 0 0-.5.5Zm9.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-1Z"/>
                   </svg>`
      }
      return prefix
    },

    formatTime(datetime: string): string {
      const date = new Date(datetime)
      // Make a fuzzy time
      let delta = Math.round((Date.now() - date.getMilliseconds()) / 1000);
      let minute = 60,
          hour = minute * 60;
      let fuzzy = "";
      if (delta < 30) {
        fuzzy = 'just then.';
      } else if (delta < minute) {
        fuzzy = delta + ' seconds ago.';
      } else if (delta < 2 * minute) {
        fuzzy = 'a minute ago.'
      } else if (delta < hour) {
        fuzzy = Math.floor(delta / minute) + ' minutes ago.';
      }

      if (fuzzy.length) return fuzzy

      return date.toLocaleString(
          "ru",
          {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          }
      )

    }
  }

});
</script>

<style scoped>

</style>