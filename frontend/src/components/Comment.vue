<template>
<!--Посмотреть комментарии-->
  <div v-if="interface.comments && interface.comments.length">
    <button @click="(<OverlayPanel>$refs.comment).toggle($event)" class="btn" style="border-color: white;">
        <span style="position: absolute; text-align: center; font-size: 14px;"
              :style="{padding: '0 ' + (3 - String(interface.comments.length).length) * 5 + 'px'}">
            {{interface.comments.length}}
        </span>
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="#ffc107" class="comment-active bi bi-chat-right-text" viewBox="0 0 16 16">
          <path d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
        </svg>
    </button>

      <!--Блок комментариев-->
    <OverlayPanel ref="comment">

        <div class="card py-2" style="width: 450px;">

          <!--Добавить новый-->
              <div style="text-align: right">
                <svg
                     v-if="registerCommentAction"
                     @click="registerCommentAction('add', null, interface.name)"
                     data-bs-toggle="modal" data-bs-target="#modal-comment"
                     xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#198754"
                     class="bi bi-plus-circle" viewBox="0 0 16 16"
                     style="margin: 0 15px; cursor: pointer;">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
                  <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"></path>
                </svg>
              </div>

          <!--Комментарии-->
              <div v-for="comment in interface.comments"
                   class="d-flex row" style="margin: 10px 15px;">

                  <div class="col-1"
                       v-if="registerCommentAction">

                  <!--Изменить-->
                      <div @click="registerCommentAction('update', comment, interface.name)"
                           data-bs-toggle="modal" data-bs-target="#modal-comment"
                           style="cursor: pointer">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#0d6efd" class="bi bi-pencil-square" viewBox="0 0 16 16">
                        <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                        <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
                      </svg>
                      </div>

                  <!--Удалить-->
                      <div @click="registerCommentAction('delete', comment, interface.name)"
                           data-bs-toggle="modal" data-bs-target="#modal-comment"
                           style="cursor: pointer">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#dc3545" class="bi bi-x-lg" viewBox="0 0 16 16">
                        <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
                      </svg>
                      </div>
                  </div>

                  <div class="col-11">
                  <!--Пользователь комментария-->
                      <span>@{{comment.user}}</span>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="mx-2" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"></path></svg>
                      <span>{{ formatDatetime(comment.createdTime) }}</span>

                  <!--ТЕКСТ комментария-->
                      <strong style="white-space: break-spaces;" class="d-block text-gray-dark">
                          {{comment.text}}
                      </strong>
                  </div>
              </div>

        </div>
    </OverlayPanel>

  </div>

<!--Создание комментария-->
  <button class="btn btn-fog"
          v-else-if="registerCommentAction"
          @click="registerCommentAction('add', interface.comments, interface.name)"
          data-bs-toggle="modal" data-bs-target="#modal-comment">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#e5e5e5" class="bi bi-chat-right-text" viewBox="0 0 16 16">
        <path d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
        <path d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
      </svg>
  </button>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import OverlayPanel from "primevue/overlaypanel";

import Interface from "../types/interfaces"

export default defineComponent({
  components: {
    OverlayPanel,
  },
  props: {
    registerCommentAction: {
      required: false,
      type: Function,
      default: null
    },
    interface: { required: true, type: Interface }
  },
  methods: {
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