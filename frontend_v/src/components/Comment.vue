<template>
  <div v-if="interface.comments && interface.comments.length" class="inline-flex relative">
    <span
        class="absolute text-white dark:text-gray-950 text-xs px-2 -right-1 -top-0.5 py-0 rounded-full z-10 bg-amber-500 dark:bg-amber-400">{{
        interface.comments?.length
      }}</span>
    <Button
        @click="showCommentsPopup"
        text badgeSeverity="warn"
        severity="secondary"
        class="comment-trigger rounded-2xl!"
        :pt="{
            root: { class: 'hover:shadow-sm hover:border-gray-300/90 dark:hover:border-gray-700/60 bg-white/60 dark:bg-gray-900/25 backdrop-blur-sm hover:bg-white/85 dark:hover:bg-gray-900/45 transition' },
            label: { class: 'hidden' },
          }">
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor"
           class="text-amber-500 dark:text-amber-400" viewBox="0 0 16 16">
        <path
            d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
        <path
            d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
      </svg>
    </Button>

    <Popover
        ref="comment"
        :pt="{
          root: {
            class: 'before:hidden! overflow-hidden rounded-2xl border border-gray-200/80 ' +
                'dark:border-gray-700/60 bg-white/95 shadow-lg dark:bg-gray-900/70 dark:backdrop-blur-xl dark:!ring-1 dark:!ring-white/5',
          },
          content: { class: 'p-0!' },
        }">
      <div class="w-[min(32rem,calc(100vw-2rem))]">
        <div
            class="flex items-start justify-between gap-3 border-b border-gray-200/80 px-4 py-3 dark:border-gray-700/70">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Комментарии интерфейса
            </div>
            <div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400 font-mono">
              {{ interface.name }}
            </div>
          </div>
          <Button
              v-if="allowEdit"
              text
              severity="success"
              icon="pi pi-plus"
              class="rounded-2xl!"
              v-tooltip.bottom="'Добавить комментарий'"
              @click="registerCommentAction('add', null)"/>
        </div>

        <div class="max-h-[min(60vh,28rem)] overflow-y-auto p-3">
          <div class="flex flex-col gap-3">
            <article
                v-for="comment in interface.comments"
                :key="comment.id || `${comment.user}-${comment.createdTime}-${comment.text}`"
                class="group rounded-2xl border border-gray-200/80 bg-gray-50/80 p-3 shadow-sm transition hover:border-indigo-200 hover:bg-white dark:border-gray-700/60 dark:bg-gray-800/45 dark:hover:border-indigo-500/40 dark:hover:bg-gray-800/70">
              <div class="flex items-start gap-3">
                <div
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-linear-to-br from-indigo-500/15 via-sky-500/10 to-transparent text-sm font-semibold text-indigo-600 shadow-sm dark:text-indigo-300">
                  {{ getInitials(comment.user) }}
                </div>

                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      @{{ comment.user }}
                    </div>
                    <div class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                      <i class="pi pi-clock text-[11px]"/>
                      <span>{{ formatDatetime(comment.createdTime) }}</span>
                    </div>
                  </div>

                  <div
                      class="comment-body mt-2 text-sm leading-6 text-gray-700 dark:text-gray-200"
                      v-html="textToHtml(markedText ? markText(comment.text, markedText) : comment.text)"/>
                </div>

                <div v-if="allowEdit"
                     class="flex shrink-0 items-center gap-1 opacity-100 sm:opacity-0 sm:transition group-hover:opacity-100">
                  <Button
                      text
                      severity="info"
                      icon="pi pi-pencil"
                      class="rounded-xl!"
                      v-tooltip.bottom="'Изменить'"
                      @click="registerCommentAction('update', comment)"/>
                  <Button
                      text
                      severity="danger"
                      icon="pi pi-times"
                      class="rounded-xl!"
                      v-tooltip.bottom="'Удалить'"
                      @click="registerCommentAction('delete', comment)"/>
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>
    </Popover>
  </div>

  <Button
      v-else-if="allowEdit"
      text
      severity="secondary"
      class="rounded-2xl!"
      :pt="{
        root: { class: 'hover:shadow-sm hover:border-gray-300/90 dark:hover:border-gray-700/60 bg-white/60 dark:bg-gray-900/25 backdrop-blur-sm hover:bg-white/85 dark:hover:bg-gray-900/45 transition' },
        label: { class: 'hidden' }
      }"
      @click="registerCommentAction('add', null)">
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor"
         class="text-gray-500 dark:text-gray-400" viewBox="0 0 16 16">
      <path
          d="M2 1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h9.586a2 2 0 0 1 1.414.586l2 2V2a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v12.793a.5.5 0 0 1-.854.353l-2.853-2.853a1 1 0 0 0-.707-.293H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12z"/>
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
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              }
          )
    },

    getInitials(username: string): string {
      return (username || "?").trim().slice(0, 2).toUpperCase()
    },
  }
})
</script>

<style scoped>
.comment-body :deep(mark) {
  border-radius: 0.4rem;
  background: color-mix(in srgb, var(--p-primary-300, #93c5fd) 35%, transparent);
  color: inherit;
  padding: 0.05rem 0.25rem;
}

.comment-body :deep(p:last-child) {
  margin-bottom: 0;
}

.comment-body :deep(a) {
  color: rgb(79 70 229);
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.comment-body :deep(code) {
  border-radius: 0.55rem;
  background: rgb(15 23 42 / 0.06);
  padding: 0.15rem 0.45rem;
  font-size: 0.9em;
}

:global(.dark) .comment-body :deep(code) {
  background: rgb(255 255 255 / 0.08);
}
</style>
