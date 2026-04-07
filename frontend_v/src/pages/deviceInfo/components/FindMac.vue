<template>
  <Dialog
      v-model:visible="macSearch.dialogVisible"
      modal
      class="w-[min(96vw,1100px)]"
      content-class="!p-0">

    <template #header>
      <div class="flex items-center gap-3">
        <div
            class="flex h-11 w-11 items-center justify-center rounded-2xl bg-linear-to-br from-indigo-500/15 via-sky-500/10 to-transparent text-indigo-600 shadow-sm dark:text-indigo-300">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-ethernet" viewBox="0 0 16 16">
              <path d="M14 13.5v-7a.5.5 0 0 0-.5-.5H12V4.5a.5.5 0 0 0-.5-.5h-1v-.5A.5.5 0 0 0 10 3H6a.5.5 0 0 0-.5.5V4h-1a.5.5 0 0 0-.5.5V6H2.5a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5M3.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25m2 0h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25m1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25zM9.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25m1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25z"/>
              <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zM1 2a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1z"/>
            </svg>
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Поиск MAC-адреса</div>
          <div class="mt-0.5 truncate font-mono text-sm text-gray-500 dark:text-gray-400">
            {{ macSearch.lastMac || "..." }}
          </div>
        </div>
      </div>
    </template>

    <div class="flex flex-col gap-5 bg-gray-50/60 p-4 dark:bg-gray-950/30 sm:p-6">
      <section class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Информация о MAC</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Производитель и нормализованный адрес по последнему запросу.
            </div>
          </div>

          <div v-if="macSearch.lastMac" class="inline-flex w-fit items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50 px-3 py-1.5 font-mono text-sm text-indigo-900 dark:border-indigo-900/70 dark:bg-indigo-500/15 dark:text-indigo-100">
            <span class="inline-flex h-2.5 w-2.5 rounded-full bg-indigo-500"></span>
            {{ macSearch.lastMac }}
          </div>
        </div>

        <div v-if="macSearch.lastSearch" class="mt-4 grid gap-3 md:grid-cols-2">
          <article class="rounded-2xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/60">
            <div class="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">Vendor</div>
            <div class="mt-2 text-base font-semibold text-gray-900 dark:text-gray-100">
              {{ macSearch.lastSearch.vendor }}
            </div>
          </article>

          <article class="rounded-2xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/60">
            <div class="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">Address</div>
            <div class="mt-2 break-all font-mono text-sm text-gray-700 dark:text-gray-200">
              {{ macSearch.lastSearch.address }}
            </div>
          </article>
        </div>

        <div v-else class="mt-4 flex justify-center rounded-2xl border border-dashed border-gray-200/80 bg-white/70 p-8 dark:border-gray-700/80 dark:bg-gray-950/25">
          <ProgressSpinner />
        </div>
      </section>

      <section class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Результаты в сети</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Найденные устройства, VLAN и порты, связанные с этим MAC.
            </div>
          </div>

          <div v-if="zabbixLinks.length" class="flex flex-wrap gap-2">
            <a
                v-for="zbx in zabbixLinks"
                :key="zbx.hostid"
                :href="`${macSearch.lastMacDetail?.zabbix_url}/hostinventories.php?hostid=${zbx.hostid}`"
                target="_blank"
                rel="noopener noreferrer">
              <Button
                  severity="danger"
                  size="small"
                  :label="zbx.name"
                  class="rounded-full! text-xs!" />
            </a>
          </div>
        </div>

        <div v-if="macSearch.lastMacDetail" class="mt-4 flex flex-col gap-4">
          <div
              v-if="!macSearch.lastMacDetail.info?.length"
              class="rounded-2xl border border-dashed border-gray-200/80 bg-white/70 px-4 py-10 text-center text-sm text-gray-500 dark:border-gray-700/80 dark:bg-gray-950/25 dark:text-gray-400">
            Совпадений в сетевой информации не найдено.
          </div>

          <article
              v-for="info in macSearch.lastMacDetail.info"
              :key="info.device.name"
              class="overflow-hidden rounded-3xl border border-gray-200/80 bg-white/70 dark:border-gray-700/80 dark:bg-gray-950/25">
            <div class="flex flex-col gap-3 border-b border-gray-200/80 bg-gray-50/80 px-4 py-4 dark:border-gray-700/80 dark:bg-gray-900/70 lg:flex-row lg:items-center lg:justify-between">
              <div class="flex min-w-0 items-center gap-3">
                <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300">
                  <i class="pi pi-server text-base"/>
                </div>
                <div class="min-w-0">
                  <div class="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {{ info.device.name }}
                  </div>
                  <div class="mt-1 font-mono text-xs text-gray-500 dark:text-gray-400">
                    {{ info.device.ip }}
                  </div>
                </div>
              </div>

              <div class="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-200/80 bg-emerald-50 px-3 py-1.5 text-sm text-emerald-800 dark:border-emerald-900/70 dark:bg-emerald-500/10 dark:text-emerald-200">
                <span class="inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                {{ info.results.length }} {{ formatResultsCount(info.results.length) }}
              </div>
            </div>

            <div class="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
              <article
                  v-for="res in info.results"
                  :key="`${info.device.name}-${res.ip}-${res.mac}-${res.port}-${res.vlan}`"
                  class="rounded-2xl border border-gray-200/80 bg-gray-50/80 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-800/60">
                <div class="flex items-start justify-between gap-3">
                  <div class="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">
                    Найдено совпадение
                  </div>
                  <span class="w-full text-center rounded-full bg-indigo-600 px-2.5 py-1 text-[16px] font-mono font-semibold text-white dark:bg-indigo-400 dark:text-slate-950">
                    VLAN {{ res.vlan }}
                  </span>
                </div>

                <dl class="mt-4 flex flex-col gap-3">
                  <div>
                    <dt class="text-[11px] uppercase tracking-[0.18em] text-gray-400 dark:text-gray-500">IP</dt>
                    <dd class="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">{{ res.ip }}</dd>
                  </div>

                  <div>
                    <dt class="text-[11px] uppercase tracking-[0.18em] text-gray-400 dark:text-gray-500">MAC</dt>
                    <dd class="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100 break-all">{{ res.mac }}</dd>
                  </div>

                  <div v-if="res.device_name">
                    <dt class="text-[11px] uppercase tracking-[0.18em] text-gray-400 dark:text-gray-500">Device</dt>
                    <dd class="mt-1 text-sm text-gray-700 dark:text-gray-200">{{ res.device_name }}</dd>
                  </div>

                  <div v-if="res.port">
                    <dt class="text-[11px] uppercase tracking-[0.18em] text-gray-400 dark:text-gray-500">Port</dt>
                    <dd class="mt-1 font-mono text-sm text-gray-700 dark:text-gray-200">{{ res.port }}</dd>
                  </div>
                </dl>
              </article>
            </div>
          </article>
        </div>

        <div v-else class="mt-4 flex justify-center rounded-2xl border border-dashed border-gray-200/80 bg-white/70 p-8 dark:border-gray-700/80 dark:bg-gray-950/25">
          <ProgressSpinner />
        </div>
      </section>
    </div>
  </Dialog>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import macSearch from "@/services/macSearch";

export default defineComponent({
  computed: {
    zabbixLinks() {
      return this.macSearch.lastMacDetail?.zabbix || [];
    },
  },
  data() {
    return {
      macSearch: macSearch
    }
  },
  methods: {
    formatResultsCount(count: number): string {
      if (count % 10 === 1 && count % 100 !== 11) return "совпадение";
      if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "совпадения";
      return "совпадений";
    },
  },
})
</script>
