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
const rows = ref<number>(10);
const page = ref<number>(0);
const sortKey = ref<SortKey | null>(null);
const sortDir = ref<SortDir>("asc");
const emitTimer = ref<number | null>(null);

const pinned = computed(() => pinnedDevices);
const hasInterfacesCount = computed(() => !!props.devices?.length && !!(props.devices as any)[0]?.interfaces_count);

const preparedDevices = computed(() =>
    props.devices.map((device) => ({
      ...device,
      _nameLower: (device.name || "").toLowerCase(),
      _ip: device.ip || "",
    }))
);

const filteredModelGroups = computed<ModelGroup[]>(() => {
  if (vendorFilter.value) {
    return props.models.filter((g) => g.label === vendorFilter.value);
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
  return longer.length ? (longer.length - distance) / longer.length : 0;
}

function smartSearch(searchStr: string, list: string[], minSimilarity = 0.72): string[] {
  const s = searchStr.toLowerCase();
  const words = s.split(/\s+/).filter(Boolean);
  return list
      .map((item) => {
        const itemLower = item.toLowerCase();
        let score = 0;
        if (s.includes(itemLower) || itemLower.includes(s)) {
          score = 1;
        } else if (words.length) {
          score = Math.max(...words.map((w) => similarity(w, itemLower)));
        }
        return {item, score};
      })
      .filter((r) => r.score >= minSimilarity)
      .sort((a, b) => b.score - a.score)
      .map((r) => r.item);
}

const searchedDevices = computed<Device[]>(() => {
  const s = search.value.trim();
  if (!s) return props.devices;

  const query = s.toLowerCase();
  const direct = preparedDevices.value.filter((d) => d._nameLower.includes(query) || d._ip.includes(s));
  if (direct.length || s.length < 3) return direct as unknown as Device[];

  const matched = smartSearch(s, props.devices.map((d) => d.name), 0.76);
  const out: Device[] = [];
  for (const name of matched) {
    const dev = props.devices.find((d) => d.name === name);
    if (dev) out.push(dev);
  }
  return out;
});

const filteredDevicesUnsorted = computed<Device[]>(() => {
  let list = searchedDevices.value;
  if (vendorFilter.value) list = list.filter((d) => d.vendor === vendorFilter.value);
  if (modelFilter.value) list = list.filter((d) => d.model === modelFilter.value);
  if (groupFilter.value) list = list.filter((d) => d.group === groupFilter.value);

  if (hasInterfacesCount.value) {
    const [min, max] = workloadRange.value;
    list = list.filter((d) => {
      const value = getAbonsUp(d);
      return value >= min && value <= max;
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
const pageStart = computed(() => page.value * rows.value);
const pageEnd = computed(() => Math.min(pageStart.value + rows.value, total.value));
const pageItems = computed<Device[]>(() => filteredDevices.value.slice(pageStart.value, pageEnd.value));

watch(filteredDevicesUnsorted, (value) => {
  if (emitTimer.value) clearTimeout(emitTimer.value);
  emitTimer.value = window.setTimeout(() => {
    emit("filter:devices", value);
  }, 100);
  if (pageStart.value >= value.length) page.value = 0;
}, {immediate: true});

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

function sortIcon(key: SortKey): string {
  if (sortKey.value !== key) return "pi pi-sort-alt";
  return sortDir.value === "asc" ? "pi pi-sort-amount-up-alt" : "pi pi-sort-amount-down";
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
    ].map((v) => `"${String(v).replaceAll("\"", "\"\"")}"`);
    lines.push(row.join(","));
  }
  const blob = new Blob([lines.join("\n")], {type: "text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "devices.csv";
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div
      class="overflow-hidden rounded-[1.75rem] sm:border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40">
    <div class="border-b border-gray-200/70 p-4 dark:border-gray-700/70">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex flex-wrap items-center gap-2">
            <Button @click="updateData" icon="pi pi-refresh" severity="secondary" outlined size="small"
                    class="rounded-2xl!"/>
            <Button @click="exportCSV" icon="pi pi-file-excel" severity="success" outlined size="small" label="CSV"
                    class="rounded-2xl!"/>
            <Button
                v-if="vendorFilter || modelFilter || groupFilter || sortKey"
                @click="clearFilters"
                icon="pi pi-filter-slash"
                severity="secondary"
                outlined
                size="small"
                label="Сбросить"
                class="rounded-2xl!"
            />
          </div>

        </div>

        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div class="min-w-0">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Вендор
            </div>
            <Select v-model="vendorFilter" :options="vendors" placeholder="Все" class="w-full rounded-2xl" :showClear="true"
                    scroll-height="300px">
              <template #option="slotProps">
                <div class="flex items-center gap-2">
                  <span class="h-2.5 w-2.5 rounded-full"
                        :style="{ backgroundColor: stringToColour(slotProps.option) }"/>
                  <span class="font-mono">{{ slotProps.option }}</span>
                </div>
              </template>
            </Select>
          </div>

          <div class="min-w-0">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Модель
            </div>
            <Select
                v-model="modelFilter"
                :options="filteredModelGroups"
                optionGroupLabel="label"
                optionGroupChildren="items"
                filter
                :showClear="true"
                placeholder="Все"
                class="w-full rounded-2xl"
                scroll-height="350px"
            >
              <template #optiongroup="slotProps">
                <div class="flex items-center gap-2">
                  <span class="h-2.5 w-2.5 rounded-full"
                        :style="{ backgroundColor: stringToColour(slotProps.option.label) }"/>
                  <span class="font-mono">{{ slotProps.option.label }}</span>
                </div>
              </template>
              <template #option="slotProps">
                <div class="font-mono">{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>

          <div class="min-w-0">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Группа
            </div>
            <Select v-model="groupFilter" :options="groups" placeholder="Все" class="w-full rounded-2xl" :showClear="true"
                    scroll-height="300px">
              <template #option="slotProps">
                <div class="font-mono">{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>

          <div v-if="hasInterfacesCount" class="min-w-0">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Абоненты
            </div>
            <div class="flex items-center gap-2">
              <InputNumber v-model="workloadRange[0]" input-class="w-full" class="w-full"/>
              <span class="text-gray-400">—</span>
              <InputNumber v-model="workloadRange[1]" input-class="w-full" class="w-full"/>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-240 w-full text-sm">
        <thead class="border-b border-gray-200/70 bg-gray-50/80 dark:border-gray-700/70 dark:bg-gray-900/70">
        <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
          <th class="px-4 py-3 text-left font-semibold">
            <button class="inline-flex items-center gap-2" @click="toggleSort('ip')">
              <span>IP</span>
              <i :class="sortIcon('ip')"/>
            </button>
          </th>
          <th class="px-4 py-3 text-left font-semibold">
            <button class="inline-flex items-center gap-2" @click="toggleSort('name')">
              <span>Имя</span>
              <i :class="sortIcon('name')"/>
            </button>
          </th>
          <th v-if="hasInterfacesCount" class="px-4 py-3 text-left font-semibold">
            <button class="inline-flex items-center gap-2" @click="toggleSort('interfaces_count.abons_up')">
              <span>Абоненты</span>
              <i :class="sortIcon('interfaces_count.abons_up')"/>
            </button>
          </th>
          <th class="px-4 py-3 text-left font-semibold">
            <button class="inline-flex items-center gap-2" @click="toggleSort('vendor')">
              <span>Вендор</span>
              <i :class="sortIcon('vendor')"/>
            </button>
          </th>
          <th class="px-4 py-3 text-left font-semibold">
            <button class="inline-flex items-center gap-2" @click="toggleSort('model')">
              <span>Модель</span>
              <i :class="sortIcon('model')"/>
            </button>
          </th>
          <th class="px-4 py-3 text-left font-semibold">
            <button class="inline-flex items-center gap-2" @click="toggleSort('group')">
              <span>Группа</span>
              <i :class="sortIcon('group')"/>
            </button>
          </th>
        </tr>
        </thead>

        <tbody>
        <tr
            v-for="dev in pageItems"
            :key="dev.ip"
            class="border-b border-gray-200/60 transition hover:bg-white/70 dark:border-gray-700/60 dark:hover:bg-gray-900/50"
        >
          <td class="px-4 py-3">
            <div class="group/ip flex items-center gap-3">
              <div class="font-mono text-gray-900 dark:text-gray-100">{{ dev.ip }}</div>
              <a
                  v-if="(dev as any).console_url"
                  :href="(dev as any).console_url"
                  target="_blank"
                  class="opacity-0 transition group-hover/ip:opacity-100 text-indigo-600 dark:text-indigo-300"
              >
                <i class="pi pi-desktop"/>
              </a>
            </div>
          </td>

          <td class="px-4 py-3">
            <div class="group/device-name flex items-center gap-2">
              <router-link :to="'/device/' + dev.name">
                <Button text icon="pi pi-box" :label="dev.name" class="rounded-2xl!"/>
              </router-link>
              <span :class="{ 'opacity-100!': pinned.isPinned(dev.name) }"
                    class="opacity-50 sm:opacity-0 transition group-hover/device-name:opacity-100">
                  <PinDevice :device="dev"/>
                </span>
            </div>
            <InterfacesWorkload class="px-2 pb-1" :dev="dev"/>
          </td>

          <td v-if="hasInterfacesCount" class="px-4 py-3 font-mono text-gray-900 dark:text-gray-100">
            {{ getAbonsUp(dev) }}
          </td>

          <td class="px-4 py-3">
            <button
                v-if="dev.vendor"
                class="inline-flex items-center gap-2 rounded-xl px-2 py-1 transition hover:bg-white/70 dark:hover:bg-gray-900/40 cursor-pointer border border-transparent hover:border-primary-200"
                @click="vendorFilter = dev.vendor"
            >
              <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: stringToColour(dev.vendor) }"/>
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.vendor }}</span>
            </button>
          </td>

          <td class="px-4 py-3">
            <div v-if="dev.model" class="flex items-center gap-2 group">
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.model }}</span>
              <Button v-if="modelFilter !== dev.model" @click="modelFilter = dev.model" icon="pi pi-filter" size="small"
                      outlined class="rounded-xl! opacity-0 group-hover:opacity-100"/>
              <Button v-else @click="modelFilter = null" icon="pi pi-filter-slash" size="small" outlined
                      class="rounded-xl!"/>
            </div>
          </td>

          <td class="px-4 py-3">
            <div v-if="dev.group" class="flex items-center gap-2 group">
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.group }}</span>
              <Button v-if="groupFilter !== dev.group" @click="groupFilter = dev.group" icon="pi pi-filter" size="small"
                      outlined class="rounded-xl! opacity-0 group-hover:opacity-100"/>
              <Button v-else @click="groupFilter = null" icon="pi pi-filter-slash" size="small" outlined
                      class="rounded-xl!"/>
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

    <div v-if="total > 0" class="p-3">
      <Paginator
          :rows="rows"
          :totalRecords="total"
          :first="pageStart"
          :pageLinkSize="3"
          @page="(e: any) => { page = e.page; rows = e.rows; }"
          :pt="{
            root: { class: 'rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-2' }
          }"
      />
    </div>
  </div>
</template>
