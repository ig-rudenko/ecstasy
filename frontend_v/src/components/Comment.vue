<template>
  <!--Посмотреть комментарии-->
  <div v-if="interface.comments && interface.comments.length">
    <Button @click="showCommentsPopup" text severity="secondary">
      <span style="position: absolute; text-align: center; font-size: 14px; top: 8px"
            :style="{padding: '0 ' + (3 - String(interface.comments.length).length) * 5 + 'px'}">
          {{ interface.comments.length }}
      </span>
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="#ffc107"
           class="comment-active bi bi-chat-right-text" viewBox="0 0 16 16">
        <path
            d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
      </svg>
    </Button>

    <!--Блок комментариев-->
    <Popover ref="comment">

      <div class="card py-2">

        <!--Добавить новый-->
        <div style="text-align: right">
          <svg v-if="allowEdit" @click="registerCommentAction('add', null)"
               width="24" height="24" fill="#198754" viewBox="0 0 16 16" style="margin: 0 15px; cursor: pointer;">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
            <path
                d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"></path>
          </svg>
        </div>

        <!--Комментарии-->
        <div v-for="comment in interface.comments" class="flex" style="margin: 10px 15px;">
          <div class="flex flex-col gap-1" v-if="allowEdit">

            <!--Изменить-->
            <div @click="registerCommentAction('update', comment)" style="cursor: pointer">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#0d6efd" class="bi bi-pencil-square"
                   viewBox="0 0 16 16">
                <path
                    d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                <path fill-rule="evenodd"
                      d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
              </svg>
            </div>

            <!--Удалить-->
            <div @click="registerCommentAction('delete', comment)" data-bs-target="#modal-comment"
                 style="cursor: pointer">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#dc3545" class="bi bi-x-lg"
                   viewBox="0 0 16 16">
                <path
                    d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
              </svg>
            </div>
          </div>

          <div class="pl-3">
            <!--Пользователь комментария-->
            <div class="flex gap-2 items-center text-sm text-muted-color">
              <div>@{{ comment.user }}</div>
              <i class="pi pi-clock"/>
              <div>{{ formatDatetime(comment.createdTime) }}</div>
            </div>

            <!--ТЕКСТ комментария-->
            <div class="py-2" v-html="textToHtml(markedText?markText(comment.text, markedText):comment.text)"></div>
          </div>
        </div>

      </div>
    </Popover>

  </div>

  <!--Создание комментария-->
  <Button text severity="secondary"
          v-else-if="allowEdit"
          @click="registerCommentAction('add', null)">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#999" class="bi bi-chat-right-text"
         viewBox="0 0 16 16">
      <path
          d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
      <path
          d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
    </svg>
  </Button>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

import {markText, textToHtml} from "@/formats";
import {DeviceInterface, InterfaceComment} from "@/services/interfaces";
import commentService, {CommentAction} from "@/services/comments.ts";

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
    markedText: {required: false, type: String, default: ""},
    allowEdit: {required: false, type: Boolean, default: false},
  },
  methods: {
    textToHtml,
    markText,
    showCommentsPopup(event: Event) {
      // @ts-ignore
      this.$refs.comment.toggle(event)
    },

    registerCommentAction(action: CommentAction, comments: InterfaceComment | null) {
      commentService.registerCommentAction(action, comments, this.interface.name, this.deviceName)
    },

    formatDatetime(datetime: string): string {
      return new Date(datetime)
          .toLocaleString(
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
    },
  }
})
</script>