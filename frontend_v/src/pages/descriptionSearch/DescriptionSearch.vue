<template>
  <Header/>

  <div class="mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
    <div class="flex items-center flex-col gap-6">
      <div class="sm:px-4 lg:px-8 max-w-7xl w-full flex flex-col gap-6">
        <div
            class=" w-full relative overflow-hidden rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur">
          <div
              class="absolute inset-0 bg-linear-to-br from-indigo-500/10 via-transparent to-sky-500/10 pointer-events-none"/>
          <div class="relative p-6 sm:p-8">
            <div class="flex flex-col lg:flex-row gap-8 lg:items-start lg:justify-between">
              <div class="max-w-3xl">
                <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
                  Поиск по описанию портов
                </h1>
                <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300">
                  Поиск строки в описании порта и комментариях ко всем ранее собранным интерфейсам на оборудовании.
                </p>
              </div>
              <div class="hidden lg:block w-32 shrink-0 opacity-90">
                <img class="w-full" src="/img/search-description-2.svg" alt="">
              </div>
            </div>
          </div>
        </div>

      <div
          class="rounded-3xl max-w-7xl w-full border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-4 sm:p-6"
          :class="{ '!ring-2 !ring-indigo-400/60 dark:!ring-indigo-500/40': isRegexPattern }">
        <div
            class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-gray-200/60 dark:border-gray-700/60">
          <label
              for="isRegexPattern"
              class="flex items-center gap-2 cursor-pointer"
              :class="{ 'opacity-50 cursor-not-allowed pointer-events-none': waitResult }">
            <ToggleSwitch v-model="isRegexPattern" input-id="isRegexPattern" :disabled="waitResult"/>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">Искать по регулярному выражению</span>
          </label>
          <div v-if="isRegexPattern"
               class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 flex flex-wrap items-center gap-2">
            <span>Проверка шаблона —</span>
            <a href="https://regex101.com/" target="_blank" rel="noopener noreferrer"
               class="text-indigo-600 dark:text-indigo-400 hover:underline">regex101.com</a>
          </div>
        </div>
        <div class="mt-4">
          <SearchInput
              @submit_input="searchDescription"
              @update:modelValue="(v: string) => pattern = v"
              :init-search="$route.query.pattern?.toString()"
              :active-mode="true"
              input-class="font-mono"
              placeholder="Введите строку для поиска"/>
        </div>
      </div>
      </div>

      <div v-if="waitResult"
           class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur px-6 py-10 text-center">
        <p class="text-base sm:text-lg text-gray-800 dark:text-gray-100">
          Поиск по паттерну:
          <code class="mx-1 px-2 py-0.5 rounded-lg bg-gray-100 dark:bg-gray-800 font-mono text-sm">{{ pattern }}</code>
        </p>
        <img class="mx-auto mt-6 h-[200px] object-contain" src="/img/load_desc.gif" alt="Загрузка">
      </div>

      <template v-else-if="lastPattern">
        <div
            v-if="interfaces.length"
            class="rounded-3xl w-full border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-4 sm:p-6">
          <div class="mb-4 text-center sm:text-left space-y-1">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Результаты по паттерну
              <code class="ml-1 text-indigo-700 dark:text-indigo-300 font-mono text-base">{{ lastPattern }}</code>
            </h2>
            <p class="text-sm font-mono text-gray-600 dark:text-gray-300">Найдено: {{ interfaces.length }}</p>
          </div>

          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
              <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5 flex-1">
                <div class="min-w-0">
                  <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Оборудование
                  </div>
                  <InputText v-model="filters.device" class="w-full" placeholder="Поиск по имени"/>
                </div>
                <div class="min-w-0">
                  <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Порт
                  </div>
                  <InputText v-model="filters.port" class="w-full" placeholder="Поиск порта"/>
                </div>
                <div class="min-w-0">
                  <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Статус
                  </div>
                  <Select v-model="filters.status" :options="statusOptions" placeholder="Все" class="w-full"
                          :showClear="true"/>
                </div>
                <div class="min-w-0">
                  <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Описание
                  </div>
                  <InputText v-model="filters.description" class="w-full" placeholder="Поиск"/>
                </div>
                <div class="min-w-0">
                  <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    VLAN
                  </div>
                  <InputText v-model="filters.vlans" class="w-full" placeholder="Поиск VLAN"/>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-2 xl:justify-end">
                <Button
                    severity="success"
                    @click="exportCSV"
                    icon="pi pi-file-excel"
                    outlined
                    label="CSV"
                    class="shrink-0"
                    v-tooltip.left="'Экспорт текущей таблицы по фильтру, но без сортировки'"/>
                <Button
                    v-if="hasActiveFilters || sortState.key"
                    severity="secondary"
                    outlined
                    icon="pi pi-filter-slash"
                    label="Сбросить"
                    @click="clearTableState"/>
                <Select
                    v-model="rows"
                    :options="rowsPerPageOptions"
                    class="w-[5.5rem]"/>
              </div>
            </div>

            <div class="text-sm font-mono text-gray-600 dark:text-gray-300">
              {{ filteredInterfaces.length }} строк
            </div>

            <div
                class="overflow-x-auto rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/50 dark:bg-gray-950/20">
              <table class="min-w-[1100px] w-full text-sm">
                <thead
                    class="border-b border-gray-200/70 dark:border-gray-700/70 bg-white/80 dark:bg-gray-900/70 backdrop-blur">
                <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
                  <th class="px-4 py-3 text-left font-semibold cursor-pointer select-none"
                      @click="toggleSort('device')">
                    Оборудование <span
                      v-if="sortState.key === 'device'">{{ sortState.dir === 'asc' ? '↑' : '↓' }}</span>
                  </th>
                  <th class="px-4 py-3 text-left font-semibold cursor-pointer select-none" @click="toggleSort('port')">
                    Порт <span v-if="sortState.key === 'port'">{{ sortState.dir === 'asc' ? '↑' : '↓' }}</span>
                  </th>
                  <th class="px-4 py-3 text-left font-semibold cursor-pointer select-none"
                      @click="toggleSort('status')">
                    Статус <span v-if="sortState.key === 'status'">{{
                      sortState.dir === 'asc' ? '↑' : '↓'
                    }}</span>
                  </th>
                  <th class="px-4 py-3 text-left font-semibold cursor-pointer select-none"
                      @click="toggleSort('description')">
                    Описание <span v-if="sortState.key === 'description'">{{
                      sortState.dir === 'asc' ? '↑' : '↓'
                    }}</span>
                  </th>
                  <th class="px-4 py-3 text-left font-semibold">Комментарии</th>
                  <th class="px-4 py-3 text-left font-semibold cursor-pointer select-none" @click="toggleSort('vlans')">
                    VLAN <span v-if="sortState.key === 'vlans'">{{ sortState.dir === 'asc' ? '↑' : '↓' }}</span>
                  </th>
                </tr>
                </thead>

                <tbody>
                <tr
                    v-for="data in pageItems"
                    :key="`${data.device}-${data.interface.name}-${data.interface.savedTime}`"
                    class="border-b border-gray-200/60 dark:border-gray-700/60 align-top hover:bg-white/60 dark:hover:bg-gray-900/40 transition">
                  <td class="px-4 py-3">
                    <router-link :to="'/device/' + data.device" target="_blank" rel="noopener noreferrer">
                      <Button text icon="pi pi-box" class="text-nowrap max-w-full" :label="data.device"/>
                    </router-link>
                  </td>
                  <td class="px-4 py-3 font-mono">
                    <router-link
                        :to="'/device/' + data.device + '?port=' + data.interface.name"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="inline-block px-2 py-1 rounded-lg bg-indigo-200/90 text-gray-900 dark:bg-indigo-600/80 dark:text-gray-100 hover:opacity-90 transition">
                      {{ data.interface.name }}
                    </router-link>
                  </td>
                  <td class="px-4 py-3">
                    <div
                        v-tooltip="'Время опроса: ' + data.interface.savedTime.toString()"
                        class="text-nowrap p-2 flex items-center justify-center rounded-lg mx-auto max-w-[8rem]"
                        :style="statusStyle(data.interface.status)">
                      <span class="me-1">{{ data.interface.status }}</span>
                      <i class="pi pi-clock"/>
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-sm leading-relaxed text-gray-800 dark:text-gray-200 font-mono"
                         v-html="markDescription(data.interface.description)"/>
                  </td>
                  <td class="px-4 py-3">
                    <Comment :interface="getInterface(data)" :markedText="lastPattern" :device-name="data.device"/>
                  </td>
                  <td class="px-4 py-3">
                    <button
                        type="button"
                        class="w-full text-left font-mono text-indigo-600 dark:text-indigo-400 hover:underline"
                        @click="toggleVlansList($event, data.interface)">
                      {{ truncateVlans(data.interface.vlans) }}
                    </button>
                  </td>
                </tr>

                <tr v-if="!pageItems.length">
                  <td colspan="6" class="px-4 py-10 text-center">
                    <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">По фильтрам ничего не найдено
                    </div>
                    <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Измените фильтры или сбросьте их.
                    </div>
                  </td>
                </tr>
                </tbody>
              </table>
            </div>

            <div v-if="filteredInterfaces.length > rows" class="pt-1">
              <Paginator
                  :rows="rows"
                  :totalRecords="filteredInterfaces.length"
                  :first="page * rows"
                  :rowsPerPageOptions="rowsPerPageOptions"
                  @page="onPage"
                  :pt="{
                    root: { class: 'rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-2' }
                  }"/>
            </div>
          </div>
        </div>

        <div
            v-else
            class="rounded-3xl border border-dashed border-gray-200/80 dark:border-gray-700/60 bg-white/50 dark:bg-gray-900/30 backdrop-blur px-6 py-12 text-center">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">
            По паттерну
            <code class="mx-1 px-2 py-0.5 rounded-lg bg-amber-100/90 dark:bg-amber-900/40 font-mono">{{
                lastPattern
              }}</code>
            совпадений нет
          </h2>
          <svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" fill="currentColor"
               class="mx-auto mt-6 text-gray-400 dark:text-gray-500" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path
                d="M4.285 12.433a.5.5 0 0 0 .683-.183A3.498 3.498 0 0 1 8 10.5c1.295 0 2.426.703 3.032 1.75a.5.5 0 0 0 .866-.5A4.498 4.498 0 0 0 8 9.5a4.5 4.5 0 0 0-3.898 2.25.5.5 0 0 0 .183.683zM7 6.5C7 7.328 6.552 8 6 8s-1-.672-1-1.5S5.448 5 6 5s1 .672 1 1.5zm4 0c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5S9.448 5 10 5s1 .672 1 1.5z"/>
          </svg>
        </div>
      </template>
    </div>
  </div>

  <Popover
      ref="vlansList"
      :pt="{
        root: {
          class: 'before:!hidden overflow-hidden rounded-2xl border border-gray-200/80 dark:border-gray-700/60 ' +
              'bg-white/95 dark:bg-gray-900/80 dark:backdrop-blur-xl shadow-lg dark:!ring-1 dark:!ring-white/5',
        },
        content: { class: '!p-4 max-w-md' },
      }">
    <div class="text-xs text-gray-500 dark:text-gray-400 pb-3 border-b border-gray-200/70 dark:border-gray-700/60">
      <i class="pi pi-clock me-2 text-sm"/>
      {{ selectedVlansTime }}
    </div>
    <div class="mt-3 text-sm font-mono text-gray-800 dark:text-gray-100 whitespace-pre-wrap break-all">{{
        selectedVlans
      }}
    </div>
  </Popover>

  <Footer/>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import Comment from "@/components/Comment.vue";
import SearchInput from "@/components/SearchInput.vue";
import {DeviceInterface, findInterfacesByDescription, InterfaceDescriptionMatchResult} from "@/services/interfaces";
import {markText} from "@/formats.ts";

type SortKey = "device" | "port" | "status" | "description" | "vlans";
type SortDir = "asc" | "desc";

export default defineComponent({
  components: {Footer, Header, Comment, SearchInput},

  data() {
    return {
      interfaces: [] as InterfaceDescriptionMatchResult[],
      pattern: "" as string,
      lastPattern: "" as string,
      isRegexPattern: false,
      waitResult: false,

      rows: 25,
      page: 0,
      rowsPerPageOptions: [10, 25, 50, 100],
      statusOptions: ["up", "down", "admin down", "noPresent", "notPresent", "dormant"],

      selectedVlans: "",
      selectedVlansTime: "",

      filters: {
        device: "",
        port: "",
        status: null as string | null,
        description: "",
        vlans: "",
      },

      sortState: {
        key: null as SortKey | null,
        dir: "asc" as SortDir,
      },
    }
  },

  computed: {
    hasActiveFilters(): boolean {
      return Boolean(
          this.filters.device ||
          this.filters.port ||
          this.filters.status ||
          this.filters.description ||
          this.filters.vlans
      );
    },

    filteredInterfaces(): InterfaceDescriptionMatchResult[] {
      const device = this.filters.device.trim().toLowerCase();
      const port = this.filters.port.trim().toLowerCase();
      const status = (this.filters.status || "").trim().toLowerCase();
      const description = this.filters.description.trim().toLowerCase();
      const vlans = this.filters.vlans.trim().toLowerCase();

      return this.interfaces.filter((item) => {
        if (device && !item.device.toLowerCase().includes(device)) return false;
        if (port && !item.interface.name.toLowerCase().includes(port)) return false;
        if (status && item.interface.status.toLowerCase() !== status) return false;
        if (description && !item.interface.description.toLowerCase().includes(description)) return false;
        if (vlans && !item.interface.vlans.toLowerCase().includes(vlans)) return false;
        return true;
      });
    },

    sortedInterfaces(): InterfaceDescriptionMatchResult[] {
      const list = [...this.filteredInterfaces];
      if (!this.sortState.key) return list;

      const dir = this.sortState.dir === "asc" ? 1 : -1;
      list.sort((a, b) => {
        const av = this.getSortValue(a, this.sortState.key!);
        const bv = this.getSortValue(b, this.sortState.key!);
        return av.localeCompare(bv, "ru", {numeric: true, sensitivity: "base"}) * dir;
      });
      return list;
    },

    pageItems(): InterfaceDescriptionMatchResult[] {
      const start = this.page * this.rows;
      return this.sortedInterfaces.slice(start, start + this.rows);
    },
  },

  watch: {
    filteredInterfaces() {
      if (this.page * this.rows >= this.filteredInterfaces.length) {
        this.page = 0;
      }
    },

    rows() {
      this.page = 0;
    },
  },

  mounted() {
    if (this.$route.query.pattern) {
      this.pattern = this.$route.query.pattern.toString();
      this.searchDescription();
    }
  },

  methods: {
    getInterface(data: InterfaceDescriptionMatchResult): DeviceInterface {
      return {
        name: data.interface.name,
        description: data.interface.description,
        status: data.interface.status,
        vlans: [],
        comments: data.comments,
      }
    },

    searchDescription() {
      if (this.pattern.length < 2) return;
      this.waitResult = true;
      this.page = 0;

      this.$router.replace({query: {...this.$route.query, pattern: this.pattern}});

      findInterfacesByDescription(this.pattern, this.isRegexPattern)
          .then(
              data => {
                this.interfaces = data;
                this.lastPattern = this.pattern;
                this.waitResult = false;
              },
              () => this.waitResult = false
          )
          .catch(() => this.waitResult = false)
    },

    markDescription(desc: string): string {
      return markText(desc, this.lastPattern)
    },

    statusStyle(status: string): Record<string, string> {
      status = status.toLowerCase()
      const style: Record<string, string> = {
        color: 'black',
        width: '120px',
      }
      if (status === "admin down") {
        style['background-color'] = "#ffb4bb";
      } else if (status === "notpresent" || status === "nopresent") {
        style['background-color'] = "#c1c1c1"
      } else if (status === "dormant") {
        style['background-color'] = "#ffe389"
      } else if (status !== "down") {
        style['background-color'] = "#22e58b"
      }

      style.color = style['background-color'] ? "black" : ""

      return style
    },

    truncateVlans(vlans: string): string {
      if (vlans.length > 17) {
        return vlans.slice(0, 15) + "..."
      }
      return vlans
    },

    getSortValue(data: InterfaceDescriptionMatchResult, key: SortKey): string {
      if (key === "device") return data.device || "";
      if (key === "port") return data.interface.name || "";
      if (key === "status") return data.interface.status || "";
      if (key === "description") return data.interface.description || "";
      return data.interface.vlans || "";
    },

    toggleSort(key: SortKey) {
      if (this.sortState.key !== key) {
        this.sortState.key = key;
        this.sortState.dir = "asc";
        return;
      }

      if (this.sortState.dir === "asc") {
        this.sortState.dir = "desc";
      } else {
        this.sortState.key = null;
        this.sortState.dir = "asc";
      }
    },

    clearTableState() {
      this.filters.device = "";
      this.filters.port = "";
      this.filters.status = null;
      this.filters.description = "";
      this.filters.vlans = "";
      this.sortState.key = null;
      this.sortState.dir = "asc";
      this.page = 0;
    },

    onPage(event: { page: number; rows: number }) {
      this.page = event.page;
      this.rows = event.rows;
    },

    toggleVlansList(event: Event, intf: { vlans: string, vlansSavedTime: string }) {
      this.selectedVlans = intf.vlans;
      this.selectedVlansTime = intf.vlansSavedTime;
      (this.$refs.vlansList as { toggle: (e: Event) => void }).toggle(event);
    },

    exportCSV() {
      const header = ["device", "port", "status", "description", "comments", "vlans"];
      const lines = [header.join(",")];

      for (const item of this.filteredInterfaces) {
        const comments = item.comments.map((comment) => comment.text).join(" | ");
        const row = [
          item.device,
          item.interface.name,
          item.interface.status,
          item.interface.description,
          comments,
          item.interface.vlans,
        ].map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`);
        lines.push(row.join(","));
      }

      const blob = new Blob([lines.join("\n")], {type: "text/csv;charset=utf-8;"});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "description-search.csv";
      link.click();
      URL.revokeObjectURL(url);
    },
  },
});
</script>
