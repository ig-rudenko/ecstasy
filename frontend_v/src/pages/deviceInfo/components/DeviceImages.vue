<template>
  <Button
      text
      v-tooltip.bottom="'Медиафайлы'"
      class="flex items-center gap-2 !rounded-2xl"
      :severity="items.length ? 'success' : 'secondary'"
      @click="dialogVisible = true"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" :fill="mediaToggleButtonColor" viewBox="0 0 16 16">
      <path d="M4.502 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
      <path
          d="M14.002 13a2 2 0 0 1-2 2h-10a2 2 0 0 1-2-2V5A2 2 0 0 1 2 3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-1.998 2zM14 2H4a1 1 0 0 0-1 1h9.002a2 2 0 0 1 2 2v7A1 1 0 0 0 15 11V3a1 1 0 0 0-1-1zM2.002 4a1 1 0 0 0-1 1v8l2.646-2.354a.5.5 0 0 1 .63-.062l2.66 1.773 3.71-3.71a.5.5 0 0 1 .577-.094l1.777 1.947V5a1 1 0 0 0-1-1h-10z"/>
    </svg>
    <span
        v-if="items.length"
        class="inline-flex min-w-6 items-center justify-center rounded-full bg-emerald-500 px-2 py-0.5 text-xs font-semibold text-white"
    >
      {{ items.length }}
    </span>
  </Button>

  <Dialog
      v-model:visible="dialogVisible"
      modal
      maximizable
      :header="`Медиафайлы оборудования ${deviceName}`"
      class="w-[min(96vw,1400px)]"
      content-class="!p-0"
  >
    <div class="grid h-full min-h-[75vh] gap-0 xl:grid-cols-2">
      <aside
          class="border-b border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-900/60 xl:border-b-0 xl:border-r col-md-2">
        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Файлы</div>
              <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">Выберите файл для просмотра или
                редактирования.
              </div>
            </div>
            <Button @click="setCurrentItem()" label="Добавить" icon="pi pi-plus" size="small" class="!rounded-2xl"/>
          </div>

          <IconField>
            <InputIcon class="pi pi-search"/>
            <InputText v-model.trim="searchQuery" placeholder="Поиск по названию и описанию" fluid/>
          </IconField>

          <div class="flex max-h-[58vh] flex-col gap-2 overflow-auto pr-1">
            <button
                v-for="(item, index) in filteredItems"
                :key="item.id"
                type="button"
                @click="setCurrentItem(item)"
                :class="[
                  'flex w-full flex-col gap-3 rounded-3xl border px-3 py-3 text-left transition',
                  currentItem?.id === item.id
                    ? 'border-sky-400 bg-sky-50/80 shadow-sm dark:border-sky-500 dark:bg-sky-500/10'
                    : 'border-gray-200/80 bg-white/85 hover:border-sky-300 hover:bg-white dark:border-gray-700/80 dark:bg-gray-800/55 dark:hover:border-sky-500 dark:hover:bg-gray-800/80'
                ]"
            >
              <div class="flex items-start gap-3">
                <div
                    class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-gray-100 dark:bg-gray-700/60">
                  <img v-if="item.isImage" :src="item.url" class="h-full w-full object-cover" alt="preview"/>
                  <i v-else class="pi pi-file text-2xl text-gray-500 dark:text-gray-300"/>
                </div>

                <div class="min-w-0 flex-1">
                  <div class="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">{{ item.name }}</div>
                  <div class="mt-1 line-clamp-2 text-xs text-gray-500 dark:text-gray-400">
                    {{ item.description || "Без описания" }}
                  </div>
                  <div class="mt-2 flex items-center gap-2 text-[11px] text-gray-400 dark:text-gray-500">
                    <i class="pi pi-clock"/>
                    <span>{{ parseDateTimeString(item.modTime) }}</span>
                  </div>
                </div>
              </div>

              <div class="flex items-center justify-end gap-2">
                <Button @click.stop="showEditForm(index)" icon="pi pi-pencil" rounded outlined severity="contrast"
                        size="small"/>
                <Button @click.stop="setCurrentItem(item); showDeleteFrom()" icon="pi pi-trash" rounded outlined
                        severity="danger" size="small"/>
              </div>
            </button>

            <div v-if="!filteredItems.length"
                 class="rounded-3xl border border-dashed border-gray-200/80 px-4 py-8 text-center text-sm text-gray-500 dark:border-gray-700/80 dark:text-gray-400">
              Ничего не найдено
            </div>
          </div>
        </div>
      </aside>

      <section class="flex min-h-[60vh] flex-col bg-white/70 p-4 dark:bg-gray-950/20 sm:p-6">
        <template v-if="!currentItem">
          <LoadMedia @loadedmedia="addNewMedia" :device-name="deviceName"/>
        </template>

        <div v-else-if="deleteForm.show"
             class="m-auto flex max-w-lg flex-col gap-4 rounded-3xl border border-red-200/80 bg-red-50/70 p-6 text-center dark:border-red-900/60 dark:bg-red-950/20">
          <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">Удалить файл?</div>
          <div class="text-sm text-gray-600 dark:text-gray-300">Действие необратимо. Файл будет удалён с устройства.
          </div>
          <Message v-if="deleteForm.notification.error" severity="error" class="rounded-2xl">
            {{ deleteForm.notification.error }}
          </Message>
          <div class="flex flex-wrap justify-center gap-2">
            <Button icon="pi pi-times" @click="deleteForm.show = false" label="Отмена" severity="secondary" outlined
                    class="!rounded-2xl"/>
            <Button icon="pi pi-trash" @click="deleteCurrentItem" label="Удалить" severity="danger"
                    class="!rounded-2xl"/>
          </div>
        </div>

        <EditMedia
            v-else-if="editForm.show"
            :item="items[editForm.itemIndex]"
            :device-name="deviceName"
            @close="editForm.show = false; currentItem = items[editForm.itemIndex]"
            @reloadedmedia="updateMedia"
        />

        <div v-else class="flex h-full flex-col gap-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ currentItem.name }}</div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {{ currentItem.description || "Описание не указано" }}
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <Button @click="showEditForm(currentItemIndex)" icon="pi pi-pencil" label="Редактировать"
                      severity="contrast" outlined class="!rounded-2xl"/>
              <Button @click="showDeleteFrom" icon="pi pi-trash" label="Удалить" severity="danger" outlined
                      class="!rounded-2xl"/>
            </div>
          </div>

          <a
              v-if="currentItem.isImage"
              :href="currentItem.url"
              target="_blank"
              class="flex min-h-[24rem] flex-1 items-center justify-center overflow-hidden rounded-3xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/40"
          >
            <img class="max-h-[60vh] max-w-full rounded-2xl object-contain" :src="currentItem.url" alt="image"/>
          </a>

          <div
              v-else
              class="flex min-h-[24rem] flex-1 flex-col items-center justify-center gap-4 rounded-3xl border border-gray-200/80 bg-gray-50/80 p-6 text-center dark:border-gray-700/80 dark:bg-gray-800/40"
          >
            <i class="pi pi-file text-7xl text-gray-400 dark:text-gray-500"/>
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ currentItem.name }}</div>
            <Button
                v-if="!downloadInProgress"
                @click="downloadFile(currentItem.url)"
                icon="pi pi-download"
                label="Скачать"
                class="!rounded-2xl"
            />
            <ProgressSpinner v-else style="width: 56px; height: 56px" strokeWidth="6" fill="transparent"
                             animationDuration=".5s" aria-label="downloading"/>
          </div>
        </div>
      </section>
    </div>
  </Dialog>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import LoadMedia from "./LoadMedia.vue";
import EditMedia from "./EditMedia.vue";

import api from "@/services/api";
import errorFmt from "@/errorFmt";
import {downloadFile} from "@/services/files";
import {errorToast} from "@/services/my.toast";
import {getProtectedImage} from "@/helpers/images";
import {MediaFileInfo, newMediaFileInfoList} from "../files";

export default defineComponent({
  components: {EditMedia, LoadMedia},
  props: {
    deviceName: {required: true, type: String}
  },
  data() {
    return {
      dialogVisible: false,
      searchQuery: "",
      items: [] as MediaFileInfo[],
      currentItem: null as MediaFileInfo | null,
      editForm: {
        show: false,
        itemIndex: 0,
      },
      downloadInProgress: false,
      deleteForm: {
        show: false,
        notification: {
          error: "",
        }
      }
    };
  },
  mounted() {
    this.loadMedia();
  },
  computed: {
    mediaToggleButtonColor(): string {
      if (this.items.length) {
        return "#198754"
      }
      return "currentColor"
    },
    filteredItems(): MediaFileInfo[] {
      const query = this.searchQuery.trim().toLowerCase();
      if (!query) return this.items;
      return this.items.filter((item) =>
          item.name.toLowerCase().includes(query) ||
          item.description.toLowerCase().includes(query)
      );
    },
    currentItemIndex(): number {
      return this.currentItem ? this.items.findIndex((item) => item.id === this.currentItem?.id) : -1;
    }
  },
  methods: {
    downloadFile(url: string) {
      this.downloadInProgress = true;
      downloadFile(url, () => this.downloadInProgress = false);
    },
    setCurrentItem(item?: MediaFileInfo): void {
      this.deleteForm.show = false;
      this.editForm.show = false;
      this.deleteForm.notification.error = "";
      this.currentItem = item ?? null;
    },
    showDeleteFrom(): void {
      this.editForm.show = false;
      this.deleteForm.show = true;
    },
    showEditForm(itemIndex: number): void {
      if (itemIndex < 0) return;
      this.deleteForm.show = false;
      this.editForm.show = true;
      this.editForm.itemIndex = itemIndex;
      this.currentItem = this.items[itemIndex];
    },
    async loadMedia() {
      try {
        const resp = await api.get(`/api/v1/devices/${this.deviceName}/media`);
        this.items = await newMediaFileInfoList(resp.data);
        if (this.items.length) {
          this.setCurrentItem(this.items[0]);
        }
      } catch (error: any) {
        errorToast("Не удалось загрузить список медиафайлов", errorFmt(error));
      }
    },
    async addNewMedia(media: MediaFileInfo) {
      if (media.isImage) media.url = await getProtectedImage(media.url);
      this.items.unshift(media);
      this.setCurrentItem(media);
    },
    async updateMedia(newMedia: MediaFileInfo) {
      if (newMedia.isImage) newMedia.url = await getProtectedImage(newMedia.url);
      this.items.splice(this.editForm.itemIndex, 1, newMedia);
      this.currentItem = newMedia;
      this.editForm.show = false;
    },
    parseDateTimeString(str: string): string {
      const date = new Date(str);
      if (isNaN(date.getTime())) {
        return "Неверная дата";
      }

      const hours = String(date.getHours()).padStart(2, "0");
      const minutes = String(date.getMinutes()).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const year = date.getFullYear();

      return `${hours}:${minutes} - ${day}.${month}.${year}`;
    },
    deleteCurrentItem() {
      if (!this.currentItem) return;
      api.delete(`/api/v1/devices/${this.deviceName}/media/${this.currentItem.id}`)
          .then(() => {
            this.removeElement(this.items, this.currentItem);
            this.currentItem = this.items[0] ?? null;
            this.deleteForm.show = false;
          })
          .catch((reason: any) => {
            this.deleteForm.notification.error = reason.response?.data?.detail || reason.response?.data || "Не удалось удалить файл";
          });
    },
    removeElement(array: Array<MediaFileInfo>, element: MediaFileInfo | null) {
      if (!element) return array;
      const index = array.indexOf(element);
      if (index !== -1) {
        array.splice(index, 1);
      }
      return array;
    }
  }
});
</script>
