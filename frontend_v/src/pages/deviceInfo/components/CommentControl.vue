<template>

<!-- Modal -->
<div class="modal fade" id="modal-comment" tabindex="-1" data-bs-backdrop="static"
     aria-labelledby="ModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content">

<!--      HEADER-->
      <div class="modal-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"
             :fill="iconColor" class="bi bi-chat-right-text" viewBox="0 0 16 16">
          <path d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
          <path d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
        </svg>

        <h1 class="modal-title fs-5 text-center" style="padding-left: 10px">
            {{modalTitle}}
        </h1>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>

<!--      DESCRIPTION-->
      <div style="padding: 10px">
        <div v-if="comment.action === 'add' || comment.action === 'update'">
          <textarea class="form-control" v-model="comment.text" style="height: 170px;"></textarea>
        </div>

        <div v-else-if="comment.action === 'delete'" class="text-center">
          <strong>Вы уверены, что хотите удалить комментарий?</strong>
          <br>
          {{comment.text}}
        </div>

        <div v-else>
          <h3>Неверное действие</h3>
        </div>
      </div>

<!--      BUTTONS-->
      <div class="modal-footer">

        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
              <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"></path>
            </svg>
        </button>


        <button @click="() => comment.submit!()"
            id="modal-button-no-save" type="submit" class="btn btn-success">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
                <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
            </svg>
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
    comment: {
      required: true,
      type: Object as PropType<{id: number, text: string, user: string, action: (""|"add"|"update"|"delete"), interface: string, submit: Function|null}>
    }
  },
  computed: {
    modalTitle: function () {
      if (this.comment.action === "add") return "Создать комментарий для порта " + this.comment.interface
      if (this.comment.action === "update") return "Обновить комментарий порта " + this.comment.interface
      if (this.comment.action === "delete") return "Удалить комментарий порта " + this.comment.interface
    },
    iconColor: function () {
      if (this.comment.action === "add") return "#198754"
      if (this.comment.action === "update") return "#0d6efd"
      if (this.comment.action === "delete") return "#dc3545"
    }
  }
})
</script>