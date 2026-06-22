<template>
    <div class="py-2">
        <div
            class="rounded-4xl border border-gray-200/80 bg-white/85 p-4 shadow-[0_18px_60px_-42px_rgba(15,23,42,0.45)] dark:border-gray-700/80 dark:bg-gray-900/55 sm:p-5"
        >
            <div class="flex flex-col gap-5">
                <div
                    v-if="!collectNew.active"
                    class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
                >
                    <div>
                        <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">
                            Configs
                        </div>
                        <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                            Конфигурации оборудования
                        </div>
                        <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Просмотр, скачивание, удаление и сравнение версий.
                        </div>
                    </div>

                    <div class="flex flex-wrap gap-2">
                        <Button
                            v-if="canCollectConfig"
                            @click="collectConfig"
                            icon="pi pi-plus"
                            label="Собрать новую"
                            severity="success"
                            class="rounded-2xl!"
                        />
                        <Button
                            @click="showDiffDialog = true"
                            icon="pi pi-sliders-h"
                            label="Сравнение"
                            severity="secondary"
                            outlined
                            class="rounded-2xl!"
                        />
                    </div>
                </div>

                <div
                    v-else
                    class="flex items-center justify-center gap-3 rounded-3xl border border-sky-200/80 bg-sky-50/70 px-4 py-5 text-center text-sm font-medium text-sky-800 dark:border-sky-900/60 dark:bg-sky-950/20 dark:text-sky-200"
                >
                    <i class="pi pi-spin pi-spinner text-lg" />
                    <span>Собираем текущую конфигурацию устройства</span>
                </div>

                <Message v-if="collectNew.display" :severity="collectNew.status" class="rounded-3xl">
                    <div class="flex w-full items-center justify-between gap-3">
                        <span>{{ collectNew.text }}</span>
                        <Button
                            @click="collectNew.display = false"
                            icon="pi pi-times"
                            rounded
                            text
                            size="small"
                            severity="contrast"
                        />
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
                                    <div
                                        class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-gray-600 shadow-sm dark:bg-gray-900/80 dark:text-gray-300"
                                        v-html="fileIcon(file.name)"
                                    ></div>
                                    <div class="min-w-0">
                                        <button
                                            class="max-w-full truncate text-left text-base font-semibold text-gray-900 transition group-hover:text-sky-700 dark:text-gray-100 dark:group-hover:text-sky-300"
                                            @click="toggleFileDisplay(file)"
                                        >
                                            {{ file.name }}
                                        </button>
                                        <div
                                            class="mt-1 flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400"
                                        >
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
                                <Button
                                    @click="toggleFileDisplay(file)"
                                    icon="pi pi-eye"
                                    label="Открыть"
                                    severity="contrast"
                                    outlined
                                    class="rounded-2xl!"
                                />
                                <Button
                                    @click="downloadFile(file)"
                                    icon="pi pi-download"
                                    label="Скачать"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                />
                                <Button
                                    v-if="canDeleteConfig"
                                    @click="showDeleteDialog(file)"
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                />
                            </div>
                        </div>
                    </article>
                </div>

                <div
                    v-else
                    class="rounded-3xl border border-dashed border-gray-200/80 bg-gray-50/70 px-4 py-10 text-center text-sm text-gray-500 dark:border-gray-700/80 dark:bg-gray-900/30 dark:text-gray-400"
                >
                    Конфигурации пока не найдены
                </div>
            </div>
        </div>
    </div>

    <Dialog
        v-model:visible="visibleConfigText"
        modal
        maximizable
        class="w-[min(96vw,1400px)]"
        content-class="!p-0"
        @hide="resetConfigSearch"
    >
        <template #header>
            <div class="min-w-0 px-1">
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">
                    Config preview
                </div>
                <div class="mt-1 break-all text-base font-semibold text-gray-900 dark:text-gray-100">
                    {{ selectedFile?.name }}
                </div>
            </div>
        </template>

        <div v-if="selectedFile?.content" class="rounded-b-3xl bg-gray-950 p-4 text-gray-100">
            <div
                class="mb-4 flex flex-col gap-4 rounded-2xl border border-gray-700 bg-gray-900/90 p-3 lg:flex-row lg:items-end"
            >
                <div class="min-w-0 flex-1">
                    <label
                        for="config-regex-search"
                        class="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-gray-400"
                    >
                        Поиск по регулярному выражению
                    </label>
                    <div class="flex flex-wrap items-center gap-2">
                        <InputText
                            id="config-regex-search"
                            v-model="configSearchPattern"
                            class="min-w-[16rem] flex-1 font-mono"
                            placeholder="Например: interface\s+\S+"
                            autocomplete="off"
                            aria-describedby="config-search-help"
                            @keydown.enter.prevent="handleConfigSearchEnter"
                        />
                        <span
                            class="min-w-16 text-center text-sm tabular-nums text-gray-300"
                            aria-live="polite"
                            aria-label="Текущее совпадение и общее количество"
                        >
                            {{ configMatchCounter }}
                        </span>
                        <Button
                            icon="pi pi-chevron-up"
                            severity="secondary"
                            outlined
                            rounded
                            :disabled="configMatches.length === 0"
                            aria-label="Предыдущее совпадение"
                            title="Предыдущее совпадение (Shift+Enter)"
                            @click="showPreviousConfigMatch"
                        />
                        <Button
                            icon="pi pi-chevron-down"
                            severity="secondary"
                            outlined
                            rounded
                            :disabled="configMatches.length === 0"
                            aria-label="Следующее совпадение"
                            title="Следующее совпадение (Enter)"
                            @click="showNextConfigMatch"
                        />
                    </div>
                    <div
                        id="config-search-help"
                        class="mt-2 min-h-5 text-xs"
                        :class="configSearchError ? 'text-red-300' : 'text-gray-500'"
                    >
                        {{
                            configSearchError ||
                            "Поиск без учёта регистра; ^ и $ работают для каждой строки. Ctrl+F переводит фокус в это поле."
                        }}
                    </div>
                </div>

                <div class="w-full lg:w-64">
                    <div class="mb-2 flex items-center justify-between gap-3">
                        <label
                            for="config-font-size"
                            class="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400"
                        >
                            Размер шрифта
                        </label>
                        <output for="config-font-size" class="text-sm tabular-nums text-gray-200">
                            {{ configFontSize }} px
                        </output>
                    </div>
                    <input
                        id="config-font-size"
                        v-model.number="configFontSize"
                        type="range"
                        min="10"
                        max="24"
                        step="1"
                        class="h-2 w-full cursor-pointer accent-sky-500"
                    />
                </div>
            </div>

            <pre
                ref="configText"
                class="config-content max-h-[70vh] overflow-auto whitespace-pre-wrap break-all rounded-2xl bg-black/20 p-3 font-mono"
                :style="{ fontSize: `${configFontSize}px`, lineHeight: 1.6 }"
                v-html="highlightedConfigText"
            ></pre>
        </div>
        <div v-else class="flex justify-center p-10">
            <ProgressSpinner />
        </div>
    </Dialog>

    <Dialog v-model:visible="visibleDeleteDialog" modal header="Удаление конфигурации" class="w-[min(92vw,32rem)]">
        <div class="flex flex-col gap-5">
            <div
                class="flex items-start gap-3 rounded-3xl border border-red-200/80 bg-red-50/70 p-4 dark:border-red-900/70 dark:bg-red-950/20"
            >
                <i class="pi pi-exclamation-triangle mt-0.5 text-red-500" />
                <div class="text-sm text-gray-700 dark:text-gray-200">
                    Вы уверены, что хотите удалить конфигурацию
                    <span v-if="selectedFile" class="font-semibold break-all">{{ selectedFile.name }}</span
                    >?
                </div>
            </div>

            <div class="flex justify-end gap-2">
                <Button
                    icon="pi pi-times"
                    label="Отмена"
                    severity="secondary"
                    outlined
                    class="rounded-2xl!"
                    @click="visibleDeleteDialog = false"
                />
                <Button
                    v-if="selectedFile && canDeleteConfig"
                    @click="deleteFile(selectedFile)"
                    icon="pi pi-trash"
                    severity="danger"
                    label="Удалить"
                    class="rounded-2xl!"
                />
            </div>
        </div>
    </Dialog>

    <Dialog
        v-model:visible="showDiffDialog"
        modal
        header="Сравнение конфигураций"
        maximizable
        class="w-[min(96vw,1500px)]"
    >
        <ConfigFileDiff :config-files="files" :device-name="deviceName" :formatted-config-function="formatConfigFile" />
    </Dialog>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { AxiosResponse } from "axios";
import Dialog from "primevue/dialog";

import ConfigFileDiff from "./ConfigFileDiff.vue";
import api from "@/services/api";
import errorFmt from "@/errorFmt.ts";

interface ConfigFile {
    name: string;
    size: number;
    modTime: string;
    content?: string;
    display?: boolean;
}

interface ConfigMatch {
    start: number;
    end: number;
}

/** Экранирует текст конфигурации перед добавлением безопасной разметки подсветки. */
function escapeHtml(value: string): string {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
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
        deviceName: { required: true, type: String },
        permissions: { required: true, type: Array as PropType<string[]> },
    },
    data() {
        return {
            files: [] as ConfigFile[],
            selectedFile: null as ConfigFile | null,
            collectNew: new CollectNewConfig(),
            showDiffDialog: false,
            visibleConfigText: false,
            visibleDeleteDialog: false,
            configSearchPattern: "",
            configSearchError: "",
            configMatches: [] as ConfigMatch[],
            activeConfigMatch: -1,
            configFontSize: 12,
        };
    },
    computed: {
        configMatchCounter(): string {
            if (!this.configMatches.length) return "0 / 0";
            return `${this.activeConfigMatch + 1} / ${this.configMatches.length}`;
        },
        canCollectConfig(): boolean {
            return this.permissions.includes("check.device_config_collect");
        },
        canDeleteConfig(): boolean {
            return this.permissions.includes("check.device_config_delete");
        },
        highlightedConfigText(): string {
            const content = this.selectedFile?.content ? this.formatConfigFile(this.selectedFile.content) : "";
            if (!this.configMatches.length) return escapeHtml(content);

            let result = "";
            let offset = 0;

            this.configMatches.forEach((match, index) => {
                const matchClass =
                    index === this.activeConfigMatch ? "config-match config-match-active" : "config-match";

                result += escapeHtml(content.slice(offset, match.start));
                result += `<mark class="${matchClass}" data-config-match="${index}">${escapeHtml(
                    content.slice(match.start, match.end)
                )}</mark>`;
                offset = match.end;
            });

            return result + escapeHtml(content.slice(offset));
        },
    },
    watch: {
        configSearchPattern() {
            this.updateConfigSearch();
        },
    },
    mounted() {
        this.getFiles();
        window.addEventListener("keydown", this.handleConfigSearchShortcut);
    },
    beforeUnmount() {
        window.removeEventListener("keydown", this.handleConfigSearchShortcut);
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
            api.delete(`/api/v1/devices/${this.deviceName}/config/${file.name}`).then((value: AxiosResponse) => {
                if (value.status === 204) this.getFiles();
                this.visibleDeleteDialog = false;
            });
        },
        toggleFileDisplay(file: ConfigFile) {
            if (file.size > 1024 * 1024) return;
            this.resetConfigSearch();
            this.selectedFile = file;

            if (!file.content) {
                api.get(`/api/v1/devices/${this.deviceName}/config/${file.name}`, { responseType: "blob" })
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
        updateConfigSearch() {
            this.configSearchError = "";
            this.configMatches = [];
            this.activeConfigMatch = -1;

            const content = this.selectedFile?.content ? this.formatConfigFile(this.selectedFile.content) : "";
            if (!this.configSearchPattern || !content) return;

            let expression: RegExp;
            try {
                expression = new RegExp(this.configSearchPattern, "gim");
            } catch (error) {
                this.configSearchError =
                    error instanceof SyntaxError ? "Некорректное регулярное выражение" : "Не удалось выполнить поиск";
                return;
            }

            let match: RegExpExecArray | null;
            while ((match = expression.exec(content)) !== null) {
                if (!match[0].length) {
                    expression.lastIndex += 1;
                    continue;
                }

                this.configMatches.push({
                    start: match.index,
                    end: match.index + match[0].length,
                });
            }

            if (this.configMatches.length) {
                this.activeConfigMatch = 0;
                this.scrollToActiveConfigMatch();
            }
        },
        resetConfigSearch() {
            this.configSearchPattern = "";
            this.configSearchError = "";
            this.configMatches = [];
            this.activeConfigMatch = -1;
        },
        handleConfigSearchEnter(event: KeyboardEvent) {
            if (event.shiftKey) {
                this.showPreviousConfigMatch();
                return;
            }
            this.showNextConfigMatch();
        },
        showNextConfigMatch() {
            if (!this.configMatches.length) return;
            this.activeConfigMatch = (this.activeConfigMatch + 1) % this.configMatches.length;
            this.scrollToActiveConfigMatch();
        },
        showPreviousConfigMatch() {
            if (!this.configMatches.length) return;
            this.activeConfigMatch =
                (this.activeConfigMatch - 1 + this.configMatches.length) % this.configMatches.length;
            this.scrollToActiveConfigMatch();
        },
        scrollToActiveConfigMatch() {
            this.$nextTick(() => {
                const configText = this.$refs.configText as HTMLElement | undefined;
                const activeMatch = configText?.querySelector<HTMLElement>(
                    `[data-config-match="${this.activeConfigMatch}"]`
                );
                activeMatch?.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
            });
        },
        handleConfigSearchShortcut(event: KeyboardEvent) {
            if (!this.visibleConfigText || (!event.ctrlKey && !event.metaKey) || event.key.toLowerCase() !== "f") {
                return;
            }

            event.preventDefault();
            document.getElementById("config-regex-search")?.focus();
        },
        formatConfigFile(content: string): string {
            return content.replace(/\r\n?/g, "\n");
        },
        downloadFile(file: ConfigFile) {
            api.get(`/api/v1/devices/${this.deviceName}/config/${file.name}`, { responseType: "blob" }).then(
                (response) => {
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
                }
            );
        },
    },
});
</script>

<style scoped>
.config-content :deep(.config-match) {
    border-radius: 0.2rem;
    background: rgb(250 204 21 / 0.55);
    color: inherit;
}

.config-content :deep(.config-match-active) {
    background: rgb(251 146 60);
    color: rgb(17 24 39);
    outline: 2px solid rgb(254 215 170);
    outline-offset: 1px;
}
</style>
