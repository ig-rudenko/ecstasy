<template>
  <div class="py-2">
    <div class="rounded-[2rem] border border-gray-200/80 bg-white/85 p-4 shadow-[0_18px_60px_-42px_rgba(15,23,42,0.45)] dark:border-gray-700/80 dark:bg-gray-900/55 sm:p-5">
      <div class="flex flex-col gap-5">
        <div v-if="!collectNew.active" class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Configs</div>
            <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">Конфигурации оборудования</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Просмотр, скачивание, удаление и сравнение версий.</div>
          </div>

          <div class="flex flex-wrap gap-2">
            <Button @click="collectConfig" icon="pi pi-plus" label="Собрать новую" severity="success" class="!rounded-2xl" />
            <Button @click="showDiffDialog = true" icon="pi pi-sliders-h" label="Сравнение" severity="secondary" outlined class="!rounded-2xl" />
          </div>
        </div>

        <div v-else class="flex items-center justify-center gap-3 rounded-3xl border border-sky-200/80 bg-sky-50/70 px-4 py-5 text-center text-sm font-medium text-sky-800 dark:border-sky-900/60 dark:bg-sky-950/20 dark:text-sky-200">
          <i class="pi pi-spin pi-spinner text-lg" />
          <span>Собираем текущую конфигурацию устройства</span>
        </div>

        <Message v-if="collectNew.display" :severity="collectNew.status" class="rounded-3xl">
          <div class="flex w-full items-center justify-between gap-3">
            <span>{{ collectNew.text }}</span>
            <Button @click="collectNew.display = false" icon="pi pi-times" rounded text size="small" severity="contrast" />
          </div>
        </Message>

        <div v-if="files.length" class="grid gap-3">
          <article
              v-for="file in files"
              :key="file.name"
              class="group rounded-3xl border border-gray-200/80 bg-gray-50/70 p-4 transition hover:border-sky-300 hover:bg-white dark:border-gray-700/80 dark:bg-gray-950/20 dark:hover:border-sky-500 dark:hover:bg-gray-900/70"
          >
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-3">
                  <div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-gray-600 shadow-sm dark:bg-gray-900/80 dark:text-gray-300" v-html="fileIcon(file.name)"></div>
                  <div class="min-w-0">
                    <button class="max-w-full truncate text-left text-base font-semibold text-gray-900 transition group-hover:text-sky-700 dark:text-gray-100 dark:group-hover:text-sky-300" @click="toggleFileDisplay(file)">
                      {{ file.name }}
                    </button>
                    <div class="mt-1 flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                      <span>{{ formatBytes(file.size) }}</span>
                      <span class="h-1 w-1 rounded-full bg-gray-300 dark:bg-gray-600"></span>
                      <span class="inline-flex items-center gap-2">
                        <i class="pi pi-clock" />
                        <span>{{ file.modTime }}</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <Button @click="toggleFileDisplay(file)" icon="pi pi-eye" label="Открыть" severity="contrast" outlined class="!rounded-2xl" />
                <Button @click="downloadFile(file)" icon="pi pi-download" label="Скачать" severity="secondary" outlined class="!rounded-2xl" />
                <Button @click="showDeleteDialog(file)" icon="pi pi-trash" label="Удалить" severity="danger" outlined class="!rounded-2xl" />
              </div>
            </div>
          </article>
        </div>

        <div v-else class="rounded-3xl border border-dashed border-gray-200/80 bg-gray-50/70 px-4 py-10 text-center text-sm text-gray-500 dark:border-gray-700/80 dark:bg-gray-900/30 dark:text-gray-400">
          Конфигурации пока не найдены
        </div>
      </div>
    </div>
  </div>

  <Dialog v-model:visible="visibleConfigText" modal maximizable class="w-[min(96vw,1400px)]" content-class="!p-0">
    <template #header>
      <div class="min-w-0 px-1">
        <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Config preview</div>
        <div class="mt-1 break-all text-base font-semibold text-gray-900 dark:text-gray-100">{{ selectedFile?.name }}</div>
      </div>
    </template>

    <div v-if="selectedFile?.content" class="rounded-b-3xl bg-gray-950 px-4 py-4 text-gray-100">
      <pre class="overflow-auto whitespace-pre-wrap break-all font-mono text-[12px] leading-6">{{ selectedFile.content }}</pre>
    </div>
    <div v-else class="flex justify-center p-10">
      <ProgressSpinner />
    </div>
  </Dialog>

  <Dialog v-model:visible="visibleDeleteDialog" modal header="Удаление конфигурации" class="w-[min(92vw,32rem)]">
    <div class="flex flex-col gap-5">
      <div class="flex items-start gap-3 rounded-3xl border border-red-200/80 bg-red-50/70 p-4 dark:border-red-900/70 dark:bg-red-950/20">
        <i class="pi pi-exclamation-triangle mt-0.5 text-red-500" />
        <div class="text-sm text-gray-700 dark:text-gray-200">
          Вы уверены, что хотите удалить конфигурацию
          <span v-if="selectedFile" class="font-semibold break-all">{{ selectedFile.name }}</span>?
        </div>
      </div>

      <div class="flex justify-end gap-2">
        <Button icon="pi pi-times" label="Отмена" severity="secondary" outlined class="!rounded-2xl" @click="visibleDeleteDialog = false" />
        <Button v-if="selectedFile" @click="deleteFile(selectedFile)" icon="pi pi-trash" severity="danger" label="Удалить" class="!rounded-2xl" />
      </div>
    </div>
  </Dialog>

  <Dialog v-model:visible="showDiffDialog" modal header="Сравнение конфигураций" maximizable class="w-[min(96vw,1500px)]">
    <ConfigFileDiff
        :config-files="files"
        :device-name="deviceName"
        :formatted-config-function="formatConfigFile"
    />
  </Dialog>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import {AxiosResponse} from "axios";
import Dialog from "primevue/dialog";

import ConfigFileDiff from "./ConfigFileDiff.vue";
import api from "@/services/api";
import errorFmt from "@/errorFmt.ts";

interface ConfigFile {
  name: string
  size: number
  modTime: string
  content?: string
  display?: boolean
}

class CollectNewConfig {
  constructor(
      public active: boolean = false,
      public status: "success" | "error" = "success",
      public display: boolean = false,
      public text: string = ""
  ) {}

  setFree() {
    this.display = true;
    this.active = false;
  }
}

export default defineComponent({
  name: "ConfigFiles",
  components: {
    Dialog,
    ConfigFileDiff,
  },
  props: {
    deviceName: {required: true, type: String},
  },
  data() {
    return {
      files: [] as ConfigFile[],
      selectedFile: null as ConfigFile | null,
      collectNew: new CollectNewConfig(),
      showDiffDialog: false,
      visibleConfigText: false,
      visibleDeleteDialog: false,
    };
  },
  mounted() {
    this.getFiles();
  },
  methods: {
    fileIcon(fileName: string): string {
      if (fileName && fileName.endsWith(".txt")) {
        return `<i class="pi pi-file text-xl"></i>`;
      }
      if (fileName && fileName.endsWith(".zip")) {
        return `<i class="pi pi-file-export text-xl"></i>`;
      }
      return `<i class="pi pi-file-o text-xl"></i>`;
    },
    formatBytes(bytes: number): string {
      const marker = 1024;
      const decimal = 1;
      const kiloBytes = marker;
      const megaBytes = kiloBytes * marker;

      if (bytes < kiloBytes) return `${bytes} Б`;
      if (bytes < megaBytes) return `${(bytes / kiloBytes).toFixed(decimal)} КБ`;
      if (bytes < marker * megaBytes) return `${(bytes / megaBytes).toFixed(decimal)} МБ`;
      return "1+ ГБ";
    },
    getFiles() {
      api.get(`/api/v1/devices/${this.deviceName}/configs`)
          .then((value: AxiosResponse<ConfigFile[]>) => {
            this.files = value.data;
          })
          .catch((reason) => {
            console.log(reason);
          });
    },
    collectConfig() {
      if (this.collectNew.active) return;

      this.collectNew.active = true;
      api.post(`/api/v1/devices/${this.deviceName}/collect-config`)
          .then(
              (value: AxiosResponse) => {
                this.getFiles();
                this.collectNew.status = "success";
                this.collectNew.text = value.data.status;
                this.collectNew.setFree();
              },
              (reason: any) => {
                this.collectNew.status = "error";
                this.collectNew.text = errorFmt(reason);
                this.collectNew.setFree();
              }
          )
          .catch(() => {
            this.collectNew.status = "error";
            this.collectNew.text = "Ошибка во время сбора новой конфигурации";
            this.collectNew.setFree();
          });
    },
    showDeleteDialog(file: ConfigFile) {
      this.selectedFile = file;
      this.visibleDeleteDialog = true;
    },
    deleteFile(file: ConfigFile) {
      api.delete(`/api/v1/devices/${this.deviceName}/config/${file.name}`)
          .then((value: AxiosResponse) => {
            if (value.status === 204) this.getFiles();
            this.visibleDeleteDialog = false;
          });
    },
    toggleFileDisplay(file: ConfigFile) {
      if (file.size > 1024 * 1024) return;
      this.selectedFile = file;

      if (!file.content) {
        api.get(`/api/v1/devices/${this.deviceName}/config/${file.name}`, {responseType: "blob"})
            .then((value: AxiosResponse<Blob>) => value.data.text())
            .then((value) => {
              if (!value.length) return;
              file.content = value;
              this.visibleConfigText = true;
            });
      }
      this.visibleConfigText = true;
      file.display = !file.display;
    },
    formatConfigFile(content: string): string {
      return content.replace(/\r\n?/g, "\n");
    },
    downloadFile(file: ConfigFile) {
      api.get(`/api/v1/devices/${this.deviceName}/config/${file.name}`, {responseType: "blob"})
          .then((response) => {
            const href = URL.createObjectURL(response.data);
            const link = document.createElement("a");
            link.href = href;

            let filename = file.name;
            if (!filename.endsWith(".txt")) filename = `${filename}.txt`;

            link.setAttribute("download", filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(href);
          });
    }
  }
});
</script>
