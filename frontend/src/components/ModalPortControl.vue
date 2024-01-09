<template>

<svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
  <symbol id="port-down-icon">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="red" class="bi bi-arrow-bar-down" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M1 3.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5zM8 6a.5.5 0 0 1 .5.5v5.793l2.146-2.147a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 .708-.708L7.5 12.293V6.5A.5.5 0 0 1 8 6z"></path>
    </svg>
  </symbol>
  <symbol id="port-up-icon">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="green" class="bi bi-arrow-bar-up" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M8 10a.5.5 0 0 0 .5-.5V3.707l2.146 2.147a.5.5 0 0 0 .708-.708l-3-3a.5.5 0 0 0-.708 0l-3 3a.5.5 0 1 0 .708.708L7.5 3.707V9.5a.5.5 0 0 0 .5.5zm-7 2.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5z"></path>
    </svg>
  </symbol>
  <symbol id="port-reload-icon">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="orange" class="bi bi-arrow-repeat" viewBox="0 0 16 16">
      <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"></path>
      <path fill-rule="evenodd" d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"></path>
    </svg>
  </symbol>
</svg>


<!-- Modal -->
<div class="modal fade" id="modal" tabindex="-1" data-bs-backdrop="static" aria-labelledby="ModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content">

<!--      HEADER-->
      <div class="modal-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor"
             class="bi bi-exclamation-circle" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
          <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"></path>
        </svg>

        <h1 class="modal-title fs-5 text-center" style="padding-left: 10px">
            Внимание
        </h1>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>

<!--      TEXT-->
      <div class="modal-body text-center">
          <h4 id="modal-text" v-if="portAction.action">
              Вы уверены, что хотите {{ portAction.name }}
              <svg class="bi me-2" width="24" height="24" role="img">
                <use v-if="portAction.name === 'включить'" xlink:href="#port-up-icon"></use>
                <use v-else-if="portAction.name === 'выключить'" xlink:href="#port-down-icon"></use>
                <use v-else-if="portAction.name === 'перезагрузить'" xlink:href="#port-reload-icon"></use>
              </svg>
            {{ portAction.port }} ?
          </h4>
          <h4 v-else>
            Неверное действие
          </h4>
      </div>

<!--      DESCRIPTION-->
      <div class="col text-center" style="margin-left: 20px">
          <h3 class="text-center">
            <span id="modal-port-desc" class="bg-light text-dark">{{ portAction.desc }}</span>
          </h3>
      </div>

<!--      BUTTONS-->
      <div class="modal-footer">

        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
              <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"></path>
            </svg>
            Отмена
        </button>


        <button
            v-show="portAction.action"
            @click="submit_portAction(false)"
            id="modal-button-no-save" type="submit" class="btn btn-info" data-bs-dismiss="modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
                <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
            </svg>
            Без сохранения конфигурации
        </button>

        <button
            v-show="portAction.action"
            @click="submit_portAction(true)"
            id="modal-button-save" type="submit" class="btn btn-success" data-bs-dismiss="modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
                <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
            </svg>
            Сохранить конфигурацию после
        </button>
      </div>
    </div>
  </div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

export default defineComponent({
  props: {
    portAction: {
      required: true,
      type: Object as PropType<{name: string, action: string, submit: Function|null, port: string, desc: string}>
    }
  },
  methods:{
    submit_portAction(save: boolean) {
      if (this.portAction.submit) {
        this.portAction.submit(save)
      }
    }
  }
})
</script>