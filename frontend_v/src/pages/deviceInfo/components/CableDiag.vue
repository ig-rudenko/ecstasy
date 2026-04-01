<script lang="ts">
import {defineComponent} from "vue";

import api from "@/services/api";
import errorFmt from "@/errorFmt";

interface SFPDiagValue {
  Current: number | string | null
  "Low Warning": number | string | null
  "High Warning": number | string | null
  Status?: string | null
}

interface SFPDiagInfo {
  [key: string]: SFPDiagValue
}

interface PairInfo {
  status: string
  len: string | number
}

interface CopperPairCard extends PairInfo {
  key: string
  label: string
  align: "left" | "right"
}

interface DiagInfo {
  len: string
  status: string
  pair1?: PairInfo
  pair2?: PairInfo
  sfp?: SFPDiagInfo
}

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    port: {required: true, type: String},
  },
  data() {
    return {
      diagInfo: null as DiagInfo | null,
      diagnosticsStarted: false,
      error: "",
    };
  },
  computed: {
    isCopperPort(): boolean {
      return Boolean(this.diagInfo?.len && !this.diagInfo?.sfp);
    },
    sfpData() {
      if (!this.diagInfo?.sfp) {
        return [];
      }

      return Object.entries(this.diagInfo.sfp).map(([parameter, value]) => ({
        parameter,
        current: value.Current ?? "-",
        lowWarning: value["Low Warning"] ?? "-",
        highWarning: value["High Warning"] ?? "-",
        status: value.Status ?? "-",
      }));
    },
    copperPairs() {
      if (!this.diagInfo) {
        return [];
      }

      const pairs: CopperPairCard[] = [];

      if (this.diagInfo.pair1) {
        pairs.push({
            key: "pair1",
            label: "Пара 1",
            align: "left" as const,
            ...this.diagInfo.pair1,
          });
      }

      if (this.diagInfo.pair2) {
        pairs.push({
            key: "pair2",
            label: "Пара 2",
            align: "right" as const,
            ...this.diagInfo.pair2,
          });
      }

      return pairs;
    },
    summaryCards() {
      if (!this.diagInfo || this.diagInfo.sfp) {
        return [];
      }

      return [
        {
          label: "Статус линии",
          value: this.diagInfo.status || "-",
          dotClass: this.statusDotClass(this.diagInfo.status),
          toneClass: this.statusToneClass(this.diagInfo.status),
        },
        {
          label: "Длина кабеля",
          value: this.diagInfo.len || "-",
          dotClass: "bg-slate-400 dark:bg-slate-500",
          toneClass: "border-slate-200/80 bg-slate-50/80 text-slate-800 dark:border-slate-700/80 dark:bg-slate-800/70 dark:text-slate-100",
        },
      ];
    },
  },
  methods: {
    async startDiagnostic() {
      this.diagInfo = null;
      this.diagnosticsStarted = true;
      this.error = "";

      try {
        const response = await api.get(
          `/api/v1/devices/${this.deviceName}/cable-diag?port=${this.port}`
        );
        this.diagInfo = response.data;
      } catch (error: any) {
        console.error(error);
        this.error = errorFmt(error);
      } finally {
        this.diagnosticsStarted = false;
      }
    },
    statusColor(status: string) {
      const colors: Record<string, string> = {
        Up: "#39d286",
        Down: "#ff4b4d",
        Empty: "#19b7f3",
        Open: "#ff9100",
        Short: "#d80000",
      };
      return colors[status] || "#64748b";
    },
    statusDotClass(status: string) {
      const colors: Record<string, string> = {
        Up: "bg-emerald-500 dark:bg-emerald-400",
        Down: "bg-rose-500 dark:bg-rose-400",
        Empty: "bg-sky-500 dark:bg-sky-400",
        Open: "bg-amber-500 dark:bg-amber-400",
        Short: "bg-red-600 dark:bg-red-500",
      };
      return colors[status] || "bg-slate-400 dark:bg-slate-500";
    },
    statusToneClass(status: string) {
      const tones: Record<string, string> = {
        Up: "border-emerald-200/80 bg-emerald-50/80 text-emerald-900 dark:border-emerald-900/70 dark:bg-emerald-500/10 dark:text-emerald-100",
        Down: "border-rose-200/80 bg-rose-50/80 text-rose-900 dark:border-rose-900/70 dark:bg-rose-500/10 dark:text-rose-100",
        Empty: "border-sky-200/80 bg-sky-50/80 text-sky-900 dark:border-sky-900/70 dark:bg-sky-500/10 dark:text-sky-100",
        Open: "border-amber-200/80 bg-amber-50/80 text-amber-900 dark:border-amber-900/70 dark:bg-amber-500/10 dark:text-amber-100",
        Short: "border-red-200/80 bg-red-50/80 text-red-900 dark:border-red-900/70 dark:bg-red-500/10 dark:text-red-100",
      };
      return tones[status] || "border-slate-200/80 bg-slate-50/80 text-slate-800 dark:border-slate-700/80 dark:bg-slate-800/70 dark:text-slate-100";
    },
    pairImage(status: string, align: "left" | "right") {
      return `/img/rj45-status-${String(status).toLowerCase()}-${align}.png`;
    },
    pairStatusLabel(status: string) {
      return status || "Unknown";
    },
  },
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-3 rounded-[1.5rem] border border-sky-200/80 bg-white/75 p-4 shadow-[0_18px_50px_-40px_rgba(14,165,233,0.45)] dark:border-sky-900/70 dark:bg-slate-950/45 sm:flex-row sm:items-center sm:justify-between">
      <div class="min-w-0">
        <div class="text-xs font-semibold uppercase tracking-[0.22em] text-sky-700 dark:text-sky-300">Cable Diagnostics</div>
        <div class="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Проверка состояния линии и оптических параметров интерфейса прямо из карточки порта.
        </div>
      </div>

      <Button
        @click="startDiagnostic"
        icon="pi pi-play"
        :loading="diagnosticsStarted"
        :label="diagnosticsStarted ? 'Диагностика выполняется' : 'Запустить диагностику'"
        class="!rounded-2xl !px-4 !py-2.5"
      />
    </div>

    <Message v-if="error" severity="error" class="!rounded-2xl">
      {{ error }}
    </Message>

    <div v-if="diagnosticsStarted" class="flex items-center justify-center rounded-[1.5rem] border border-dashed border-sky-200/80 bg-sky-50/60 px-4 py-10 dark:border-sky-900/70 dark:bg-sky-950/20">
      <div class="flex flex-col items-center gap-3 text-center">
        <ProgressSpinner class="h-11 w-11" strokeWidth="5" />
        <div class="text-sm font-medium text-slate-700 dark:text-slate-200">Собираем данные диагностики</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">Обычно это занимает несколько секунд.</div>
      </div>
    </div>

    <div v-else-if="diagInfo" class="flex flex-col gap-4">
      <section
        v-if="isCopperPort"
        class="grid gap-4 xl:grid-cols-5"
      >
        <div class="overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-white/80 xl:col-span-5 dark:border-slate-700/80 dark:bg-slate-950/35">
          <div class="border-b border-slate-200/80 px-4 py-3 dark:border-slate-700/80">
            <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">Схема кабеля</div>
            <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">Статус пар и ориентировочная длина обрыва или замыкания.</div>
          </div>

          <div class="grid gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(16rem,18rem)]">
            <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 dark:border-slate-700/80 dark:bg-slate-900/70">
              <div class="flex h-full items-center justify-center">
                <img src="/img/rj45-back.jpg" class="max-h-72 w-full max-w-xs rounded-2xl object-contain dark:opacity-80" alt="RJ45 background" />
              </div>
            </div>

            <div class="grid gap-3">
              <div
                v-for="card in summaryCards"
                :key="card.label"
                :class="['rounded-[1.25rem] border px-4 py-3', card.toneClass]"
              >
                <div class="text-[11px] font-semibold uppercase tracking-[0.2em] opacity-80">{{ card.label }}</div>
                <div class="mt-2 flex items-center gap-2 text-sm font-semibold">
                  <span :class="['h-2.5 w-2.5 rounded-full', card.dotClass]"></span>
                  <span>{{ card.value }}</span>
                </div>
              </div>

              <div
                v-for="pair in copperPairs"
                :key="pair.key"
                :class="['rounded-[1.25rem] border px-4 py-4', statusToneClass(pair.status)]"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="text-[11px] font-semibold uppercase tracking-[0.2em] opacity-80">{{ pair.label }}</div>
                    <div class="mt-2 text-base font-semibold">{{ pairStatusLabel(pair.status) }}</div>
                    <div class="mt-1 text-sm opacity-80">Длина: <span class="font-mono">{{ pair.len }} м</span></div>
                  </div>

                  <div class="shrink-0 rounded-2xl bg-white/70 p-2 dark:bg-slate-950/40">
                    <img
                      :src="pairImage(pair.status, pair.align)"
                      :alt="`${pair.label} ${pair.status}`"
                      class="h-14 w-auto object-contain"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        v-if="diagInfo.sfp"
        class="overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-white/80 dark:border-slate-700/80 dark:bg-slate-950/35"
      >
        <div class="border-b border-slate-200/80 px-4 py-3 dark:border-slate-700/80">
          <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">SFP diagnostics</div>
          <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">Текущие значения модуля и предупреждающие пороги.</div>
        </div>

        <DataTable
          :value="sfpData"
          :rows="10"
          paginator
          class="text-sm"
          :pt="{
            table: { class: 'min-w-full' },
            headerRow: { class: 'bg-slate-50/80 dark:bg-slate-900/80' },
            column: {
              headerCell: { class: 'border-b border-slate-200/80 bg-slate-50/80 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:border-slate-700/80 dark:bg-slate-900/80 dark:text-slate-400' },
              bodyCell: { class: 'border-b border-slate-200/70 px-4 py-3 align-top text-slate-700 dark:border-slate-800/80 dark:text-slate-200' }
            },
            pcPaginator: { root: { class: 'border-t border-slate-200/80 bg-white/70 px-2 py-2 dark:border-slate-700/80 dark:bg-slate-900/60' } }
          }"
        >
          <Column field="parameter" header="Параметр">
            <template #body="{ data }">
              <span class="font-medium text-slate-900 dark:text-slate-100">{{ data.parameter }}</span>
            </template>
          </Column>

          <Column field="current" header="Текущее значение">
            <template #body="{ data }">
              <span class="font-mono">{{ data.current }}</span>
            </template>
          </Column>

          <Column field="lowWarning" header="Low warning">
            <template #body="{ data }">
              <span class="font-mono">{{ data.lowWarning }}</span>
            </template>
          </Column>

          <Column field="highWarning" header="High warning">
            <template #body="{ data }">
              <span class="font-mono">{{ data.highWarning }}</span>
            </template>
          </Column>

          <Column field="status" header="Статус">
            <template #body="{ data }">
              <span
                class="inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold"
                :class="statusToneClass(data.status)"
              >
                {{ data.status }}
              </span>
            </template>
          </Column>
        </DataTable>
      </section>
    </div>

    <div
      v-else
      class="rounded-[1.5rem] border border-dashed border-slate-200/80 bg-white/60 px-4 py-10 text-center dark:border-slate-700/80 dark:bg-slate-950/20"
    >
      <div class="mx-auto max-w-md">
        <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">Диагностика ещё не запускалась</div>
        <div class="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Нажмите кнопку выше, чтобы получить состояние линии или диагностические показатели SFP-модуля.
        </div>
      </div>
    </div>
  </div>
</template>
