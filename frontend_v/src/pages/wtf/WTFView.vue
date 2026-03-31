<script lang="ts" setup>
import {ref} from "vue";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import macSearch, {IPMACInfoResult} from "@/services/macSearch";
import errorFmt from "@/errorFmt.ts";
import BrasSession from "@/pages/deviceInfo/components/BrasSession.vue";
import brasSessionsService from "@/services/bras.sessions.ts";

const text = ref("");
const error = ref("");

interface WTFSearchResults {
  search: string;
  result: IPMACInfoResult;
}

const results = ref<WTFSearchResults[]>([]);
const running = ref(false);

function clearResults() {
  results.value = [];
}

async function find() {
  if (!text.value.length || running.value) return;
  running.value = true;

  if (text.value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/)) {
    try {
      error.value = "";
      const value: IPMACInfoResult | null = await macSearch.getMacDetail(text.value);
      if (value) {
        results.value.unshift({search: text.value, result: value});
      }
    } catch (e: any) {
      error.value = errorFmt(e);
    }
    running.value = false;
    return;
  }

  const macAddress = text.value.replace(/[^A-Fa-f\d]/g, "");
  if (macAddress.length === 12) {
    try {
      error.value = "";
      const value = await macSearch.getMacDetail(macAddress);
      if (value) results.value.unshift({search: text.value, result: value});
    } catch (e: any) {
      error.value = errorFmt(e);
    }
    running.value = false;
    return;
  }

  error.value = "Введенное значение не является MAC-адресом или IP-адресом";
  running.value = false;
}
</script>

<template>
  <Header/>

  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
    <div class="flex flex-col gap-6">
      <div
          class="
          relative overflow-hidden
          rounded-3xl border border-gray-200/70 dark:border-gray-700/70
          bg-white/70 dark:bg-gray-900/40
          backdrop-blur
          transition hover:-translate-y-0.5
          delay-0
          hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md
        ">
        <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-sky-500/10"/>
        <div class="relative p-6 sm:p-8">
          <div class="flex flex-col lg:flex-row gap-8 lg:items-start lg:justify-between">
            <div class="max-w-2xl">
              <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
                WTF — поиск по MAC / IP
              </h1>
              <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300">
                Укажите адрес в любом распространённом формате MAC или IPv4. Результаты накапливаются сверху — можно
                сравнивать несколько запросов подряд.
              </p>

              <Message v-if="error" severity="error" class="mt-4 w-full max-w-xl" closable @close="error = ''">
                {{ error }}
              </Message>

              <div class="mt-6 flex flex-col sm:flex-row gap-3 sm:items-center">
                <div
                    class="flex flex-1 w-full min-w-0 items-center gap-2 rounded-2xl border border-gray-200/80 dark:border-gray-600/80 bg-white/90 dark:bg-gray-900/50 px-3 py-2 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500/25 dark:focus-within:ring-indigo-400/20">
                  <i class="pi pi-search text-gray-400 dark:text-gray-500 text-sm shrink-0"/>
                  <InputText
                      v-model="text"
                      class="flex-1 min-w-0 !border-0 !bg-transparent !shadow-none !outline-none font-mono text-sm sm:text-base"
                      placeholder="Например: 192.168.0.1 или aa:bb:cc:dd:ee:ff"
                      :disabled="running"
                      @keyup.enter="find"/>
                </div>
                <div class="flex flex-wrap gap-2">
                  <Button
                      :loading="running"
                      icon="pi pi-search"
                      label="Найти"
                      class="!rounded-2xl"
                      @click="find"/>
                  <Button
                      v-if="results.length"
                      icon="pi pi-trash"
                      label="Очистить результаты"
                      severity="secondary"
                      outlined
                      class="!rounded-2xl"
                      @click="clearResults"/>
                </div>
              </div>
              <p class="mt-3 text-xs text-gray-500 dark:text-gray-400">
                Enter в поле ввода запускает тот же поиск, что и кнопка «Найти».
              </p>
            </div>

            <div class="hidden lg:flex w-40 shrink-0 justify-center opacity-90">
              <img class="w-full max-w-[10rem]" src="/img/mac-icon.svg" alt="">
            </div>
          </div>
        </div>
      </div>

      <div v-if="!results.length" class="rounded-3xl border border-dashed border-gray-200/80 dark:border-gray-700/60 bg-white/40 dark:bg-gray-900/20 backdrop-blur px-6 py-10 text-center">
        <div class="text-gray-500 dark:text-gray-400 text-sm">
          Пока нет запросов. Введите MAC или IP в блоке выше — сюда появятся разворачиваемые карточки с деталями.
        </div>
      </div>

      <div v-for="(block, idx) in results" :key="block.search + '-' + idx" class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur overflow-hidden">
        <Fieldset
            :toggleable="true"
            :collapsed="idx > 2"
            :pt="{
              root: { class: '!border-0 !bg-transparent !shadow-none' },
              legend: { class: '!border-0 !bg-transparent !ml-0 !p-0' },
              toggler: { class: '!rounded-2xl hover:!bg-gray-100/80 dark:hover:!bg-gray-800/50' },
              content: { class: '!p-0 pt-4 border-t border-gray-200/70 dark:border-gray-700/60' },
            }">
          <template #legend="{toggleCallback}">
            <button
                type="button"
                class="flex flex-wrap items-center gap-2 text-left px-2 py-1 rounded-2xl text-gray-900 dark:text-gray-100"
                @click="toggleCallback">
              <span class="text-sm font-semibold">Запрос</span>
              <code class="text-sm font-mono px-2 py-0.5 rounded-lg bg-indigo-500/10 dark:bg-indigo-400/15 text-indigo-700 dark:text-indigo-300">{{ block.search }}</code>
              <span class="text-xs text-gray-500 dark:text-gray-400">{{ block.result.info?.length || 0 }} источник(ов)</span>
            </button>
          </template>

          <div class="flex flex-col gap-4 px-1 pb-2">
            <div
                v-for="(info, infoIdx) in block.result.info"
                :key="infoIdx"
                class="rounded-2xl border border-gray-200/70 dark:border-gray-700/60 bg-white/60 dark:bg-gray-950/30 p-4 sm:p-5">
              <Fieldset
                  :toggleable="true"
                  :pt="{
                    root: { class: '!border-0 !bg-transparent !shadow-none' },
                    legend: { class: '!border-0 !bg-transparent !ml-0 !p-0' },
                    toggler: { class: '!rounded-xl' },
                    content: { class: '!p-0 pt-3' },
                  }">
                <template #legend="{toggleCallback}">
                  <Button
                      text
                      class="!p-2 !justify-start"
                      :label="info?.device?.name ? ('Найдено на ' + info.device.name) : 'Результат'"
                      icon="pi pi-server"
                      @click="toggleCallback"/>
                </template>

                <div class="flex flex-wrap gap-2 mb-4">
                  <a
                      v-for="zbx in block.result.zabbix"
                      :key="zbx.hostid"
                      :href="block.result.zabbix_url + '/hostinventories.php?hostid=' + zbx.hostid"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex">
                    <Button severity="danger" outlined class="!rounded-xl gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 64 64" class="shrink-0">
                        <path d="M0 0h64v64H0z" fill="#d31f26"/>
                        <path d="M18.8 15.382h26.393v3.424l-21.24 26.027h21.744v3.784H18.293v-3.43l21.24-26.02H18.8z" fill="#fff"/>
                      </svg>
                      <span class="font-mono text-sm">{{ zbx.name }}</span>
                    </Button>
                  </a>
                </div>

                <div class="flex flex-col gap-3">
                  <div
                      v-for="(row, rowIdx) in info.results"
                      :key="rowIdx"
                      class="rounded-xl border border-gray-100 dark:border-gray-700/50 bg-gray-50/80 dark:bg-gray-900/40 p-4 font-mono text-sm">
                    <div v-if="info?.device?.name && info.device.name.startsWith('BRAS')" class="flex justify-center pb-3">
                      <Button
                          size="small"
                          outlined
                          icon="pi pi-user"
                          label="Сессия по MAC"
                          class="!rounded-xl"
                          @click="() => brasSessionsService.getSessions(row.mac, '', '')"/>
                    </div>
                    <div class="grid gap-2 sm:grid-cols-2">
                      <div><span class="text-gray-500 dark:text-gray-400">IP</span> — {{ row.ip }}</div>
                      <div><span class="text-gray-500 dark:text-gray-400">MAC</span> — {{ row.mac }}</div>
                      <div><span class="text-gray-500 dark:text-gray-400">VLAN</span> — {{ row.vlan }}</div>
                      <div v-if="row.device_name"><span class="text-gray-500 dark:text-gray-400">Device</span> — {{ row.device_name }}</div>
                      <div v-if="row.port" class="sm:col-span-2"><span class="text-gray-500 dark:text-gray-400">Port</span> — {{ row.port }}</div>
                    </div>
                  </div>
                </div>
              </Fieldset>
            </div>
          </div>
        </Fieldset>
      </div>
    </div>
  </div>

  <BrasSession/>
  <Footer/>
</template>
