<script setup lang="ts">
import {computed, ref, watch} from "vue";
import errorFmt from "@/errorFmt";
import {
  cloneCommandTemplate,
  commandIsValid,
  DeviceCommandTemplate,
  fetchDeviceCommands,
  getCommandKeyName,
  ipRegex,
  macRegex,
  numberMaxValue,
  numberMinValue,
  numberRegex,
  numberVerboseRange,
  portRegex,
  wordRegex,
} from "@/services/deviceCommands";

const props = withDefaults(defineProps<{
  deviceName?: string | null
  portOptions?: string[]
  mode?: "select" | "execute"
  modelValue?: DeviceCommandTemplate | null
  emptyTitle?: string
  emptyDescription?: string
  title?: string
  description?: string
}>(), {
  deviceName: null,
  portOptions: () => [],
  mode: "select",
  modelValue: null,
  emptyTitle: "Нет доступных команд",
  emptyDescription: "Выберите оборудование с подходящими вендором и моделью.",
  title: "Команды",
  description: "Выберите шаблон команды и заполните параметры.",
});

const emit = defineEmits<{
  (e: "update:modelValue", value: DeviceCommandTemplate | null): void
  (e: "execute", value: DeviceCommandTemplate): void
  (e: "loaded", value: DeviceCommandTemplate[]): void
}>();

const commands = ref<DeviceCommandTemplate[]>([]);
const isLoading = ref(false);
const loadError = ref("");
const searchByName = ref("");
const searchByCommand = ref("");
const selectedCommandId = ref<number | null>(props.modelValue?.id || null);

/**
 * Synchronizes selected state from the parent.
 */
function syncSelectedFromModelValue(value: DeviceCommandTemplate | null): void {
  selectedCommandId.value = value?.id || null;

  if (!value) {
    return;
  }

  const existingCommand = commands.value.find((command) => command.id === value.id);
  if (existingCommand) {
    existingCommand.context = cloneCommandTemplate(value).context;
  }
}

watch(() => props.modelValue, (value) => {
  syncSelectedFromModelValue(value || null);
}, {immediate: true});

/**
 * Loads device commands when source device changes.
 */
async function loadCommands(): Promise<void> {
  if (!props.deviceName) {
    commands.value = [];
    loadError.value = "";
    emit("loaded", []);
    emit("update:modelValue", null);
    return;
  }

  isLoading.value = true;
  loadError.value = "";

  try {
    const loadedCommands = await fetchDeviceCommands(props.deviceName);
    commands.value = loadedCommands;
    emit("loaded", loadedCommands);

    const selected = props.modelValue
        ? loadedCommands.find((command) => command.id === props.modelValue?.id)
        : null;

    if (selected && props.modelValue) {
      selected.context = cloneCommandTemplate(props.modelValue).context;
      selectedCommandId.value = selected.id;
      emit("update:modelValue", cloneCommandTemplate(selected));
    } else {
      selectedCommandId.value = null;
      emit("update:modelValue", null);
    }
  } catch (error: any) {
    console.error(error);
    loadError.value = errorFmt(error);
    commands.value = [];
    emit("loaded", []);
    emit("update:modelValue", null);
  } finally {
    isLoading.value = false;
  }
}

watch(() => props.deviceName, () => {
  loadCommands();
}, {immediate: true});

const filteredCommands = computed(() => {
  const nameQuery = searchByName.value.trim().toLowerCase();
  const commandQuery = searchByCommand.value.trim().toLowerCase();

  return commands.value.filter((command) => {
    const matchesName = !nameQuery || command.name.toLowerCase().includes(nameQuery);
    const matchesCommand = !commandQuery || command.command.toLowerCase().includes(commandQuery);
    return matchesName && matchesCommand;
  });
});

/**
 * Emits current selected command with current context.
 */
function emitSelection(command: DeviceCommandTemplate | null): void {
  emit("update:modelValue", command ? cloneCommandTemplate(command) : null);
}

/**
 * Selects a command in select mode.
 */
function selectCommand(command: DeviceCommandTemplate): void {
  selectedCommandId.value = command.id;
  emitSelection(command);
}

/**
 * Emits an execute request for the command.
 */
function executeCommand(command: DeviceCommandTemplate): void {
  emit("execute", cloneCommandTemplate(command));
}

/**
 * Updates parent with latest context when selected command changes.
 */
function syncCommandContext(command: DeviceCommandTemplate): void {
  if (selectedCommandId.value === command.id) {
    emitSelection(command);
  }
}
</script>

<template>
  <section
      class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ title }}</div>
          <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ description }}</div>
          <div v-if="deviceName" class="mt-2 text-xs uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">
            Источник команд: {{ deviceName }}
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2 xl:min-w-136">
          <IconField>
            <InputIcon class="pi pi-search"/>
            <InputText v-model.trim="searchByName" placeholder="Фильтр по названию" fluid/>
          </IconField>
          <IconField>
            <InputIcon class="pi pi-search"/>
            <InputText v-model.trim="searchByCommand" placeholder="Фильтр по команде" fluid/>
          </IconField>
        </div>
      </div>

      <Message v-if="loadError" severity="error" class="rounded-2xl">
        {{ loadError }}
      </Message>

      <div class="overflow-hidden rounded-3xl border border-gray-200/80 dark:border-gray-700/80">
        <div
            class="hidden command-grid gap-4 bg-gray-100/80 px-4 py-3 text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:bg-gray-800/80 dark:text-gray-400 lg:grid">
          <div>Название</div>
          <div>Команда</div>
          <div>Описание</div>
          <div class="text-right">Действие</div>
        </div>

        <div class="max-h-[55vh] overflow-auto">
          <div v-if="isLoading" class="flex justify-center py-10">
            <ProgressSpinner/>
          </div>

          <template v-else>
            <div
                v-for="data in filteredCommands"
                :key="data.id"
                :class="selectedCommandId === data.id ? 'bg-sky-50/80 ring-1 ring-sky-500/20 dark:bg-sky-950/20' : 'bg-white/80 dark:bg-gray-900/60'"
                class="border-t border-gray-200/80 px-4 py-4 first:border-t-0 dark:border-gray-700/80"
            >
              <div class="grid gap-4 command-grid">
                <div class="space-y-2">
                  <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ data.name }}</div>
                  <div class="text-xs uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">{{
                      data.device_vendor
                    }}
                  </div>
                </div>

                <div class="space-y-2">
                  <div
                      v-for="line in data.command.split('\n')"
                      :key="`${data.id}-${line}`"
                      class="flex flex-wrap items-center gap-2 rounded-2xl border border-gray-200/80 bg-gray-50/80 p-2 dark:border-gray-700/80 dark:bg-gray-800/70"
                  >
                    <template v-for="part in line.split(/(?={)|(?<=})/)" :key="part">
                      <Select
                          v-if="data.context.port && portRegex.test(part) && portOptions.length"
                          v-model="data.context.port[getCommandKeyName(part)]"
                          :options="portOptions"
                          filter
                          placeholder="Порт"
                          size="small"
                          class="min-w-[11rem] rounded-full! text-xs!"
                          v-tooltip="getCommandKeyName(part)"
                          @update:modelValue="syncCommandContext(data)"
                      />
                      <InputText
                          v-else-if="data.context.port && portRegex.test(part)"
                          v-model="data.context.port[getCommandKeyName(part)]"
                          placeholder="Порт"
                          class="min-w-[11rem] rounded-full! text-xs"
                          v-tooltip="getCommandKeyName(part)"
                          @update:modelValue="syncCommandContext(data)"
                      />
                      <InputText
                          v-else-if="data.context.mac && macRegex.test(part)"
                          v-model="data.context.mac[getCommandKeyName(part)]"
                          placeholder="MAC адрес"
                          class="min-w-[11rem] rounded-full! text-xs"
                          v-tooltip="getCommandKeyName(part)"
                          @update:modelValue="syncCommandContext(data)"
                      />
                      <InputText
                          v-else-if="data.context.ip && ipRegex.test(part)"
                          v-model="data.context.ip[getCommandKeyName(part)]"
                          placeholder="IP адрес"
                          class="min-w-[11rem] rounded-full! text-xs"
                          v-tooltip="getCommandKeyName(part)"
                          @update:modelValue="syncCommandContext(data)"
                      />
                      <InputText
                          v-else-if="data.context.word && wordRegex.test(part)"
                          v-model="data.context.word[getCommandKeyName(part)]"
                          :placeholder="getCommandKeyName(part)"
                          class="min-w-[11rem] rounded-full! text-xs"
                          v-tooltip="getCommandKeyName(part)"
                          @update:modelValue="syncCommandContext(data)"
                      />
                      <InputNumber
                          v-else-if="data.context.number && numberRegex.test(part)"
                          v-model="data.context.number[getCommandKeyName(part)]"
                          :min="numberMinValue(part)"
                          :max="numberMaxValue(part)"
                          :placeholder="getCommandKeyName(part)"
                          input-class="w-[96px] rounded-full! text-xs"
                          size="small"
                          v-tooltip="`${getCommandKeyName(part)}: ${numberVerboseRange(part)}`"
                          @update:modelValue="syncCommandContext(data)"
                      />
                      <code v-else
                            class="rounded-xl bg-gray-200/70 px-2 py-1 text-xs text-gray-700 dark:bg-gray-700/70 dark:text-gray-200">{{
                          part
                        }}</code>
                    </template>
                  </div>
                </div>

                <div class="text-sm leading-6 text-gray-600 dark:text-gray-300">
                  {{ data.description || "Описание отсутствует" }}
                </div>

                <div class="flex items-start justify-end">
                  <Button
                      v-if="mode === 'execute'"
                      severity="success"
                      :disabled="!commandIsValid(data)"
                      @click="executeCommand(data)"
                      icon="pi pi-play"
                      label="Выполнить"
                      class="rounded-2xl!"
                  />
                  <Button
                      v-else
                      :severity="selectedCommandId === data.id ? 'contrast' : 'secondary'"
                      :outlined="selectedCommandId !== data.id"
                      :disabled="!commandIsValid(data)"
                      @click="selectCommand(data)"
                      :icon="selectedCommandId === data.id ? 'pi pi-check' : 'pi pi-plus'"
                      :label="selectedCommandId === data.id ? 'Выбрана' : 'Выбрать'"
                      class="rounded-2xl!"
                  />
                </div>
              </div>
            </div>

            <div
                v-if="!filteredCommands.length"
                class="px-4 py-10 text-center"
            >
              <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ emptyTitle }}</div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ emptyDescription }}</div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.command-grid {
  display: grid;
  grid-template-columns: minmax(16rem, 0.8fr) minmax(26rem, 1.7fr) minmax(14rem, 0.9fr) 9rem;
}

@media (max-width: 1279px) {
  .command-grid {
    grid-template-columns: 1fr;
  }
}
</style>
