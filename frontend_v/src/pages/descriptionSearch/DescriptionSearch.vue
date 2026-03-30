<template>
  <Header/>

  <div class="mx-auto max-w-[1500px] px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
    <div class="flex flex-col gap-6">
      <section class="relative overflow-hidden rounded-[2rem] border border-gray-200/70 bg-white/80 shadow-[0_24px_70px_-42px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.14),transparent_25%),radial-gradient(circle_at_85%_20%,rgba(14,165,233,0.14),transparent_22%)]" />
        <div class="relative p-5 sm:p-8">
          <div class="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
            <div class="max-w-4xl">


              <h1 class="mt-5 text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl">
                Поиск по описанию портов
              </h1>

              <p class="mt-3 max-w-3xl text-sm leading-7 text-gray-600 dark:text-gray-300 sm:text-base">
                Поиск строки в описаниях интерфейсов и комментариях по ранее собранным данным оборудования.
              </p>
            </div>

            <div class="hidden xl:block w-56 shrink-0 opacity-95">
              <img class="w-full" src="/img/search-description-2.svg" alt="search-description">
            </div>
          </div>
        </div>
      </section>

      <section
          class="rounded-[2rem] border border-gray-200/70 bg-white/80 p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6"
          :class="{ '!ring-2 !ring-indigo-400/60 dark:!ring-indigo-500/40': isRegexPattern }"
      >
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <label
                for="isRegexPattern"
                class="inline-flex w-fit items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                :class="{ 'opacity-50 cursor-not-allowed pointer-events-none': waitResult }"
            >
              <ToggleSwitch v-model="isRegexPattern" input-id="isRegexPattern" :disabled="waitResult"/>
              <span>Искать по регулярному выражению</span>
            </label>

            <div v-if="isRegexPattern" class="text-sm text-gray-500 dark:text-gray-400">
              Проверка шаблона:
              <a href="https://regex101.com/" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:underline dark:text-indigo-400">
                regex101.com
              </a>
            </div>
          </div>

          <SearchInput
              @submit_input="searchDescription"
              @update:modelValue="(v: string) => pattern = v"
              :init-search="$route.query.pattern?.toString()"
              :active-mode="true"
              input-class="font-mono"
              placeholder="Введите строку для поиска"
          />
        </div>
      </section>

      <div
          v-if="waitResult"
          class="rounded-[2rem] border border-gray-200/70 bg-white/80 px-6 py-10 text-center backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45"
      >
        <p class="text-base text-gray-800 dark:text-gray-100 sm:text-lg">
          Поиск по паттерну:
          <code class="mx-1 rounded-lg bg-gray-100 px-2 py-0.5 font-mono text-sm dark:bg-gray-800">{{ pattern }}</code>
        </p>
        <img class="mx-auto mt-6 h-[200px] object-contain" src="/img/load_desc.gif" alt="loading">
      </div>

      <template v-else-if="lastPattern">
        <section
            v-if="interfaces.length"
            class="rounded-[2rem] border border-gray-200/70 bg-white/80 p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6"
        >
          <div class="flex flex-col gap-5">
            <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Результаты по паттерну
                  <code class="ml-2 font-mono text-base text-indigo-700 dark:text-indigo-300">{{ lastPattern }}</code>
                </h2>
                <p class="mt-1 text-sm font-mono text-gray-600 dark:text-gray-300">Найдено: {{ filteredInterfaces.length }}</p>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <Button severity="success" @click="exportCSV" icon="pi pi-file-excel" outlined label="CSV" class="!rounded-2xl" />
                <Button
                    v-if="hasActiveFilters || sortState.key"
                    severity="secondary"
                    outlined
                    icon="pi pi-filter-slash"
                    label="Сбросить"
                    class="!rounded-2xl"
                    @click="clearTableState"
                />
              </div>
            </div>

            <div class="rounded-[1.75rem] border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40 overflow-hidden">
              <div class="border-b border-gray-200/70 p-4 dark:border-gray-700/70">
                <div class="flex flex-col gap-4">
                  <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm font-mono text-gray-600 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300">
                      {{ filteredInterfaces.length }} строк
                    </div>
                    <div class="w-full lg:w-[6rem]">
                      <Select v-model="rows" :options="rowsPerPageOptions" class="w-full" />
                    </div>
                  </div>

                  <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
                    <div class="min-w-0">
                      <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Оборудование</div>
                      <InputText v-model="filters.device" class="w-full" placeholder="Поиск по имени" />
                    </div>
                    <div class="min-w-0">
                      <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Порт</div>
                      <InputText v-model="filters.port" class="w-full" placeholder="Поиск порта" />
                    </div>
                    <div class="min-w-0">
                      <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Статус</div>
                      <Select v-model="filters.status" :options="statusOptions" placeholder="Все" class="w-full" :showClear="true" />
                    </div>
                    <div class="min-w-0">
                      <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Описание</div>
                      <InputText v-model="filters.description" class="w-full" placeholder="Поиск" />
                    </div>
                    <div class="min-w-0">
                      <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Комментарии</div>
                      <InputText v-model="filters.comments" class="w-full" placeholder="Поиск" />
                    </div>
                    <div class="min-w-0">
                      <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">VLAN</div>
                      <InputText v-model="filters.vlans" class="w-full" placeholder="Поиск VLAN" />
                    </div>
                  </div>
                </div>
              </div>

              <div class="overflow-x-auto">
                <table class="min-w-[1200px] w-full text-sm">
                  <thead class="border-b border-gray-200/70 bg-gray-50/80 dark:border-gray-700/70 dark:bg-gray-900/70">
                    <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
                      <th class="px-4 py-3 text-left font-semibold">
                        <button class="inline-flex items-center gap-2" @click="toggleSort('device')">
                          <span>Оборудование</span>
                          <i :class="sortIcon('device')" />
                        </button>
                      </th>
                      <th class="px-4 py-3 text-left font-semibold">
                        <button class="inline-flex items-center gap-2" @click="toggleSort('port')">
                          <span>Порт</span>
                          <i :class="sortIcon('port')" />
                        </button>
                      </th>
                      <th class="px-4 py-3 text-left font-semibold">
                        <button class="inline-flex items-center gap-2" @click="toggleSort('status')">
                          <span>Статус</span>
                          <i :class="sortIcon('status')" />
                        </button>
                      </th>
                      <th class="px-4 py-3 text-left font-semibold">
                        <button class="inline-flex items-center gap-2" @click="toggleSort('description')">
                          <span>Описание</span>
                          <i :class="sortIcon('description')" />
                        </button>
                      </th>
                      <th class="px-4 py-3 text-left font-semibold">Комментарии</th>
                      <th class="px-4 py-3 text-left font-semibold">
                        <button class="inline-flex items-center gap-2" @click="toggleSort('vlans')">
                          <span>VLAN</span>
                          <i :class="sortIcon('vlans')" />
                        </button>
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    <tr
                        v-for="data in pageItems"
                        :key="`${data.device}-${data.interface.name}-${data.interface.savedTime}`"
                        class="border-b border-gray-200/60 align-top transition hover:bg-white/70 dark:border-gray-700/60 dark:hover:bg-gray-900/50"
                    >
                      <td class="px-4 py-3">
                        <router-link :to="'/device/' + data.device" target="_blank" rel="noopener noreferrer">
                          <Button text icon="pi pi-box" class="!rounded-2xl max-w-full" :label="data.device" />
                        </router-link>
                      </td>

                      <td class="px-4 py-3">
                        <router-link
                            :to="'/device/' + data.device + '?port=' + data.interface.name"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="inline-flex items-center rounded-xl bg-indigo-100 px-3 py-1.5 font-mono text-sm text-indigo-900 transition hover:bg-indigo-200 dark:bg-indigo-500/20 dark:text-indigo-100 dark:hover:bg-indigo-500/30"
                        >
                          {{ data.interface.name }}
                        </router-link>
                      </td>

                      <td class="px-4 py-3">
                        <div :class="statusClass(data.interface.status)" class="inline-flex min-w-[8rem] items-center justify-center gap-2 rounded-xl px-3 py-2 text-center text-sm font-medium">
                          <span>{{ data.interface.status }}</span>
                          <i class="pi pi-clock text-xs" />
                        </div>
                      </td>

                      <td class="px-4 py-3">
                        <div class="font-mono text-sm leading-relaxed text-gray-800 dark:text-gray-200" v-html="markDescription(data.interface.description)" />
                      </td>

                      <td class="px-4 py-3">
                        <Comment :interface="getInterface(data)" :markedText="lastPattern" :device-name="data.device"/>
                      </td>

                      <td class="px-4 py-3">
                        <button
                            type="button"
                            class="font-mono text-indigo-600 transition hover:underline dark:text-indigo-400"
                            @click="toggleVlansList($event, data.interface)"
                        >
                          {{ truncateVlans(data.interface.vlans) }}
                        </button>
                      </td>
                    </tr>

                    <tr v-if="!pageItems.length">
                      <td colspan="6" class="px-4 py-10 text-center">
                        <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">По фильтрам ничего не найдено</div>
                        <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Измените фильтры или сбросьте их.</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-if="filteredInterfaces.length > rows" class="p-3">
                <Paginator
                    :rows="rows"
                    :totalRecords="filteredInterfaces.length"
                    :first="page * rows"
                    :rowsPerPageOptions="rowsPerPageOptions"
                    @page="onPage"
                    :pt="{
                      root: { class: 'rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-2' }
                    }"
                />
              </div>
            </div>
          </div>
        </section>

        <div
            v-else
            class="rounded-[2rem] border border-dashed border-gray-200/80 bg-white/70 px-6 py-12 text-center backdrop-blur dark:border-gray-700/60 dark:bg-gray-900/30"
        >
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">
            По паттерну
            <code class="mx-1 rounded-lg bg-amber-100/90 px-2 py-0.5 font-mono dark:bg-amber-900/40">{{ lastPattern }}</code>
            совпадений нет
          </h2>
        </div>
      </template>
    </div>
  </div>

  <Popover
      ref="vlansList"
      :pt="{
        root: {
          class: 'before:!hidden overflow-hidden rounded-2xl border border-gray-200/80 dark:border-gray-700/60 bg-white/95 dark:bg-gray-900/80 dark:backdrop-blur-xl shadow-lg dark:!ring-1 dark:!ring-white/5',
        },
        content: { class: '!p-4 max-w-md' },
      }"
  >
    <div class="border-b border-gray-200/70 pb-3 text-xs text-gray-500 dark:border-gray-700/60 dark:text-gray-400">
      <i class="pi pi-clock me-2 text-sm"/>
      {{ selectedVlansTime }}
    </div>
    <div class="mt-3 whitespace-pre-wrap break-all font-mono text-sm text-gray-800 dark:text-gray-100">
      {{ selectedVlans }}
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
        comments: "",
        vlans: "",
      },
      sortState: {
        key: null as SortKey | null,
        dir: "asc" as SortDir,
      },
    };
  },
  computed: {
    hasActiveFilters(): boolean {
      return Boolean(
          this.filters.device ||
          this.filters.port ||
          this.filters.status ||
          this.filters.description ||
          this.filters.comments ||
          this.filters.vlans
      );
    },
    filteredInterfaces(): InterfaceDescriptionMatchResult[] {
      const device = this.filters.device.trim().toLowerCase();
      const port = this.filters.port.trim().toLowerCase();
      const status = (this.filters.status || "").trim().toLowerCase();
      const description = this.filters.description.trim().toLowerCase();
      const comments = this.filters.comments.trim().toLowerCase();
      const vlans = this.filters.vlans.trim().toLowerCase();

      return this.interfaces.filter((item) => {
        const commentsText = item.comments.map((comment) => comment.text).join(" ").toLowerCase();
        if (device && !item.device.toLowerCase().includes(device)) return false;
        if (port && !item.interface.name.toLowerCase().includes(port)) return false;
        if (status && item.interface.status.toLowerCase() !== status) return false;
        if (description && !item.interface.description.toLowerCase().includes(description)) return false;
        if (comments && !commentsText.includes(comments)) return false;
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
      };
    },
    searchDescription() {
      if (this.pattern.length < 2) return;
      this.waitResult = true;
      this.page = 0;

      this.$router.replace({query: {...this.$route.query, pattern: this.pattern}});

      findInterfacesByDescription(this.pattern, this.isRegexPattern)
          .then(
              (data) => {
                this.interfaces = data;
                this.lastPattern = this.pattern;
                this.waitResult = false;
              },
              () => this.waitResult = false
          )
          .catch(() => this.waitResult = false);
    },
    markDescription(desc: string): string {
      return markText(desc, this.lastPattern);
    },
    statusClass(status: string): string {
      const normalized = status.toLowerCase();
      if (normalized === "admin down") return "bg-red-200 text-red-950 dark:bg-red-500/20 dark:text-red-100";
      if (normalized === "notpresent" || normalized === "nopresent") return "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-100";
      if (normalized === "dormant") return "bg-amber-100 text-amber-950 dark:bg-amber-500/20 dark:text-amber-100";
      if (normalized !== "down") return "bg-emerald-100 text-emerald-950 dark:bg-emerald-500/20 dark:text-emerald-100";
      return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200";
    },
    truncateVlans(vlans: string): string {
      if (vlans.length > 24) return vlans.slice(0, 22) + "...";
      return vlans;
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
    sortIcon(key: SortKey): string {
      if (this.sortState.key !== key) return "pi pi-sort-alt";
      return this.sortState.dir === "asc" ? "pi pi-sort-amount-up-alt" : "pi pi-sort-amount-down";
    },
    clearTableState() {
      this.filters.device = "";
      this.filters.port = "";
      this.filters.status = null;
      this.filters.description = "";
      this.filters.comments = "";
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
