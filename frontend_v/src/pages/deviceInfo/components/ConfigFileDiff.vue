<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-col gap-4 rounded-3xl border border-gray-200/80 bg-white/80 p-4 dark:border-gray-700/80 dark:bg-gray-900/55">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Сравнение конфигураций</div>
          <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Выберите две версии и сравните изменения построчно.</div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <div class="inline-flex items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300">
            <ToggleSwitch input-id="showOnlyDiff" v-model="showOnlyDiff" />
            <label for="showOnlyDiff" class="cursor-pointer">Только отличия</label>
          </div>
          <Button @click="compareConfigs" :loading="compareLoading" icon="pi pi-sliders-h" label="Сравнить" class="!rounded-2xl" />
        </div>
      </div>

      <div class="grid gap-3 lg:grid-cols-2">
        <FloatLabel variant="on">
          <Select
              v-model="config2"
              :options="configFiles"
              optionLabel="modTime"
              input-id="old-config"
              fluid
          />
          <label for="old-config">Старая конфигурация</label>
        </FloatLabel>

        <FloatLabel variant="on">
          <Select
              v-model="config1"
              :options="configFiles"
              optionLabel="modTime"
              input-id="new-config"
              fluid
          />
          <label for="new-config">Новая конфигурация</label>
        </FloatLabel>
      </div>
    </div>

    <div v-if="compareError" class="rounded-3xl border border-red-200/80 bg-red-50/70 px-4 py-3 text-sm text-red-700 dark:border-red-900/70 dark:bg-red-950/20 dark:text-red-200">
      {{ compareError }}
    </div>

    <div v-if="rows.length" class="overflow-hidden rounded-3xl border border-gray-200/80 bg-white/80 shadow-[0_18px_55px_-40px_rgba(15,23,42,0.45)] dark:border-gray-700/80 dark:bg-gray-900/55">
      <div class="border-b border-gray-200/80 bg-gradient-to-r from-gray-100/90 to-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:from-gray-800/90 dark:to-gray-900/70">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="min-w-0">
            <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">File Diff</div>
            <div class="mt-1 break-all text-sm font-semibold text-gray-900 dark:text-gray-100">
              {{ config2?.name || "config" }} <span class="text-gray-400">→</span> {{ config1?.name || "config" }}
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2 text-xs font-medium">
            <span class="inline-flex items-center gap-2 rounded-full border border-emerald-200/80 bg-emerald-50 px-3 py-1 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-500/10 dark:text-emerald-200">
              <span class="inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              +{{ addedLinesCount }}
            </span>
            <span class="inline-flex items-center gap-2 rounded-full border border-red-200/80 bg-red-50 px-3 py-1 text-red-700 dark:border-red-900/70 dark:bg-red-500/10 dark:text-red-200">
              <span class="inline-flex h-2 w-2 rounded-full bg-red-500"></span>
              -{{ removedLinesCount }}
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 border-b border-[#d0d7de] bg-[#f6f8fa] text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:border-[#30363d] dark:bg-[#161b22] dark:text-gray-400">
        <div class="flex items-center justify-between px-4 py-3">
          <span>Старая версия</span>
          <span class="font-mono normal-case tracking-normal text-gray-400 dark:text-gray-500">{{ config2?.modTime }}</span>
        </div>
        <div class="flex items-center justify-between border-l border-[#d0d7de] px-4 py-3 dark:border-[#30363d]">
          <span>Новая версия</span>
          <span class="font-mono normal-case tracking-normal text-gray-400 dark:text-gray-500">{{ config1?.modTime }}</span>
        </div>
      </div>

      <div class="max-h-[70vh] overflow-auto bg-[#f6f8fa] dark:bg-[#0d1117]">
        <div
            v-for="row in displayedRows"
            :key="row.id"
            class="grid grid-cols-2 border-b border-[#d0d7de] text-sm last:border-b-0 dark:border-[#30363d]"
        >
          <div :class="['min-w-0 border-r border-[#d0d7de] dark:border-[#30363d]', sideClasses(row.left?.type)]">
            <div class="flex min-w-0 items-stretch">
              <div class="flex w-14 shrink-0 items-start justify-end border-r border-black/5 px-2 py-1.5 font-mono text-[11px] text-gray-400 dark:border-white/5 dark:text-gray-500">
                {{ row.left?.lineNumber ?? "" }}
              </div>
              <div class="flex w-8 shrink-0 items-start justify-center px-1 py-1.5 font-mono text-[12px] font-semibold">
                {{ changeMarker(row.left?.type) }}
              </div>
              <pre class="min-w-0 flex-1 overflow-x-auto px-2 py-1.5 font-mono text-[12px] leading-6">{{ displayLine(row.left?.text) }}</pre>
            </div>
          </div>

          <div :class="['min-w-0', sideClasses(row.right?.type)]">
            <div class="flex min-w-0 items-stretch">
              <div class="flex w-14 shrink-0 items-start justify-end border-r border-black/5 px-2 py-1.5 font-mono text-[11px] text-gray-400 dark:border-white/5 dark:text-gray-500">
                {{ row.right?.lineNumber ?? "" }}
              </div>
              <div class="flex w-8 shrink-0 items-start justify-center px-1 py-1.5 font-mono text-[12px] font-semibold">
                {{ changeMarker(row.right?.type) }}
              </div>
              <pre class="min-w-0 flex-1 overflow-x-auto px-2 py-1.5 font-mono text-[12px] leading-6">{{ displayLine(row.right?.text) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="rounded-3xl border border-dashed border-gray-200/80 bg-gray-50/70 px-4 py-10 text-center text-sm text-gray-500 dark:border-gray-700/80 dark:bg-gray-900/30 dark:text-gray-400">
      Выберите две конфигурации и запустите сравнение.
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import {diffArrays} from "diff";
import api from "@/services/api";

interface ConfigFile {
  name: string
  size: number
  modTime: string
  content?: string
}

interface DiffSide {
  text: string
  lineNumber: number | null
  type: "added" | "removed" | "same"
}

interface DiffRow {
  id: string
  left: DiffSide | null
  right: DiffSide | null
}

export default defineComponent({
  name: "ConfigFileDiff",
  props: {
    configFiles: {required: true, type: Array},
    deviceName: {required: true, type: String},
    formattedConfigFunction: {required: true, type: Function},
  },
  data() {
    return {
      config1: null as ConfigFile | null,
      config2: null as ConfigFile | null,
      rows: [] as DiffRow[],
      showOnlyDiff: false,
      compareLoading: false,
      compareError: "",
    };
  },
  computed: {
    displayedRows(): DiffRow[] {
      if (!this.showOnlyDiff) return this.rows;
      return this.rows.filter((row) => row.left?.type !== "same" || row.right?.type !== "same");
    },
    addedLinesCount(): number {
      return this.rows.reduce((acc, row) => acc + (row.right?.type === "added" ? 1 : 0), 0);
    },
    removedLinesCount(): number {
      return this.rows.reduce((acc, row) => acc + (row.left?.type === "removed" ? 1 : 0), 0);
    }
  },
  methods: {
    async compareConfigs() {
      if (!this.config1 || !this.config2) {
        this.compareError = "Сначала выберите обе конфигурации.";
        return;
      }

      this.compareLoading = true;
      this.compareError = "";

      try {
        const oldContent = await this.getConfigContent(this.config2);
        const newContent = await this.getConfigContent(this.config1);
        const diff = diffArrays(this.tokenizeLines(oldContent), this.tokenizeLines(newContent));

        let oldLine = 1;
        let newLine = 1;
        const rows: DiffRow[] = [];
        let rowIndex = 0;

        for (let i = 0; i < diff.length; i++) {
          const part = diff[i];

          if (part.added) {
            for (const line of this.toLines(part.value)) {
              rows.push({
                id: `row-${rowIndex++}`,
                left: null,
                right: {text: line, lineNumber: newLine++, type: "added"}
              });
            }
            continue;
          }

          if (part.removed) {
            const nextPart = diff[i + 1];
            const removedLines = this.toLines(part.value);

            if (nextPart?.added) {
              const addedLines = this.toLines(nextPart.value);
              const maxLength = Math.max(removedLines.length, addedLines.length);

              for (let index = 0; index < maxLength; index++) {
                rows.push({
                  id: `row-${rowIndex++}`,
                  left: removedLines[index] !== undefined ? {text: removedLines[index], lineNumber: oldLine++, type: "removed"} : null,
                  right: addedLines[index] !== undefined ? {text: addedLines[index], lineNumber: newLine++, type: "added"} : null,
                });
              }
              i++;
              continue;
            }

            for (const line of removedLines) {
              rows.push({
                id: `row-${rowIndex++}`,
                left: {text: line, lineNumber: oldLine++, type: "removed"},
                right: null
              });
            }
            continue;
          }

          for (const line of this.toLines(part.value)) {
            rows.push({
              id: `row-${rowIndex++}`,
              left: {text: line, lineNumber: oldLine++, type: "same"},
              right: {text: line, lineNumber: newLine++, type: "same"}
            });
          }
        }

        this.rows = rows;
      } catch (error) {
        this.compareError = "Не удалось получить данные для сравнения конфигураций.";
      } finally {
        this.compareLoading = false;
      }
    },
    async getConfigContent(config: ConfigFile): Promise<string> {
      if (!config.content) {
        const resp = await api.get(`/api/v1/devices/${this.deviceName}/config/${config.name}`);
        config.content = this.formattedConfigFunction(resp.data);
      }
      return config.content || "";
    },
    tokenizeLines(value: string): string[] {
      const normalized = value.replace(/\r\n?/g, "\n");
      const lines = normalized.split("\n");
      if (normalized.endsWith("\n")) {
        lines.pop();
      }
      return lines;
    },
    toLines(value: unknown): string[] {
      if (Array.isArray(value)) return value.map((line) => String(line));
      return String(value).split("\n");
    },
    changeMarker(type?: "added" | "removed" | "same"): string {
      if (type === "added") return "+";
      if (type === "removed") return "-";
      return "";
    },
    displayLine(text?: string | null): string {
      return text === "" || text == null ? " " : text;
    },
    sideClasses(type?: "added" | "removed" | "same"): string {
      if (type === "added") return "bg-[#dafbe1] text-[#1f2328] dark:bg-[rgba(46,160,67,0.15)] dark:text-[#e6edf3]";
      if (type === "removed") return "bg-[#ffebe9] text-[#1f2328] dark:bg-[rgba(248,81,73,0.15)] dark:text-[#e6edf3]";
      return "bg-transparent text-[#1f2328] dark:text-[#c9d1d9]";
    }
  },
});
</script>
