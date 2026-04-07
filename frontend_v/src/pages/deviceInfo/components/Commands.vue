<script setup lang="ts">
import {computed, PropType, ref} from "vue";
import errorFmt from "@/errorFmt";
import {textToHtml} from "@/formats";
import CommandTemplateSelector from "@/components/deviceCommands/CommandTemplateSelector.vue";
import {
  DeviceCommandTemplate,
  executeDeviceCommand,
  validateDeviceCommand,
} from "@/services/deviceCommands";
import {DeviceInterface} from "@/services/interfaces";

interface CommandResult {
  command: string;
  output: string;
  error: string;
  isRunning: boolean;
}

const props = defineProps({
  deviceName: {
    type: String,
    required: true,
  },
  interfaces: {
    type: Array as PropType<DeviceInterface[]>,
    required: true,
  },
});

const visible = ref(false);
const results = ref<CommandResult[]>([]);
const interfaceNames = computed(() => props.interfaces.map((item) => item.name));

/**
 * Opens the command dialog.
 */
function openCommands(): void {
  visible.value = true;
}

/**
 * Executes a command for the current device and stores dialog-local history.
 */
async function runCommand(command: DeviceCommandTemplate): Promise<void> {
  let validatedCommand = command.command;

  try {
    validatedCommand = await validateDeviceCommand(props.deviceName, command);
  } catch (error: any) {
    console.error(error);
  }

  const resultRow: CommandResult = {
    command: validatedCommand,
    output: "",
    error: "",
    isRunning: true,
  };
  results.value.unshift(resultRow);

  try {
    resultRow.output = await executeDeviceCommand(props.deviceName, command);
  } catch (error: any) {
    console.error(error);
    resultRow.error = errorFmt(error);
  } finally {
    resultRow.isRunning = false;
  }
}
</script>

<template>
  <Button v-tooltip.right="'Команды'" outlined @click="openCommands" class="rounded-2xl shadow-sm border-none">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
      <path
          d="M2 3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h5.5a.5.5 0 0 1 0 1H2a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v4a.5.5 0 0 1-1 0V4a1 1 0 0 0-1-1z"/>
      <path
          d="M3.146 5.146a.5.5 0 0 1 .708 0L5.177 6.47a.75.75 0 0 1 0 1.06L3.854 8.854a.5.5 0 1 1-.708-.708L4.293 7 3.146 5.854a.5.5 0 0 1 0-.708M5.5 9a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1H6a.5.5 0 0 1-.5-.5M16 12.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0m-3.5-2a.5.5 0 0 0-.5.5v1h-1a.5.5 0 0 0 0 1h1v1a.5.5 0 0 0 1 0v-1h1a.5.5 0 0 0 0-1h-1v-1a.5.5 0 0 0-.5-.5"/>
    </svg>
  </Button>

  <Dialog v-model:visible="visible" modal maximizable header="Выполнение команд" class="w-[min(96vw,1500px)]" content-class="p-0!">
    <div class="flex flex-col gap-6 bg-gray-50/60 p-4 dark:bg-gray-950/30 sm:p-6">
      <CommandTemplateSelector
          :device-name="deviceName"
          :port-options="interfaceNames"
          mode="execute"
          title="Список команд"
          description="Фильтрация по названию и шаблону команды."
          empty-title="Команды не найдены"
          empty-description="Для этого оборудования нет доступных команд."
          @execute="runCommand"
      />

      <section class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Результаты</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">История выполнения в рамках текущего диалога.</div>
          </div>
        </div>

        <div v-if="results.length" class="flex flex-col gap-3 font-mono">
          <Fieldset
              v-for="(data, index) in results"
              :key="`${data.command}-${index}`"
              toggleable
              class="overflow-hidden rounded-3xl border border-gray-200/80 bg-gray-50/80 dark:border-gray-700/80 dark:bg-gray-800/60"
          >
            <template #legend="{ toggleCallback }">
              <div class="flex w-full items-center gap-3 px-2 py-1">
                <Button text rounded icon="pi pi-angle-down" @click="toggleCallback"/>
                <div class="min-w-0 flex-1">
                  <div class="whitespace-pre-wrap break-all text-xs text-gray-700 dark:text-gray-200">{{ data.command }}</div>
                </div>
                <Button severity="danger" icon="pi pi-trash" rounded outlined @click="results.splice(index, 1)"/>
              </div>
            </template>

            <Message v-if="data.error" severity="error" class="rounded-2xl">
              <div v-html="textToHtml(data.error)"></div>
            </Message>
            <pre v-else-if="data.output" class="overflow-auto whitespace-pre-wrap rounded-2xl bg-gray-950 px-4 py-3 text-xs text-gray-100">{{ data.output }}</pre>
            <div v-else class="flex justify-center py-6">
              <ProgressSpinner/>
            </div>
          </Fieldset>
        </div>

        <div v-else class="py-10 text-center text-sm text-gray-500 dark:text-gray-400">
          Пока нет выполненных команд
        </div>
      </section>
    </div>
  </Dialog>
</template>
