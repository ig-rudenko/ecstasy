<script setup lang="ts">
import {computed, ref, watch} from "vue";
import pinnedDevices from "@/services/pinnedDevices.ts";
import PinDevice from "@/components/PinDevice.vue";
import InterfacesWorkload from "./InterfacesWorkload.vue";
import {Device} from "@/services/devices";

type ModelGroup = { label: string; items: string[] }
type SortKey = "ip" | "name" | "interfaces_count.abons_up" | "vendor" | "model" | "group"
type SortDir = "asc" | "desc"

const props = defineProps<{
  devices: Device[]
  vendors: string[]
  models: ModelGroup[]
  groups: string[]
  globalSearch: string
}>();

const emit = defineEmits<{
  (e: "update:data"): void
  (e: "filter:devices", devices: Device[]): void
  (e: "filter:clear"): void
}>();

const search = ref<string>((props.globalSearch || "").trim());
watch(() => props.globalSearch, (v) => {
  search.value = (v || "").trim();
});

const vendorFilter = ref<string | null>(null);
const modelFilter = ref<string | null>(null);
const groupFilter = ref<string | null>(null);
const workloadRange = ref<[number, number]>([0, 1000]);

const rowsPerPageOptions = [10, 20, 50] as const;
const rows = ref<number>(50);
const page = ref<number>(0);

const sortKey = ref<SortKey | null>(null);
const sortDir = ref<SortDir>("asc");

const pinned = computed(() => pinnedDevices);
const hasInterfacesCount = computed(() => !!props.devices?.length && !!(props.devices as any)[0]?.interfaces_count);

const filteredModelGroups = computed<ModelGroup[]>(() => {
  if (vendorFilter.value) {
    return props.models.filter(g => g.label === vendorFilter.value);
  }
  return props.models;
});

function getAbonsUp(dev: Device): number {
  // @ts-ignore
  return dev?.interfaces_count?.abons_up ?? 0;
}

function stringToColour(str: string): string {
  if (!str) return "";
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.toLowerCase().charCodeAt(i) + ((hash << 5) - hash);
  }
  const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
  return "#" + "00000".substring(0, 6 - c.length) + c;
}

function levenshtein(a: string, b: string): number {
  a = a.toLowerCase();
  b = b.toLowerCase();
  const matrix: number[][] = [];
  for (let i = 0; i <= b.length; i++) matrix[i] = [i];
  for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  return matrix[b.length][a.length];
}

function similarity(a: string, b: string): number {
  const longer = a.length > b.length ? a : b;
  const shorter = a.length > b.length ? b : a;
  const distance = levenshtein(longer, shorter);
  return (longer.length - distance) / longer.length;
}

function smartSearch(searchStr: string, list: string[], minSimilarity = 0.5): string[] {
  const s = searchStr.toLowerCase();
  return list
    .map(item => {
      const itemLower = item.toLowerCase();
      let score = 0;
      if (s.includes(itemLower) || itemLower.includes(s)) {
        score = 1;
      } else {
        const words = s.split(/\s+/).filter(Boolean);
        const wordScores = words.map(w => similarity(w, itemLower));
        score = Math.max(...wordScores);
      }
      return { item, score };
    })
    .filter(r => r.score >= minSimilarity)
    .sort((a, b) => b.score - a.score)
    .map(r => r.item);
}

const searchedDevices = computed<Device[]>(() => {
  const s = search.value.trim();
  if (!s) return props.devices;

  const defaultFiltered = props.devices.filter(d => {
    const name = (d.name || "").toLowerCase();
    return name.includes(s.toLowerCase()) || (d.ip || "").includes(s);
  });
  if (defaultFiltered.length) return defaultFiltered;

  const names = props.devices.map(d => d.name);
  const matched = smartSearch(s, names, 0.7);
  const out: Device[] = [];
  for (const name of matched) {
    const dev = props.devices.find(d => d.name === name);
    if (dev) out.push({ ...dev });
  }
  return out;
});

const filteredDevicesUnsorted = computed<Device[]>(() => {
  let list = searchedDevices.value;

  if (vendorFilter.value) list = list.filter(d => d.vendor === vendorFilter.value);
  if (modelFilter.value) list = list.filter(d => d.model === modelFilter.value);
  if (groupFilter.value) list = list.filter(d => d.group === groupFilter.value);

  if (hasInterfacesCount.value) {
    const [min, max] = workloadRange.value;
    list = list.filter(d => {
      const v = getAbonsUp(d);
      return v >= min && v <= max;
    });
  }

  return list;
});

const filteredDevices = computed<Device[]>(() => {
  const list = [...filteredDevicesUnsorted.value];
  if (!sortKey.value) return list;

  const key = sortKey.value;
  const dir = sortDir.value === "asc" ? 1 : -1;
  list.sort((a, b) => {
    const av = key === "interfaces_count.abons_up" ? getAbonsUp(a) : (a as any)[key];
    const bv = key === "interfaces_count.abons_up" ? getAbonsUp(b) : (b as any)[key];
    if (av == null && bv == null) return 0;
    if (av == null) return 1 * dir;
    if (bv == null) return -1 * dir;
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
    return String(av).localeCompare(String(bv)) * dir;
  });
  return list;
});

const total = computed(() => filteredDevices.value.length);
const paginatorPosition = computed<"top" | "bottom" | "both" | undefined>(() => {
  if (total.value > 10) return "both";
  if (total.value > 0) return "top";
  return undefined;
});

const pageStart = computed(() => page.value * rows.value);
const pageEnd = computed(() => Math.min(pageStart.value + rows.value, total.value));
const pageItems = computed<Device[]>(() => filteredDevices.value.slice(pageStart.value, pageEnd.value));

watch(filteredDevicesUnsorted, (v) => {
  emit("filter:devices", v);
  if (pageStart.value >= v.length) page.value = 0;
});

function clearFilters(): void {
  emit("filter:clear");
  search.value = "";
  vendorFilter.value = null;
  modelFilter.value = null;
  groupFilter.value = null;
  workloadRange.value = [0, 1000];
  sortKey.value = null;
  sortDir.value = "asc";
  page.value = 0;
}

function updateData(): void {
  clearFilters();
  emit("update:data");
}

function toggleSort(key: SortKey): void {
  if (sortKey.value !== key) {
    sortKey.value = key;
    sortDir.value = "asc";
    return;
  }
  if (sortDir.value === "asc") {
    sortDir.value = "desc";
  } else {
    sortKey.value = null;
    sortDir.value = "asc";
  }
}

function exportCSV(): void {
  const rowsToExport = filteredDevicesUnsorted.value;
  const header = ["ip", "name", "abons_up", "vendor", "model", "group"];
  const lines = [header.join(",")];
  for (const d of rowsToExport) {
    const row = [
      d.ip ?? "",
      d.name ?? "",
      String(getAbonsUp(d)),
      d.vendor ?? "",
      d.model ?? "",
      d.group ?? "",
    ].map(v => `"${String(v).replaceAll('\"', '\"\"')}"`);
    lines.push(row.join(","));
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "devices.csv";
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur overflow-hidden">
    <div class="p-4 border-b border-gray-200/70 dark:border-gray-700/70">
      <div class="flex flex-col gap-3">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div class="flex flex-wrap items-center gap-2">
            <Button @click="updateData" icon="pi pi-refresh" severity="secondary" outlined size="small"
                    v-tooltip.bottom="'Обновить данные и сбросить фильтры'"/>
            <Button @click="exportCSV" icon="pi pi-file-excel" severity="success" outlined size="small"
                    v-tooltip.bottom="'Экспорт по фильтру (без сортировки)'" label="CSV"/>
            <Button v-if="vendorFilter || modelFilter || groupFilter || sortKey"
                    @click="clearFilters" icon="pi pi-filter-slash" severity="secondary" outlined size="small" label="Сбросить"/>
          </div>
          <div class="text-sm font-mono text-gray-600 dark:text-gray-300">
            {{ total }} строк
          </div>
        </div>

        <div class="grid gap-3 lg:grid-cols-12">
          <div class="lg:col-span-4">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Вендор</div>
            <Select v-model="vendorFilter" :options="vendors" placeholder="Все" class="w-full"
                    :showClear="true" scroll-height="300px">
              <template #option="slotProps">
                <div class="flex items-center gap-2">
                  <span class="h-2.5 w-2.5 rounded-full" :style="{backgroundColor: stringToColour(slotProps.option)}"/>
                  <span class="font-mono">{{ slotProps.option }}</span>
                </div>
              </template>
            </Select>
          </div>

          <div class="lg:col-span-4">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Модель</div>
            <Select v-model="modelFilter" :options="filteredModelGroups" optionGroupLabel="label" optionGroupChildren="items"
                    filter :showClear="true" placeholder="Все" class="w-full" scroll-height="350px">
              <template #optiongroup="slotProps">
                <div class="flex items-center gap-2">
                  <span class="h-2.5 w-2.5 rounded-full" :style="{backgroundColor: stringToColour(slotProps.option.label)}"/>
                  <span class="font-mono">{{ slotProps.option.label }}</span>
                </div>
              </template>
              <template #option="slotProps">
                <div class="font-mono">{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>

          <div class="lg:col-span-4">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Группа</div>
            <Select v-model="groupFilter" :options="groups" placeholder="Все" class="w-full"
                    :showClear="true" scroll-height="300px">
              <template #option="slotProps">
                <div class="font-mono">{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>

          <div v-if="hasInterfacesCount" class="lg:col-span-6">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Абоненты (от / до)</div>
            <div class="flex items-center gap-2">
              <InputNumber v-model="workloadRange[0]" input-class="w-full" class="w-full" />
              <span class="text-gray-400">—</span>
              <InputNumber v-model="workloadRange[1]" input-class="w-full" class="w-full" />
            </div>
          </div>

          <div class="lg:col-span-6">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Строк на страницу</div>
            <Select v-model="rows" :options="(rowsPerPageOptions as unknown as number[])" class="w-full" />
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-[900px] w-full text-sm">
        <thead class="bg-white/80 dark:bg-gray-900/70 backdrop-blur border-b border-gray-200/70 dark:border-gray-700/70">
        <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
          <th class="text-left px-4 py-3 font-semibold cursor-pointer select-none" @click="toggleSort('ip')">IP</th>
          <th class="text-left px-4 py-3 font-semibold cursor-pointer select-none" @click="toggleSort('name')">Имя</th>
          <th v-if="hasInterfacesCount" class="text-left px-4 py-3 font-semibold cursor-pointer select-none" @click="toggleSort('interfaces_count.abons_up')">
            Абоненты
          </th>
          <th class="text-left px-4 py-3 font-semibold cursor-pointer select-none" @click="toggleSort('vendor')">Вендор</th>
          <th class="text-left px-4 py-3 font-semibold cursor-pointer select-none" @click="toggleSort('model')">Модель</th>
          <th class="text-left px-4 py-3 font-semibold cursor-pointer select-none" @click="toggleSort('group')">Группа</th>
        </tr>
        </thead>

        <tbody>
        <tr v-for="dev in pageItems" :key="dev.ip"
            class="border-b border-gray-200/60 dark:border-gray-700/60 hover:bg-white/60 dark:hover:bg-gray-900/40 transition">
          <td class="px-4 py-3">
            <div class="flex items-center gap-3 group/ip">
              <div class="font-mono text-gray-900 dark:text-gray-100">{{ dev.ip }}</div>
              <a v-if="(dev as any).console_url" :href="(dev as any).console_url" target="_blank"
                 class="opacity-0 group-hover/ip:opacity-100 text-indigo-600 dark:text-indigo-300">
                <i class="pi pi-desktop"/>
              </a>
            </div>
          </td>

          <td class="px-4 py-3">
            <div class="flex items-center gap-2 group/device-name">
              <router-link :to="'/device/'+dev.name">
                <Button text icon="pi pi-box" :label="dev.name"/>
              </router-link>
              <span class="opacity-0 group-hover/device-name:opacity-100"
                    :class="{'opacity-100!': pinned.isPinned(dev.name)}">
                <PinDevice :device="dev"/>
              </span>
            </div>
            <InterfacesWorkload class="p-2" :dev="dev"/>
          </td>

          <td v-if="hasInterfacesCount" class="px-4 py-3 font-mono text-gray-900 dark:text-gray-100">
            {{ getAbonsUp(dev) }}
          </td>

          <td class="px-4 py-3">
            <button v-if="dev.vendor"
                    class="inline-flex items-center gap-2 rounded-xl px-2 py-1 hover:bg-white/70 dark:hover:bg-gray-900/40 transition"
                    @click="vendorFilter = dev.vendor">
              <span class="h-2.5 w-2.5 rounded-full" :style="{backgroundColor: stringToColour(dev.vendor)}"/>
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.vendor }}</span>
            </button>
          </td>

          <td class="px-4 py-3">
            <div v-if="dev.model" class="flex items-center gap-2">
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.model }}</span>
              <Button v-if="modelFilter !== dev.model" @click="modelFilter = dev.model" icon="pi pi-filter" size="small" outlined />
              <Button v-else @click="modelFilter = null" icon="pi pi-filter-slash" size="small" outlined />
            </div>
          </td>

          <td class="px-4 py-3">
            <div v-if="dev.group" class="flex items-center gap-2">
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.group }}</span>
              <Button v-if="groupFilter !== dev.group" @click="groupFilter = dev.group" icon="pi pi-filter" size="small" outlined />
              <Button v-else @click="groupFilter = null" icon="pi pi-filter-slash" size="small" outlined />
            </div>
          </td>
        </tr>

        <tr v-if="!pageItems.length">
          <td :colspan="hasInterfacesCount ? 6 : 5" class="px-4 py-10 text-center">
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">Оборудование не найдено</div>
            <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Измените поиск или сбросьте фильтры.</div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <div v-if="paginatorPosition" class="p-3">
      <Paginator :rows="rows" :totalRecords="total" :first="pageStart"
                 :rowsPerPageOptions="(rowsPerPageOptions as unknown as number[])"
                 @page="(e: any) => { page = e.page; rows = e.rows; }"
                 :pt="{
                   root: { class: 'rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-2' }
                 }"/>
    </div>
  </div>
</template>