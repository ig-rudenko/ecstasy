<template>
  <Header/>

  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
    <div class="flex flex-col gap-6 sm:gap-8 md:gap-10 lg:gap-16 xl:gap-24">
      <div
          class="
          relative overflow-hidden
          rounded-3xl border border-gray-200/50 dark:border-gray-700/50
          bg-white/75 dark:bg-gray-900/45
          backdrop-blur
          transition hover:-translate-y-0.5
          delay-0
          hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md
          ">
        <div class="absolute inset-0 bg-linear-to-br from-indigo-500/10 via-transparent to-sky-500/10 pointer-events-none"/>
        <div class="relative p-5 sm:p-7 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
              Трассировка L2
            </h1>
            <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300 max-w-2xl">
              Построение графа по VLAN или по MAC
            </p>
          </div>

          <div class="flex flex-col sm:flex-row sm:items-center gap-3">
            <span class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Режим</span>
            <div
                class="inline-flex w-fit rounded-2xl p-1 border border-gray-200/80 dark:border-gray-700/60 bg-gray-100/80 dark:bg-gray-950/40">
              <button
                  type="button"
                  :class="tracerouteMode === 'vlan'
                    ? 'shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'"
                  class="cursor-pointer px-4 py-2 rounded-xl text-sm font-medium transition"
                  @click="setTracerouteMode('vlan')">
                VLAN
              </button>
              <button
                  type="button"
                  :class="tracerouteMode === 'mac'
                    ? 'shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'"
                  class="cursor-pointer px-4 py-2 rounded-xl text-sm font-medium transition"
                  @click="setTracerouteMode('mac')">
                MAC
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- VLAN -->
      <div
          v-show="tracerouteMode === 'vlan'"
          class="
            w-fit
            rounded-3xl border border-gray-200/50 dark:border-gray-700/50
            bg-white/75 dark:bg-gray-900/45
            backdrop-blur
            p-5 sm:p-6 space-y-5
            transition hover:-translate-y-0.5
            delay-0
            hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md
          ">
        <div class="flex flex-wrap items-center gap-3">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 m-0">VLAN traceroute</h2>
          <div class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <template v-if="vlanScanStatus.running && vlanScanStatus.progress && vlanScanStatus.progress > 0">
              <ProgressSpinner class="w-6! h-6!" stroke-width="4"/>
              <span>Сканирование: {{ vlanScanStatus.progress }}%</span>
            </template>
            <template v-else-if="vlanScanStatus.running">
              <ProgressSpinner class="w-6! h-6!" stroke-width="4"/>
              <span>Идёт сканирование VLAN…</span>
            </template>
            <template v-else-if="!vlanScanStatus.running && vlanScanStatus.available">
              <button
                  type="button"
                  class="p-2 rounded-xl text-gray-700 dark:text-gray-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/60 transition cursor-pointer"
                  v-tooltip.bottom="'Запустить скан VLAN\'ов'"
                  @click="vlanScanStatus.run_vlans_scan">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                  <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
                </svg>
              </button>
            </template>
            <template v-else>
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor"
                   class="text-red-500 shrink-0" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path
                    d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
              </svg>
              <span class="text-red-600 dark:text-red-400">Скан VLAN недоступен</span>
            </template>
          </div>
        </div>

        <div class="flex flex-wrap items-end gap-3">
          <div>
            <InputNumber
                :min="1"
                :max="4096"
                v-model="input.vlan"
                placeholder="vlan"
                class="mt-1"
                input-class="!w-28 !rounded-2xl !text-center !font-mono !text-lg !bg-white/95 dark:!bg-gray-950/60 !text-gray-900 dark:!text-gray-100 !border-gray-200/80 dark:!border-gray-700/60"
                @keyup.enter="load_vlan_traceroute"
                @input="getInputVlanInfo"/>
          </div>
          <Button
              rounded
              class="rounded-2xl!"
              :loading="vlanTracerouteStarted"
              v-tooltip.bottom="'Построить граф'"
              @click="load_vlan_traceroute">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-bezier2"
                 viewBox="0 0 16 16">
              <path fill-rule="evenodd"
                    d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01c.18.18.34.381.484.605.638.992.892 2.354.892 3.895 0 1.993.257 3.092.713 3.7.356.476.895.721 1.787.784A1.5 1.5 0 0 1 12.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5H6.866a1 1 0 1 1 0-1h1.711a2.839 2.839 0 0 1-.165-.2C7.743 11.407 7.5 10.007 7.5 8c0-1.46-.246-2.597-.733-3.355-.39-.605-.952-1-1.767-1.112A1.5 1.5 0 0 1 3.5 5h-1A1.5 1.5 0 0 1 1 3.5v-1zM2.5 2a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1zm10 10a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
            </svg>
          </Button>
          <div v-if="inputVlanInfo.name" class="text-sm text-gray-700 dark:text-gray-200 pb-1 font-mono">
            {{ inputVlanInfo.name }}
            <span v-if="inputVlanInfo.description" class="text-gray-500 dark:text-gray-400">({{ inputVlanInfo.description }})</span>
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-1 md:max-w-3xl">
          <div class="flex items-center gap-3">
            <ToggleSwitch input-id="adminDownPorts" v-model="vlanTracerouteOptions.adminDownPorts"/>
            <label for="adminDownPorts" class="text-sm text-gray-700 dark:text-gray-200 cursor-pointer">Указывать выключенные порты</label>
          </div>
          <div class="flex items-center gap-3">
            <ToggleSwitch input-id="showEmptyPorts" v-model="vlanTracerouteOptions.showEmptyPorts"/>
            <label for="showEmptyPorts" class="text-sm text-gray-700 dark:text-gray-200 cursor-pointer">Показывать пустые порты</label>
          </div>
          <div class="flex items-center gap-3">
            <ToggleSwitch input-id="doubleCheckVlan" v-model="vlanTracerouteOptions.doubleCheckVlan"/>
            <label for="doubleCheckVlan" class="text-sm text-gray-700 dark:text-gray-200 cursor-pointer">Двухстороннее соответствие VLAN на соседних портах</label>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3 pt-1">
          <span class="text-sm text-gray-600 dark:text-gray-300">Мин. число узлов в графе</span>
          <InputGroup unstyled class="inline-flex items-center rounded-2xl border border-gray-200/80 dark:border-gray-700/60 bg-white/90 dark:bg-gray-950/40 px-1">
            <Button icon="pi pi-minus" text rounded @click="vlanTracerouteOptions.graphMinLength > 1 ? vlanTracerouteOptions.graphMinLength-- : null"/>
            <InputNumber
                v-model="vlanTracerouteOptions.graphMinLength"
                :min="1"
                :max="100"
                input-class="!w-12 !border-0 !bg-transparent !text-center !font-mono !text-lg !text-gray-900 dark:!text-gray-100"/>
            <Button icon="pi pi-plus" text rounded @click="vlanTracerouteOptions.graphMinLength++"/>
          </InputGroup>
        </div>
      </div>

      <!-- MAC -->
      <div
          v-show="tracerouteMode === 'mac'"
          class="
            w-fit
            rounded-3xl border border-gray-200/50 dark:border-gray-700/50
            bg-white/75 dark:bg-gray-900/45
            backdrop-blur
            p-5 sm:p-6 space-y-5
            transition hover:-translate-y-0.5
            delay-0
            hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md
            ">
        <div class="flex flex-wrap items-center gap-3">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 m-0">MAC traceroute</h2>
          <div class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <template v-if="macScanStatus.running && macScanStatus.progress && macScanStatus.progress > 0">
              <ProgressSpinner class="w-6! h-6!" stroke-width="4"/>
              <span>Сканирование: {{ macScanStatus.progress }}%</span>
            </template>
            <template v-else-if="macScanStatus.running">
              <ProgressSpinner class="w-6! h-6!" stroke-width="4"/>
              <span>Идёт сканирование MAC…</span>
            </template>
            <template v-else-if="!macScanStatus.running && macScanStatus.available">
              <button
                  type="button"
                  class="p-2 rounded-xl text-gray-700 dark:text-gray-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/60 transition cursor-pointer"
                  v-tooltip.bottom="'Запустить скан MAC'"
                  @click="macScanStatus.run_vlans_scan">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                  <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
                </svg>
              </button>
            </template>
            <template v-else>
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor"
                   class="text-red-500 shrink-0" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path
                    d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
              </svg>
              <span class="text-red-600 dark:text-red-400">Скан MAC недоступен</span>
            </template>
          </div>
        </div>

        <div class="flex flex-wrap items-center jus gap-3">
          <div>
            <InputText
                v-model="input.mac"
                placeholder="MAC"
                class="mt-1 rounded-2xl! font-mono! min-w-56! bg-white/95! dark:bg-gray-950/60! text-gray-900! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60!"
                @keyup.enter="load_mac_traceroute"/>
          </div>
          <Button
              rounded
              class="rounded-2xl!"
              :loading="macTracerouteStarted"
              :disabled="macTracerouteStarted"
              v-tooltip.bottom="'Построить граф'"
              @click="load_mac_traceroute">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-bezier2"
                 viewBox="0 0 16 16">
              <path fill-rule="evenodd"
                    d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01c.18.18.34.381.484.605.638.992.892 2.354.892 3.895 0 1.993.257 3.092.713 3.7.356.476.895.721 1.787.784A1.5 1.5 0 0 1 12.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5H6.866a1 1 0 1 1 0-1h1.711a2.839 2.839 0 0 1-.165-.2C7.743 11.407 7.5 10.007 7.5 8c0-1.46-.246-2.597-.733-3.355-.39-.605-.952-1-1.767-1.112A1.5 1.5 0 0 1 3.5 5h-1A1.5 1.5 0 0 1 1 3.5v-1zM2.5 2a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1zm10 10a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
            </svg>
          </Button>
          <div>
            <InputNumber
                v-model="macTracerouteOptions.vlanFilter"
                placeholder="Фильтр VLAN"
                :min="1"
                :max="4096"
                class="mt-1 block"
                input-class="!w-[9rem] !rounded-2xl !text-center !font-mono !bg-white/95 dark:!bg-gray-950/60 !text-gray-900 dark:!text-gray-100 !border-gray-200/80 dark:!border-gray-700/60"/>
          </div>
        </div>
      </div>

      <div v-if="vlanTracerouteStarted || macTracerouteStarted" class="flex justify-center py-10">
        <div
            class="inline-flex flex-col items-center gap-4 rounded-3xl border border-gray-200/50 dark:border-gray-700/50 bg-white/80 dark:bg-gray-900/50 px-10 py-8 backdrop-blur">
          <ProgressSpinner class="w-16! h-16!" stroke-width="3"/>
          <span class="text-sm text-gray-600 dark:text-gray-300">Строим граф…</span>
        </div>
      </div>

      <div v-if="tracerouteMode === 'mac' && macTracerouteVLANInfo.length" class="flex flex-wrap gap-2 font-mono text-sm py-1">
        <div v-for="vlanInfo in macTracerouteVLANInfo" :key="vlanInfo.vid" class="inline-flex rounded-xl overflow-hidden border border-gray-200/60 dark:border-gray-700/60 shadow-sm">
          <button
              type="button"
              class="cursor-pointer py-1.5 pl-3 pr-2 font-medium bg-indigo-500 text-white dark:bg-indigo-600 hover:bg-indigo-600 dark:hover:bg-indigo-500 transition"
              v-tooltip.bottom="macTracerouteOptions.vlanFilter == vlanInfo.vid ? 'Убрать фильтр' : `Фильтр по VLAN ${vlanInfo.vid}`"
              @click="tracerouteMACWithVlanFilter(vlanInfo.vid)">
            vid: {{ vlanInfo.vid }}
          </button>
          <span
              v-tooltip.bottom="vlanInfo.description || 'Нет описания'"
              class="py-1.5 px-2 bg-gray-600 text-white dark:bg-gray-700 max-w-48 truncate">
            {{ vlanInfo.name }}
          </span>
          <span v-tooltip.bottom="'Количество'" class="py-1.5 pl-2 pr-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
            {{ vlanInfo.count }}
          </span>
        </div>
      </div>

      <div
          :class="[
            'relative rounded-3xl border shadow-inner min-h-120',
            graphAreaTransparent ? 'border-gray-200/40 dark:border-gray-700/50 overflow-hidden bg-black/35 dark:bg-black/50 backdrop-blur-[2px]' : 'border-gray-700 overflow-hidden bg-neutral-950',
            graphMaximized ? 'overflow-visible! rounded-none! border-0 shadow-none min-h-0 bg-transparent' : '',
          ]">
        <div
            v-show="tracerouteMode === 'vlan'"
            :class="[
              'relative min-h-[480px] h-[900px]',
              vlanTracerouteOptions.maximized ? 'maximized-shell' : '',
            ]">
          <Button
              v-if="vlanTracerouteOptions.rendered"
              class="!absolute z-[10001] top-3 right-3 !rounded-xl"
              :icon="vlanTracerouteOptions.maximized ? 'pi pi-times' : 'pi pi-expand'"
              rounded
              severity="secondary"
              v-tooltip.bottom="vlanTracerouteOptions.maximized ? 'Выйти из полного экрана' : 'На весь экран'"
              @click="toggleMaximizeVlanTraceroute"/>
          <div
              id="vlan-network"
              :class="[
                'min-h-[480px] h-full w-full',
                vlanTracerouteOptions.maximized ? 'maximized' : '',
              ]"/>
        </div>
        <div
            v-show="tracerouteMode === 'mac'"
            :class="[
              'relative min-h-[480px] h-[900px]',
              macTracerouteOptions.maximized ? 'maximized-shell' : '',
            ]">
          <Button
              v-if="macTracerouteOptions.rendered"
              class="!absolute z-[10001] top-3 right-3 !rounded-xl"
              :icon="macTracerouteOptions.maximized ? 'pi pi-times' : 'pi pi-expand'"
              rounded
              severity="secondary"
              v-tooltip.bottom="macTracerouteOptions.maximized ? 'Выйти из полного экрана' : 'На весь экран'"
              @click="toggleMaximizeMACTraceroute"/>
          <div
              id="mac-network"
              :class="[
                'min-h-[480px] h-full w-full',
                macTracerouteOptions.maximized ? 'maximized' : '',
              ]"/>
        </div>
      </div>
    </div>
  </div>

  <Footer/>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import api from "@/services/api";
import TracerouteNetwork from "./net";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import ScanStatus, {getInputVlanInfo} from "@/services/traceroute";
import {InputNumberInputEvent} from "primevue";
import {applyTracerouteForcedDark} from "@/services/themes";


interface VlanCountInfo {
  vid: number
  count: number
  name: string
  description: string
}


export default defineComponent({
  name: 'Traceroute',
  components: {Header, Footer},
  data() {
    return {
      vlanScanStatus: new ScanStatus("/api/v1/tools/vlans-scan/check", "/api/v1/tools/vlans-scan/run"),
      macScanStatus: new ScanStatus("/api/v1/gather/mac-address/scan/status", "/api/v1/gather/mac-address/scan/run"),

      vlanTracerouteStarted: false,
      macTracerouteStarted: false,

      // Установка значения по умолчанию для свойства tracerouteMode.
      tracerouteMode: 'vlan' as ("vlan" | "mac"),

      // Пользовательский ввод
      input: {
        vlan: null as number | null,
        mac: "",
      },

      inputVlanInfo: {
        name: "" as string,
        description: "" as string
      },

      // Свойство данных, которое используется для хранения состояния флажков.
      vlanTracerouteOptions: {
        adminDownPorts: false,
        showEmptyPorts: false,
        doubleCheckVlan: true,
        graphMinLength: 3,
        maximized: false,
        rendered: false,
      },

      macTracerouteOptions: {
        maximized: false,
        rendered: false,
        vlanFilter: null as number | null,
      },
      macTracerouteVLANInfo: [] as VlanCountInfo[],

      vlanNetwork: new TracerouteNetwork("vlan-network"),
      macNetwork: new TracerouteNetwork("mac-network"),

      restoreGlobalTheme: null as null | (() => void),
    }
  },

  computed: {
    graphAreaTransparent(): boolean {
      const vlanShown = this.tracerouteMode === 'vlan';
      const macShown = this.tracerouteMode === 'mac';
      const hasForMode =
          (vlanShown && this.vlanTracerouteOptions.rendered) ||
          (macShown && this.macTracerouteOptions.rendered);
      return !hasForMode;
    },
    graphMaximized(): boolean {
      return this.vlanTracerouteOptions.maximized || this.macTracerouteOptions.maximized;
    },
  },

  created() {
    this.restoreGlobalTheme = applyTracerouteForcedDark();
    this.vlanScanStatus.checkScanStatus();
    this.macScanStatus.checkScanStatus();
    document.body.classList.add('traceroute-back')
  },

  unmounted() {
    this.restoreGlobalTheme?.();
    this.restoreGlobalTheme = null;
    document.body.classList.remove("traceroute-back")
  },

  methods: {

    setTracerouteMode(mode: 'vlan' | 'mac') {
      if (this.tracerouteMode !== mode) {
        this.vlanTracerouteOptions.maximized = false;
        this.macTracerouteOptions.maximized = false;
      }
      this.tracerouteMode = mode;
    },

    getInputVlanInfo(event: InputNumberInputEvent) {
      const vid = parseInt(event.value?.toString() || "")
      getInputVlanInfo(vid).then(value => this.inputVlanInfo = value);
    },

    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода VLAN
     * И создаем в определенном блоке граф для данной трассировки.
     */
    load_vlan_traceroute() {
      if (!this.input.vlan) return;

      this.vlanTracerouteStarted = true

      let url = '/api/v1/tools/vlan-traceroute?vlan=' + this.input.vlan +
          '&ep=' + this.vlanTracerouteOptions.showEmptyPorts +
          '&ad=' + this.vlanTracerouteOptions.adminDownPorts +
          '&double_check=' + this.vlanTracerouteOptions.doubleCheckVlan +
          '&graph_min_length=' + this.vlanTracerouteOptions.graphMinLength

      api.get(url)
          .then(
              (resp) => {
                this.vlanNetwork.renderVisualData(resp.data.nodes, resp.data.edges);
                this.vlanTracerouteStarted = false;
                this.vlanTracerouteOptions.rendered = true;
              }
          ).catch(
          () => this.vlanTracerouteStarted = false
      )

    },

    toggleMaximizeVlanTraceroute() {
      this.vlanTracerouteOptions.maximized = !this.vlanTracerouteOptions.maximized;
      if (this.vlanTracerouteOptions.maximized) {
        setTimeout(() => document.getElementById("vlan-network")!.scrollIntoView({behavior: "instant", block: "end"}))
      }
    },
    toggleMaximizeMACTraceroute() {
      this.macTracerouteOptions.maximized = !this.macTracerouteOptions.maximized;
    },

    // Удаляет из MAC адреса все символы, не являющиеся шестнадцатеричными.
    validateMac(mac: string): string {
      return String(mac).replace(/\W/g, "")
    },


    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода MAC.
     * И создаем в определенном блоке граф для данной трассировки.
     */
    load_mac_traceroute() {
      let valid_mac = this.validateMac(this.input.mac)
      if (!valid_mac.length) return

      this.macTracerouteStarted = true
      const url = '/api/v1/gather/traceroute/mac-address/' + valid_mac + "/"
      const params: any = {}
      if (this.macTracerouteOptions.vlanFilter) {
        params["vlan"] = this.macTracerouteOptions.vlanFilter
      }

      api.get(url, {params: params})
          .then(
              resp => {
                this.macNetwork.renderVisualData(resp.data.nodes, resp.data.edges);
                this.macTracerouteVLANInfo = resp.data.vlansInfo;
                this.macTracerouteStarted = false;
                this.macTracerouteOptions.rendered = true;
              }
          )
          .catch(
              () => this.macTracerouteStarted = false
          )
    },

    tracerouteMACWithVlanFilter(vlan: number) {
      if (this.macTracerouteOptions.vlanFilter === vlan) {
        this.macTracerouteOptions.vlanFilter = null
      } else {
        this.macTracerouteOptions.vlanFilter = vlan
      }
      this.load_mac_traceroute()
    }

  }
});
</script>

<style scoped>
.maximized-shell {
  position: fixed !important;
  inset: 0 !important;
  z-index: 10000 !important;
  width: 100vw !important;
  height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  background-color: #000000 !important;
  border-radius: 0 !important;
}

.maximized {
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100vw !important;
  max-height: 100vh !important;
  margin: 0 !important;
  background-color: #000000 !important;
  border-radius: 0 !important;
}

.maximized :deep(.vis-network),
.maximized :deep(.vis-network > canvas) {
  width: 100% !important;
  height: 100% !important;
}
</style>
