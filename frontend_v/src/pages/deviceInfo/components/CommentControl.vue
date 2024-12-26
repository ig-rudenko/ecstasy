<template>

  <!-- Modal -->
  <Dialog modal v-model:visible="commentService.dialogVisible">
    <template #header>
      <div class="flex items-center gap-3 px-4">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"
             :fill="iconColor" class="bi bi-chat-right-text" viewBox="0 0 16 16">
          <path
              d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
          <path
              d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
        </svg>

        <div class="text-xl">{{ modalTitle }}</div>
      </div>
    </template>

    <!--      DESCRIPTION-->
    <div>
      <div v-if="commentService.commentObject.action === 'add' || commentService.commentObject.action === 'update'">
        <Textarea class="w-full p-3" autoResize autofocus v-model="commentService.commentObject.text" style="height: 170px;"></Textarea>
      </div>

      <div v-else-if="commentService.commentObject.action === 'delete'" class="text-center">
        <div class="text-xl font-bold">Вы уверены, что хотите удалить комментарий?</div>
        <div class="whitespace-break-spaces text-left p-3 border rounded-xl m-3">{{ commentService.commentObject.text }}</div>
      </div>

      <div v-else>
        <div class="text-center text-xl">Неверное действие</div>
      </div>
    </div>

    <!--      BUTTONS-->
    <div class="flex justify-end gap-2">
      <Button label="Нет" autofocus @click="commentService.dialogVisible = false" icon="pi pi-times" severity="secondary" />

      <Button v-if="commentService.commentObject.action === 'delete'" icon="pi pi-trash" label="Да" severity="danger"
              @click="() => submit()" />
      <Button v-else @click="() => submit()" icon="pi pi-check" label="Да"  severity="success" />
    </div>

  </Dialog>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import commentService from "@/services/comments.ts";

export default defineComponent({
  data() {
    return {
      commentService: commentService
    }
  },
  computed: {
    modalTitle: function () {
      if (commentService.commentObject.value.action === "add") {
        return "Создать комментарий для порта " + commentService.commentObject.value.interface;
      }
      if (commentService.commentObject.value.action === "update") {
        return "Обновить комментарий порта " + commentService.commentObject.value.interface;
      }
      if (commentService.commentObject.value.action === "delete") {
        return "Удалить комментарий порта " + commentService.commentObject.value.interface;
      }
    },

    iconColor: function () {
      if (commentService.commentObject.value.action === "add") return "#198754"
      if (commentService.commentObject.value.action === "update") return "#0d6efd"
      if (commentService.commentObject.value.action === "delete") return "#dc3545"
    }

  },

  methods: {
    submit() {
      commentService.submitCommentAction();
    }
  }
})
</script>