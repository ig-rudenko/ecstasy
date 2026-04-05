<script setup lang="ts">
import {computed, ref, watch} from "vue";
import PinDevice from "@/components/PinDevice.vue";
import pinnedDevices from "@/services/pinnedDevices";
import {Device} from "@/services/devices";

type ModelGroup = { label: string; items: string[] }
type SortKey = "ip" | "name" | "vendor" | "model" | "group"
type SortDir = "asc" | "desc"

const props = defineProps<{
  devices: Device[]
  vendors: string[]
  models: ModelGroup[]
  groups: string[]
  globalSearch: string
  selectedDeviceIds: number[]
}>();

const emit = defineEmits<{
  (e: "update:data"): void
  (e: "filter:devices", devices: Device[]): void
  (e: "filter:clear"): void
  (e: "update:selectedDeviceIds", deviceIds: number[]): void
}>();

const search = ref<string>((props.globalSearch || "").trim());
const vendorFilter = ref<string | null>(null);
const modelFilter = ref<string | null>(null);
const groupFilter = ref<string | null>(null);
const page = ref(0);
const rows = ref(50);
const sortKey = ref<SortKey | null>(null);
const sortDir = ref<SortDir>("asc");

watch(() => props.globalSearch, (value) => {
  search.value = (value || "").trim();
});

const pinned = computed(() => pinnedDevices);
const selectionSet = computed(() => new Set(props.selectedDeviceIds));

/**
 * Returns a vendor color.
 */
function stringToColour(str: string): string {
  if (!str) return "";
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.toLowerCase().charCodeAt(i) + ((hash << 5) - hash);
  }
  const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
  return "#" + "00000".substring(0, 6 - c.length) + c;
}

const filteredModelGroups = computed<ModelGroup[]>(() => {
  if (vendorFilter.value) {
    return props.models.filter((group) => group.label === vendorFilter.value);
  }
  return props.models;
});

const filteredDevices = computed<Device[]>(() => {
  let list = props.devices;
  const query = search.value.toLowerCase();

  if (query) {
    list = list.filter((device) => device.name.toLowerCase().includes(query) || device.ip.includes(query));
  }
  if (vendorFilter.value) list = list.filter((device) => device.vendor === vendorFilter.value);
  if (modelFilter.value) list = list.filter((device) => device.model === modelFilter.value);
  if (groupFilter.value) list = list.filter((device) => device.group === groupFilter.value);

  const output = [...list];
  if (!sortKey.value) {
    return output;
  }

  const dir = sortDir.value === "asc" ? 1 : -1;
  output.sort((a, b) => String(a[sortKey.value!] || "").localeCompare(String(b[sortKey.value!] || "")) * dir);
  return output;
});

watch(filteredDevices, (devices) => {
  emit("filter:devices", devices);
  if (page.value * rows.value >= devices.length) {
    page.value = 0;
  }
}, {immediate: true});

const pageStart = computed(() => page.value * rows.value);
const pageEnd = computed(() => Math.min(pageStart.value + rows.value, filteredDevices.value.length));
const pageItems = computed(() => filteredDevices.value.slice(pageStart.value, pageEnd.value));

const allFilteredSelected = computed(() => (
    filteredDevices.value.length > 0 && filteredDevices.value.every((device) => selectionSet.value.has(device.id!))
));

/**
 * Updates sorting for the requested column.
 */
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

/**
 * Returns a sort icon class.
 */
function sortIcon(key: SortKey): string {
  if (sortKey.value !== key) return "pi pi-sort-alt";
  return sortDir.value === "asc" ? "pi pi-sort-amount-up-alt" : "pi pi-sort-amount-down";
}

/**
 * Clears all active filters.
 */
function clearFilters(): void {
  emit("filter:clear");
  search.value = "";
  vendorFilter.value = null;
  modelFilter.value = null;
  groupFilter.value = null;
  sortKey.value = null;
  sortDir.value = "asc";
  page.value = 0;
}

/**
 * Emits a reload request.
 */
function updateData(): void {
  clearFilters();
  emit("update:data");
}

/**
 * Toggles a single device selection.
 */
function toggleDevice(deviceId: number): void {
  const next = new Set(props.selectedDeviceIds);
  if (next.has(deviceId)) {
    next.delete(deviceId);
  } else {
    next.add(deviceId);
  }
  emit("update:selectedDeviceIds", [...next]);
}

/**
 * Selects all currently filtered devices.
 */
function selectAllFiltered(): void {
  const next = new Set(props.selectedDeviceIds);
  filteredDevices.value.forEach((device) => next.add(device.id!));
  emit("update:selectedDeviceIds", [...next]);
}

/**
 * Clears all current selection.
 */
function clearSelection(): void {
  emit("update:selectedDeviceIds", []);
}
</script>

<template>
  <div
      class="overflow-hidden rounded-[1.75rem] border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40">
    <div class="border-b border-gray-200/70 p-4 dark:border-gray-700/70">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div class="flex flex-wrap items-center gap-2">
            <Button @click="updateData" icon="pi pi-refresh" severity="secondary" outlined size="small"
                    class="rounded-2xl!"/>
            <Button @click="selectAllFiltered" icon="pi pi-check-square" severity="contrast" size="small"
                    label="Выделить все" class="rounded-2xl!"/>
            <Button @click="clearSelection" icon="pi pi-times-circle" severity="secondary" outlined size="small"
                    label="Снять выделение" class="rounded-2xl!"/>
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

          <div class="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
            <span>Строк на странице: <strong>50</strong></span>
            <span>Выбрано: <strong>{{ selectedDeviceIds.length }}</strong></span>
            <span v-if="allFilteredSelected"
                  class="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
              Весь отфильтрованный список выделен
            </span>
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div class="min-w-0">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Вендор
            </div>
            <Select v-model="vendorFilter" :options="vendors" placeholder="Все" class="w-full rounded-2xl"
                    :showClear="true" scroll-height="300px">
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
            <Select v-model="groupFilter" :options="groups" placeholder="Все" class="w-full rounded-2xl"
                    :showClear="true" scroll-height="300px">
              <template #option="slotProps">
                <div class="font-mono">{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>

          <div class="min-w-0">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Поиск</div>
            <IconField>
              <InputIcon class="pi pi-search"/>
              <InputText v-model.trim="search" placeholder="Имя или IP" fluid/>
            </IconField>
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-[980px] w-full text-sm">
        <thead class="border-b border-gray-200/70 bg-gray-50/80 dark:border-gray-700/70 dark:bg-gray-900/70">
        <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
          <th class="px-4 py-3 text-left font-semibold">
            <Checkbox :modelValue="allFilteredSelected" :binary="true"
                      @update:modelValue="allFilteredSelected ? clearSelection() : selectAllFiltered()"/>
          </th>
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
            :class="selectionSet.has(dev.id!) ? 'bg-sky-50/60 dark:bg-sky-950/20' : ''"
            class="border-b border-gray-200/60 transition hover:bg-white/70 dark:border-gray-700/60 dark:hover:bg-gray-900/50"
        >
          <td class="px-4 py-3">
            <Checkbox :modelValue="selectionSet.has(dev.id!)" :binary="true"
                      @update:modelValue="toggleDevice(dev.id!)"/>
          </td>

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
            <div class="group/device-name flex items-center gap-2 font-mono">
              <router-link :to="'/device/' + dev.name">
                <Button text icon="pi pi-box" :label="dev.name" class="rounded-2xl! hover:shadow-sm"/>
              </router-link>
              <span :class="{ 'opacity-100!': pinned.isPinned(dev.name) }"
                    class="opacity-50 sm:opacity-0 transition group-hover/device-name:opacity-100">
                <PinDevice :device="dev"/>
              </span>
            </div>
          </td>

          <td class="px-4 py-3">
            <button
                v-if="dev.vendor"
                class="inline-flex items-center gap-2 rounded-xl px-2 py-1 transition hover:bg-white/70 dark:hover:bg-gray-900/40 cursor-pointer"
                @click="vendorFilter = dev.vendor"
            >
              <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: stringToColour(dev.vendor) }"/>
              <span class="font-mono text-gray-900 dark:text-gray-100">{{ dev.vendor }}</span>
            </button>
          </td>

          <td class="px-4 py-3">
            <div class="font-mono text-gray-900 dark:text-gray-100">{{ dev.model || "—" }}</div>
          </td>

          <td class="px-4 py-3">
            <div class="font-mono text-gray-900 dark:text-gray-100">{{ dev.group || "—" }}</div>
          </td>
        </tr>

        <tr v-if="!pageItems.length">
          <td colspan="6" class="px-4 py-10 text-center">
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">Оборудование не найдено</div>
            <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Измените поиск или сбросьте фильтры.</div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <div v-if="filteredDevices.length > 0" class="p-3">
      <Paginator
          :rows="rows"
          :totalRecords="filteredDevices.length"
          :first="pageStart"
          :pageLinkSize="3"
          @page="(e: any) => { page = e.page; rows = 50; }"
          :pt="{
            root: { class: 'rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-2' }
          }"
      />
    </div>
  </div>
</template>
