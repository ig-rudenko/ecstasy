<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref, watch} from "vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import SearchInput from "@/components/SearchInput.vue";
import CommandTemplateSelector from "@/components/deviceCommands/CommandTemplateSelector.vue";
import BulkDevicesTable from "@/pages/bulkCommands/BulkDevicesTable.vue";
import api from "@/services/api";
import devicesService, {Device} from "@/services/devices";
import errorFmt from "@/errorFmt";
import {errorToast, successToast} from "@/services/my.toast";
import {
  BulkCommandDeviceResult,
  BulkCommandTaskLaunch,
  BulkCommandTaskStatus,
  cloneCommandTemplate,
  DeviceCommandTemplate,
  executeBulkDeviceCommand,
  getBulkCommandTaskDeviceResult,
  getBulkCommandTaskStatus,
} from "@/services/deviceCommands";

interface TaskDeviceState extends BulkCommandDeviceResult {
  canRetry: boolean;
}

interface TaskSummary {
  success: number;
  error: number;
  skipped: number;
  waiting: number;
}

interface TaskHistoryEntry {
  taskId: string;
  command: DeviceCommandTemplate;
  status: string;
  progress: number;
  processed: number;
  total: number;
  launchedAt: number;
  devices: TaskDeviceState[];
  skipped: TaskDeviceState[];
}

const devices = ref<Device[]>([]);
const filteredDevices = ref<Device[]>([]);
const vendors = ref<string[]>([]);
const groups = ref<string[]>([]);
const models = ref<{ label: string; items: string[] }[]>([]);
const search = ref("");
const selectedDeviceIds = ref<number[]>([]);
const selectedCommand = ref<DeviceCommandTemplate | null>(null);
const referencePortOptions = ref<string[]>([]);
const isLoadingDevices = ref(false);
const isLaunchingTask = ref(false);
const tasks = ref<TaskHistoryEntry[]>([]);
const currentOutput = ref<TaskDeviceState | null>(null);
const outputVisible = ref(false);
let pollingTimer: number | null = null;

/**
 * Computes the current command source device.
 */
const referenceDevice = computed<Device | null>(() => {
  const devicesByPriority = [
    ...devices.value.filter((device) => selectedDeviceIds.value.includes(device.id!)),
    ...filteredDevices.value.filter((device) => !selectedDeviceIds.value.includes(device.id!)),
  ];

  return devicesByPriority.find((device) => !!device.vendor && !!device.model) || null;
});

/**
 * Returns selected devices as model objects.
 */
const selectedDevices = computed(() => {
  const selectedSet = new Set(selectedDeviceIds.value);
  return devices.value.filter((device) => selectedSet.has(device.id!));
});

/**
 * Returns selected devices count with vendor and model.
 */
const compatibleSelectedDevicesCount = computed(() => (
    selectedDevices.value.filter((device) => device.vendor && device.model).length
));

/**
 * Returns count of active tasks.
 */
const activeTasksCount = computed(() => (
    tasks.value.filter((task) => !isTaskFinished(task)).length
));

/**
 * Returns the latest task summary.
 */
const latestTaskSummary = computed<TaskSummary>(() => {
  if (!tasks.value.length) {
    return {success: 0, error: 0, skipped: 0, waiting: 0};
  }
  return getTaskSummary(tasks.value[0]);
});

/**
 * Fetches all devices for the page.
 */
async function loadDevices(): Promise<void> {
  isLoadingDevices.value = true;

  try {
    const loadedDevices = await devicesService.getDevicesList();
    devices.value = loadedDevices;
    filteredDevices.value = loadedDevices;
    buildDeviceFilters(loadedDevices);
  } finally {
    isLoadingDevices.value = false;
  }
}

/**
 * Builds filter options for table selects.
 */
function buildDeviceFilters(items: Device[]): void {
  const groupsSet = new Set<string>();
  const vendorsSet = new Set<string>();
  const modelsMap = new Map<string, Set<string>>();

  for (const device of items) {
    if (device.group) groupsSet.add(device.group);
    if (device.vendor) {
      vendorsSet.add(device.vendor);
      if (!modelsMap.has(device.vendor)) {
        modelsMap.set(device.vendor, new Set<string>());
      }
      if (device.model) {
        modelsMap.get(device.vendor)?.add(device.model);
      }
    }
  }

  groups.value = [...groupsSet].sort((left, right) => left.localeCompare(right));
  vendors.value = [...vendorsSet].sort((left, right) => left.localeCompare(right));
  models.value = [...modelsMap.entries()]
      .sort((left, right) => left[0].localeCompare(right[0]))
      .map(([label, itemsSet]) => ({
        label,
        items: [...itemsSet].sort((left, right) => left.localeCompare(right)),
      }));
}

/**
 * Loads interface names for the reference device.
 */
async function loadReferenceDeviceInterfaces(): Promise<void> {
  referencePortOptions.value = [];

  if (!referenceDevice.value) {
    return;
  }

  try {
    const response = await api.get<{ interfaces: { name: string }[] }>(
        `/api/v1/devices/${referenceDevice.value.name}/interfaces?vlans=0`,
    );
    referencePortOptions.value = response.data.interfaces.map((item) => item.name);
  } catch (error: any) {
    console.error(error);
  }
}

watch(referenceDevice, () => {
  selectedCommand.value = null;
  loadReferenceDeviceInterfaces();
}, {immediate: true});

/**
 * Opens an output dialog for a device result.
 */
function showDeviceOutput(device: TaskDeviceState): void {
  currentOutput.value = device;
  outputVisible.value = true;
}

/**
 * Returns whether a task is completed.
 */
function isTaskFinished(task: TaskHistoryEntry): boolean {
  return getTaskSummary(task).waiting === 0;
}

/**
 * Returns summary counters for a task.
 */
function getTaskSummary(task: TaskHistoryEntry): TaskSummary {
  const allDevices = [...task.devices, ...task.skipped];
  return {
    success: allDevices.filter((device) => device.status === "SUCCESS").length,
    error: allDevices.filter((device) => device.status === "ERROR").length,
    skipped: allDevices.filter((device) => device.status === "SKIPPED").length,
    waiting: allDevices.filter((device) => ["PENDING", "PROGRESS", "STARTED"].includes(device.status)).length,
  };
}

/**
 * Returns waiting devices for a task.
 */
function getWaitingDevices(task: TaskHistoryEntry): TaskDeviceState[] {
  return task.devices.filter((device) => ["PENDING", "PROGRESS", "STARTED"].includes(device.status));
}

/**
 * Creates a task entry from launch response.
 */
function createTaskEntry(response: BulkCommandTaskLaunch, command: DeviceCommandTemplate, requestedDeviceIds: number[]): TaskHistoryEntry {
  return {
    taskId: response.taskId,
    command: cloneCommandTemplate(command),
    status: "PENDING",
    progress: 0,
    processed: 0,
    total: requestedDeviceIds.length,
    launchedAt: Date.now(),
    devices: response.devices.map((device) => ({
      deviceId: device.deviceId,
      deviceName: device.deviceName,
      status: "PENDING",
      output: "",
      detail: "",
      canRetry: true,
    })),
    skipped: response.skipped.map((device) => ({
      deviceId: device.deviceId,
      deviceName: device.deviceName,
      status: "SKIPPED",
      output: "",
      detail: device.detail || "",
      canRetry: true,
    })),
  };
}

/**
 * Launches a new bulk task.
 */
async function launchTask(command: DeviceCommandTemplate, deviceIds: number[]): Promise<void> {
  isLaunchingTask.value = true;

  try {
    const response = await executeBulkDeviceCommand(command.id, deviceIds, command.context);
    tasks.value.unshift(createTaskEntry(response, command, deviceIds));
    successToast("Задача отправлена", `Оборудование в задаче: ${deviceIds.length}`);
    ensurePolling();
    await pollTasks();
  } catch (error: any) {
    console.error(error);
    errorToast("Не удалось запустить задачу", errorFmt(error));
  } finally {
    isLaunchingTask.value = false;
  }
}

/**
 * Validates current selection and launches the chosen command.
 */
async function runSelectedCommand(): Promise<void> {
  if (!selectedDeviceIds.value.length) {
    errorToast("Нет оборудования", "Выберите хотя бы одно устройство.");
    return;
  }
  if (!selectedCommand.value) {
    errorToast("Нет команды", "Выберите и заполните команду.");
    return;
  }

  await launchTask(cloneCommandTemplate(selectedCommand.value), selectedDeviceIds.value);
}

/**
 * Repeats the task command for one device.
 */
async function retryDevice(task: TaskHistoryEntry, deviceId: number): Promise<void> {
  await launchTask(cloneCommandTemplate(task.command), [deviceId]);
}

/**
 * Repeats command for all failed devices in the task.
 */
async function retryFailedDevices(task: TaskHistoryEntry): Promise<void> {
  const failedIds = task.devices.filter((device) => device.status === "ERROR").map((device) => device.deviceId);
  if (!failedIds.length) {
    return;
  }
  await launchTask(cloneCommandTemplate(task.command), failedIds);
}

/**
 * Applies task status response.
 */
function applyTaskStatus(task: TaskHistoryEntry, status: BulkCommandTaskStatus): void {
  task.status = status.status;
  task.progress = status.progress || 0;
  task.processed = status.processed || 0;
  task.total = status.total || task.total;
}

/**
 * Applies single device result to a task.
 */
function applyTaskDeviceResult(task: TaskHistoryEntry, result: BulkCommandDeviceResult): void {
  const target = task.devices.find((device) => device.deviceId === result.deviceId);
  if (!target) {
    return;
  }

  target.status = result.status;
  target.output = result.output;
  target.detail = result.detail;
}

/**
 * Polls status and resolved device outputs for all active tasks.
 */
async function pollTasks(): Promise<void> {
  const activeTasks = tasks.value.filter((task) => !isTaskFinished(task));
  if (!activeTasks.length) {
    stopPolling();
    return;
  }

  await Promise.all(activeTasks.map(async (task) => {
    try {
      const status = await getBulkCommandTaskStatus(task.taskId);
      applyTaskStatus(task, status);
    } catch (error: any) {
      console.error(error);
    }

    await Promise.all(task.devices
        .filter((device) => ["PENDING", "PROGRESS", "STARTED"].includes(device.status))
        .map(async (device) => {
          try {
            const result = await getBulkCommandTaskDeviceResult(task.taskId, device.deviceId);
            applyTaskDeviceResult(task, result);
          } catch (error: any) {
            if (error?.response?.status !== 404) {
              console.error(error);
            }
          }
        }));
  }));
}

/**
 * Starts task polling if needed.
 */
function ensurePolling(): void {
  if (pollingTimer != null) {
    return;
  }

  pollingTimer = window.setInterval(() => {
    pollTasks();
  }, 2500);
}

/**
 * Stops background task polling.
 */
function stopPolling(): void {
  if (pollingTimer != null) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

/**
 * Returns badge severity by device state.
 */
function getDeviceSeverity(status: string): "success" | "danger" | "warn" | "secondary" | "info" | "contrast" {
  switch (status) {
    case "SUCCESS":
      return "success";
    case "ERROR":
      return "danger";
    case "SKIPPED":
      return "warn";
    default:
      return "info";
  }
}

onMounted(() => {
  loadDevices();
});

onBeforeUnmount(() => {
  stopPolling();
});
</script>

<template>
  <Header/>

  <div class="mx-auto px-2 py-2 sm:px-4 sm:py-6 xl:px-8">
    <div class="flex flex-col gap-6">
      <section
          class="relative overflow-hidden rounded-4xl border border-gray-200/70 bg-white/80 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45">
        <div
            class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.16),transparent_26%),radial-gradient(circle_at_80%_18%,rgba(34,197,94,0.12),transparent_22%),radial-gradient(circle_at_52%_100%,rgba(59,130,246,0.12),transparent_25%)]"/>

        <div class="relative p-5 sm:p-8">
          <div class="flex flex-col gap-8 2xl:flex-row 2xl:items-start 2xl:justify-between">
            <div class="max-w-5xl">
              <div
                  class="inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-sky-700 dark:text-sky-300">
                Bulk Command Center
              </div>

              <h1 class="mt-5 text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl">
                Массовое выполнение команд
              </h1>

              <p class="mt-3 max-w-4xl text-sm leading-7 text-gray-600 dark:text-gray-300 sm:text-base">
                Выберите оборудование галочками, задайте шаблон команды и наблюдайте прогресс выполнения в реальном
                времени.
                Результаты по каждому устройству сохраняются отдельно и доступны для повторного запуска.
              </p>
            </div>

            <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div
                  class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Всего
                </div>
                <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ devices.length }}</div>
                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Доступных устройств</div>
              </div>
              <div
                  class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">
                  Выбрано
                </div>
                <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">{{
                    selectedDeviceIds.length
                  }}
                </div>
                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Устройств для задачи</div>
              </div>
              <div
                  class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Активных
                  задач
                </div>
                <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ activeTasksCount }}</div>
                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Сейчас выполняются</div>
              </div>
              <div
                  class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">
                  Последняя задача
                </div>
                <div class="mt-2 flex flex-wrap gap-2 text-sm">
                  <Tag severity="success" :value="`OK ${latestTaskSummary.success}`"/>
                  <Tag severity="danger" :value="`ERR ${latestTaskSummary.error}`"/>
                  <Tag severity="warn" :value="`SKIP ${latestTaskSummary.skipped}`"/>
                  <Tag severity="info" :value="`WAIT ${latestTaskSummary.waiting}`"/>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="md:grid gap-6 xl:grid-cols-2">
        <div
            class="rounded-4xl border border-gray-200/70 bg-white/80 p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6">
          <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div class="w-full md:max-w-xl">
              <SearchInput
                  @update:modelValue="(value: string) => search = value"
                  :active-mode="true"
                  :init-search="search"
                  placeholder="Поиск по имени или IP адресу"
              />
            </div>
            <div
                class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-2 font-mono text-sm text-gray-600 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300">
              Отфильтровано: <span class="font-semibold text-gray-900 dark:text-gray-100">{{
                filteredDevices.length
              }}</span>
            </div>
          </div>

          <div class="mt-5">
            <BulkDevicesTable
                :global-search="search"
                :devices="devices"
                :groups="groups"
                :vendors="vendors"
                :models="models"
                :selected-device-ids="selectedDeviceIds"
                @filter:devices="(items: Device[]) => filteredDevices = items"
                @filter:clear="() => search = ''"
                @update:data="loadDevices"
                @update:selectedDeviceIds="(ids: number[]) => selectedDeviceIds = ids"
            />
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <div
              class="rounded-4xl border border-gray-200/70 bg-white/80 p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Параметры запуска</div>
                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Опорное устройство для списка команд:
                  <span class="font-mono text-gray-900 dark:text-gray-100">{{
                      referenceDevice?.name || "не выбрано"
                    }}</span>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
                <Tag severity="contrast" :value="`Выбрано ${selectedDeviceIds.length}`"/>
                <Tag severity="info" :value="`Совместимо ${compatibleSelectedDevicesCount}`"/>
              </div>
            </div>

            <div class="mt-5">
              <CommandTemplateSelector
                  v-model="selectedCommand"
                  :device-name="referenceDevice?.name || null"
                  :port-options="referencePortOptions"
                  mode="select"
                  title="Команда"
                  description="Команды загружаются по опорному устройству. Оборудование без модели или вендора будет пропущено сервером."
                  empty-title="Сначала выберите подходящее оборудование"
                  empty-description="Нужно хотя бы одно устройство с указанными вендором и моделью."
              />
            </div>

            <div
                class="mt-5 rounded-3xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/50">
              <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {{ selectedCommand?.name || "Команда не выбрана" }}
                  </div>
                  <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    {{
                      selectedCommand?.description || "Выберите шаблон команды и заполните параметры перед запуском."
                    }}
                  </div>
                </div>

                <Button
                    icon="pi pi-send"
                    label="Запустить на выбранных"
                    :loading="isLaunchingTask"
                    :disabled="!selectedCommand || !selectedDeviceIds.length || isLaunchingTask"
                    @click="runSelectedCommand"
                    class="rounded-2xl!"
                />
              </div>
            </div>
          </div>

          <div
              class="rounded-4xl border border-gray-200/70 bg-white/80 p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Задачи</div>
                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Ход выполнения, ожидание и повторные
                  запуски.
                </div>
              </div>
              <Tag severity="secondary" :value="`История ${tasks.length}`"/>
            </div>

            <div v-if="tasks.length" class="mt-5 flex flex-col gap-4">
              <Fieldset
                  v-for="task in tasks"
                  :key="task.taskId"
                  toggleable
                  class="overflow-hidden rounded-3xl border border-gray-200/80 bg-gray-50/80 dark:border-gray-700/80 dark:bg-gray-800/50"
              >
                <template #legend="{ toggleCallback }">
                  <div class="flex w-full flex-wrap items-center gap-3 px-2 py-1">
                    <Button text rounded icon="pi pi-angle-down" @click="toggleCallback"/>
                    <div class="min-w-0 flex-1">
                      <div class="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">{{
                          task.command.name
                        }}
                      </div>
                      <div class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ task.taskId }}</div>
                    </div>
                    <Tag :severity="isTaskFinished(task) ? 'contrast' : 'info'" :value="task.status"/>
                  </div>
                </template>

                <div class="flex flex-col gap-4">
                  <div class="grid gap-3 md:grid-cols-4">
                    <div class="rounded-2xl bg-white/80 p-3 dark:bg-gray-900/50">
                      <div class="text-xs uppercase tracking-[0.2em] text-gray-400">Прогресс</div>
                      <div class="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">{{
                          task.progress
                        }}%
                      </div>
                      <ProgressBar :value="task.progress" class="mt-3"/>
                    </div>
                    <div class="rounded-2xl bg-white/80 p-3 dark:bg-gray-900/50">
                      <div class="text-xs uppercase tracking-[0.2em] text-gray-400">Успешно</div>
                      <div class="mt-2 text-lg font-semibold text-emerald-600">{{ getTaskSummary(task).success }}</div>
                    </div>
                    <div class="rounded-2xl bg-white/80 p-3 dark:bg-gray-900/50">
                      <div class="text-xs uppercase tracking-[0.2em] text-gray-400">Ошибки</div>
                      <div class="mt-2 text-lg font-semibold text-rose-600">{{ getTaskSummary(task).error }}</div>
                    </div>
                    <div class="rounded-2xl bg-white/80 p-3 dark:bg-gray-900/50">
                      <div class="text-xs uppercase tracking-[0.2em] text-gray-400">Ожидают</div>
                      <div class="mt-2 text-lg font-semibold text-sky-600">{{ getTaskSummary(task).waiting }}</div>
                    </div>
                  </div>

                  <div class="flex flex-wrap items-center gap-2">
                    <Button
                        v-if="task.devices.some((device) => device.status === 'ERROR')"
                        icon="pi pi-refresh"
                        label="Повторить ошибки"
                        severity="danger"
                        outlined
                        class="rounded-2xl!"
                        @click="retryFailedDevices(task)"
                    />
                    <Tag severity="warn" :value="`Пропущено ${getTaskSummary(task).skipped}`"/>
                    <Tag severity="info" :value="`Обработано ${task.processed}/${task.total}`"/>
                  </div>

                  <div v-if="getWaitingDevices(task).length"
                       class="rounded-2xl border border-sky-200/80 bg-sky-50/80 p-3 dark:border-sky-900/60 dark:bg-sky-950/20">
                    <div class="text-sm font-semibold text-sky-900 dark:text-sky-200">Ожидают выполнения</div>
                    <div class="mt-2 flex flex-wrap gap-2">
                      <Tag
                          v-for="device in getWaitingDevices(task)"
                          :key="`${task.taskId}-${device.deviceId}`"
                          severity="info"
                          :value="device.deviceName"
                      />
                    </div>
                  </div>

                  <div class="overflow-x-auto">
                    <table class="min-w-[780px] w-full text-sm">
                      <thead>
                      <tr class="border-b border-gray-200/80 text-left text-xs uppercase tracking-[0.2em] text-gray-500 dark:border-gray-700/80 dark:text-gray-400">
                        <th class="px-3 py-3">Устройство</th>
                        <th class="px-3 py-3">Статус</th>
                        <th class="px-3 py-3">Детали</th>
                        <th class="px-3 py-3 text-right">Действия</th>
                      </tr>
                      </thead>
                      <tbody>
                      <tr
                          v-for="device in [...task.devices, ...task.skipped]"
                          :key="`${task.taskId}-${device.deviceId}`"
                          class="border-b border-gray-200/70 last:border-b-0 dark:border-gray-700/70"
                      >
                        <td class="px-3 py-3">
                          <div class="font-medium text-gray-900 dark:text-gray-100">{{ device.deviceName }}</div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">ID: {{ device.deviceId }}</div>
                        </td>
                        <td class="px-3 py-3">
                          <Tag :severity="getDeviceSeverity(device.status)" :value="device.status"/>
                        </td>
                        <td class="px-3 py-3">
                          <div class="max-w-xl truncate text-sm text-gray-600 dark:text-gray-300">
                            {{ device.detail || (device.output ? "Есть вывод" : "Ожидание результата") }}
                          </div>
                        </td>
                        <td class="px-3 py-3">
                          <div class="flex justify-end gap-2">
                            <Button
                                v-if="device.output"
                                icon="pi pi-file"
                                label="Вывод"
                                size="small"
                                outlined
                                class="rounded-2xl!"
                                @click="showDeviceOutput(device)"
                            />
                            <Button
                                v-if="device.canRetry"
                                icon="pi pi-refresh"
                                label="Повторить"
                                size="small"
                                severity="secondary"
                                outlined
                                class="rounded-2xl!"
                                @click="retryDevice(task, device.deviceId)"
                            />
                          </div>
                        </td>
                      </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </Fieldset>
            </div>

            <div v-else class="py-12 text-center text-sm text-gray-500 dark:text-gray-400">
              Пока нет запущенных задач
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>

  <Dialog v-model:visible="outputVisible" modal maximizable :header="currentOutput?.deviceName || 'Вывод'"
          class="w-[min(96vw,1280px)]">
    <div v-if="currentOutput" class="flex flex-col gap-4">
      <div class="flex flex-wrap items-center gap-2">
        <Tag :severity="getDeviceSeverity(currentOutput.status)" :value="currentOutput.status"/>
        <Tag severity="secondary" :value="`ID ${currentOutput.deviceId}`"/>
      </div>
      <Message v-if="currentOutput.detail && !currentOutput.output" severity="warn" class="rounded-2xl">
        {{ currentOutput.detail }}
      </Message>
      <pre
          class="max-h-[70vh] overflow-auto whitespace-pre-wrap rounded-2xl bg-gray-950 px-4 py-3 text-xs text-gray-100">{{
          currentOutput.output || "Вывод отсутствует"
        }}</pre>
    </div>
  </Dialog>

  <Footer/>
</template>
