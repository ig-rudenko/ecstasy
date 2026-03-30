<script setup lang="ts">
import {computed, PropType, ref} from "vue";
import api from "@/services/api";
import {DeviceInterface} from "@/services/interfaces";
import errorFmt from "@/errorFmt";
import {textToHtml} from "@/formats";

const props = defineProps({
  deviceName: {
    type: String,
    required: true
  },
  interfaces: {
    type: Array as PropType<DeviceInterface[]>,
    required: true
  }
});

interface StringValues {
  [key: string]: string;
}

interface NullNumberValues {
  [key: string]: null | number;
}

interface CommandContext {
  port?: StringValues;
  ip?: StringValues;
  mac?: StringValues;
  number?: NullNumberValues;
  word?: StringValues;
}

interface CommandType {
  id: number;
  name: string;
  description: string;
  command: string;
  device_vendor: string;
  context: CommandContext;
}

interface CommandResult {
  command: string;
  output: string;
  error: string;
  isRunning: boolean;
}

interface CommandValidateResult {
  command: string;
  conditions: { expect: string, command: string }[];
}

const visible = ref(false);
const results = ref<CommandResult[]>([]);
const commands = ref<CommandType[]>([]);
const searchByName = ref("");
const searchByCommand = ref("");

async function openCommands() {
  try {
    const resp = await api.get<CommandType[]>(`/api/v1/devices/${props.deviceName}/commands`);
    resp.data.forEach((c: CommandType) => {
      c.command = c.command.replaceAll(/\{if.+(?<!\\)}/g, "");
      c.context = {};
      markCommandKeys(c);
    });
    commands.value = resp.data;
  } catch (e) {
    console.error(e);
  }
  visible.value = true;
}

function getKeyName(key: string): string {
  const regex = /#(\S+)?}/;
  const match = regex.exec(key);
  if (match) {
    return match[1];
  }
  return "_";
}

const numberRegex = /\{number:?(-?\d+)?:?(-?\d+)?(#(\S+?)?)?}/;
const portRegex = /\{port(#(\S+?)?)?}/;
const ipRegex = /\{ip(#(\S+?)?)?}/;
const macRegex = /\{mac(#(\S+?)?)?}/;
const wordRegex = /\{word(#(\S+?)?)?}/;

function markCommandKeys(command: CommandType) {
  command.context.number = {};
  command.context.port = {};
  command.context.ip = {};
  command.context.mac = {};
  command.context.word = {};

  const numberRegexGlobal = /\{number:?(-?\d+)?:?(-?\d+)?(#(\S+?)?)?}/g;
  const portRegexGlobal = /\{port(#(\S+?)?)?}/g;
  const ipRegexGlobal = /\{ip(#(\S+?)?)?}/g;
  const macRegexGlobal = /\{mac(#(\S+?)?)?}/g;
  const wordRegexGlobal = /\{word(#(\S+?)?)?}/g;

  let match;

  while ((match = numberRegexGlobal.exec(command.command)) !== null) {
    command.context.number[getKeyName(match[0])] = null;
  }
  while ((match = portRegexGlobal.exec(command.command)) !== null) {
    command.context.port[getKeyName(match[0])] = "";
  }
  while ((match = ipRegexGlobal.exec(command.command)) !== null) {
    command.context.ip[getKeyName(match[0])] = "";
  }
  while ((match = macRegexGlobal.exec(command.command)) !== null) {
    command.context.mac[getKeyName(match[0])] = "";
  }
  while ((match = wordRegexGlobal.exec(command.command)) !== null) {
    command.context.word[getKeyName(match[0])] = "";
  }
}

function numberVerboseRange(command: string): string {
  const numberMatch = numberRegex.exec(command);
  if (numberMatch && numberMatch.length >= 3) {
    const start = Number(numberMatch[1]);
    const end = Number(numberMatch[2]);
    return `целое число от ${start} до ${end}`;
  }
  return "любое целое число";
}

function numberMinValue(command: string): number | undefined {
  const numberMatch = numberRegex.exec(command);
  if (numberMatch && numberMatch.length >= 3) {
    return Number(numberMatch[1]);
  }
}

function numberMaxValue(command: string): number | undefined {
  const numberMatch = numberRegex.exec(command);
  if (numberMatch && numberMatch.length >= 3) {
    return Number(numberMatch[2]);
  }
}

const interfacesNames = computed(() => props.interfaces.map((i) => i.name));

const filteredCommands = computed(() => {
  const nameQuery = searchByName.value.trim().toLowerCase();
  const commandQuery = searchByCommand.value.trim().toLowerCase();

  return commands.value.filter((command) => {
    const matchesName = !nameQuery || command.name.toLowerCase().includes(nameQuery);
    const matchesCommand = !commandQuery || command.command.toLowerCase().includes(commandQuery);
    return matchesName && matchesCommand;
  });
});

function cleanMacAddress(mac: string): string {
  const cleaned = mac.toUpperCase().match(/[0-9A-F]/g);
  return cleaned && cleaned.length === 12 ? cleaned.join("") : "";
}

function isValidWord(word: string): boolean {
  return word.match(/^\S+$/g) != null;
}

function isValidIPAddress(ip: string): boolean {
  const ipRegexValue = /^(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)$/;
  return ipRegexValue.test(ip);
}

function commandIsValid(command: CommandType) {
  if (command.context.port) {
    for (const key in command.context.port) {
      if (!command.context.port[key].length) return false;
    }
  }
  if (command.context.ip) {
    for (const key in command.context.ip) {
      if (!isValidIPAddress(command.context.ip[key])) return false;
    }
  }
  if (command.context.mac) {
    for (const key in command.context.mac) {
      if (!cleanMacAddress(command.context.mac[key])) return false;
    }
  }
  if (command.context.word) {
    for (const key in command.context.word) {
      if (!isValidWord(command.context.word[key])) return false;
    }
  }
  if (command.context.number) {
    for (const key in command.context.number) {
      if (command.context.number[key] == null || isNaN(command.context.number[key] as number)) return false;
    }
  }
  return true;
}

async function getValidatedCommand(command: CommandType): Promise<string> {
  try {
    const url = `/api/v1/devices/${props.deviceName}/commands/${command.id}/validate`;
    const validateRes = await api.post<{ command: CommandValidateResult[] }>(url, command.context);

    let validatedCommands = "";
    for (const commandElement of validateRes.data.command) {
      validatedCommands += commandElement.command + "\n";
    }
    return validatedCommands;
  } catch (e: any) {
    console.error(e);
    return command.command;
  }
}

async function executeCommand(command: CommandType) {
  if (!commandIsValid(command)) return;

  const validCommand = await getValidatedCommand(command);
  const resultRow: CommandResult = {command: validCommand, output: "", error: "", isRunning: true};
  results.value.unshift(resultRow);

  try {
    const url = `/api/v1/devices/${props.deviceName}/commands/${command.id}/execute`;
    const resp = await api.post<{ output: string }>(url, command.context);
    resultRow.output = resp.data.output;
  } catch (e: any) {
    console.error(e);
    resultRow.error = errorFmt(e);
  }
  resultRow.isRunning = false;
}
</script>

<template>
  <Button v-tooltip.right="'Команды'" outlined @click="openCommands">
      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
        <path
            d="M2 3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h5.5a.5.5 0 0 1 0 1H2a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v4a.5.5 0 0 1-1 0V4a1 1 0 0 0-1-1z"/>
        <path
            d="M3.146 5.146a.5.5 0 0 1 .708 0L5.177 6.47a.75.75 0 0 1 0 1.06L3.854 8.854a.5.5 0 1 1-.708-.708L4.293 7 3.146 5.854a.5.5 0 0 1 0-.708M5.5 9a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1H6a.5.5 0 0 1-.5-.5M16 12.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0m-3.5-2a.5.5 0 0 0-.5.5v1h-1a.5.5 0 0 0 0 1h1v1a.5.5 0 0 0 1 0v-1h1a.5.5 0 0 0 0-1h-1v-1a.5.5 0 0 0-.5-.5"/>
      </svg>
  </Button>

  <Dialog v-model:visible="visible" modal maximizable header="Выполнение команд" class="w-[min(96vw,1500px)]" content-class="!p-0">
    <div class="flex flex-col gap-6 bg-gray-50/60 p-4 dark:bg-gray-950/30 sm:p-6">
      <section class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Список команд</div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Фильтрация по названию и шаблону команды.</div>
            </div>

            <div class="grid gap-3 md:grid-cols-2 xl:min-w-[34rem]">
              <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model.trim="searchByName" placeholder="Фильтр по названию" fluid />
              </IconField>
              <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model.trim="searchByCommand" placeholder="Фильтр по команде" fluid />
              </IconField>
            </div>
          </div>

          <div class="overflow-hidden rounded-3xl border border-gray-200/80 dark:border-gray-700/80">
            <div class="hidden custom-grid gap-4 bg-gray-100/80 px-4 py-3 text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:bg-gray-800/80 dark:text-gray-400 lg:grid">
              <div>Название</div>
              <div>Команда</div>
              <div>Описание</div>
              <div class="text-right">Действие</div>
            </div>

            <div class="max-h-[55vh] overflow-auto">
              <div
                  v-for="data in filteredCommands"
                  :key="data.id"
                  class="border-t border-gray-200/80 bg-white/80 px-4 py-4 first:border-t-0 dark:border-gray-700/80 dark:bg-gray-900/60"
              >
                <div class="grid gap-4 custom-grid">
                  <div class="space-y-2">
                    <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ data.name }}</div>
                    <div class="text-xs uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">{{ data.device_vendor }}</div>
                  </div>

                  <div class="space-y-2">
                    <div v-for="line in data.command.split('\n')" :key="line" class="flex flex-wrap items-center gap-2 rounded-2xl border border-gray-200/80 bg-gray-50/80 p-2 dark:border-gray-700/80 dark:bg-gray-800/70">
                      <template v-for="part in line.split(/(?={)|(?<=})/)" :key="part">
                        <Select
                            v-if="data.context.port && portRegex.test(part)"
                            v-model="data.context.port[getKeyName(part)]"
                            :options="interfacesNames"
                            filter
                            placeholder="Порт"
                            class="min-w-[11rem]"
                            v-tooltip="getKeyName(part)"
                        />
                        <InputText
                            v-else-if="data.context.mac && macRegex.test(part)"
                            v-model="data.context.mac[getKeyName(part)]"
                            placeholder="MAC адрес"
                            class="min-w-[11rem]"
                            v-tooltip="getKeyName(part)"
                        />
                        <InputText
                            v-else-if="data.context.ip && ipRegex.test(part)"
                            v-model="data.context.ip[getKeyName(part)]"
                            placeholder="IP адрес"
                            class="min-w-[11rem]"
                            v-tooltip="getKeyName(part)"
                        />
                        <InputText
                            v-else-if="data.context.word && wordRegex.test(part)"
                            v-model="data.context.word[getKeyName(part)]"
                            :placeholder="getKeyName(part)"
                            class="min-w-[11rem]"
                            v-tooltip="getKeyName(part)"
                        />
                        <InputNumber
                            v-else-if="data.context.number && numberRegex.test(part)"
                            v-model="data.context.number[getKeyName(part)]"
                            :min="numberMinValue(part)"
                            :max="numberMaxValue(part)"
                            :placeholder="getKeyName(part)"
                            input-class="w-[96px]"
                            size="small"
                            v-tooltip="`${getKeyName(part)}: ${numberVerboseRange(part)}`"
                        />
                        <code v-else class="rounded-xl bg-gray-200/70 px-2 py-1 text-xs text-gray-700 dark:bg-gray-700/70 dark:text-gray-200">{{ part }}</code>
                      </template>
                    </div>
                  </div>

                  <div class="text-sm leading-6 text-gray-600 dark:text-gray-300">
                    {{ data.description || "Описание отсутствует" }}
                  </div>

                  <div class="flex items-start justify-end">
                    <Button
                        severity="success"
                        :disabled="!commandIsValid(data)"
                        @click="() => executeCommand(data)"
                        icon="pi pi-play"
                        label="Выполнить"
                        class="!rounded-2xl"
                    />
                  </div>
                </div>
              </div>

              <div v-if="!filteredCommands.length" class="px-4 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                Команды не найдены
              </div>
            </div>
          </div>
        </div>
      </section>

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
                <Button text rounded icon="pi pi-angle-down" @click="toggleCallback" />
                <div class="min-w-0 flex-1">
                  <div class="whitespace-pre-wrap break-all text-xs text-gray-700 dark:text-gray-200">{{ data.command }}</div>
                </div>
                <Button severity="danger" icon="pi pi-trash" rounded outlined @click="results.splice(index, 1)" />
              </div>
            </template>

            <Message v-if="data.error" severity="error" class="rounded-2xl">
              <div v-html="textToHtml(data.error)"></div>
            </Message>
            <pre v-else-if="data.output" class="overflow-auto whitespace-pre-wrap rounded-2xl bg-gray-950 px-4 py-3 text-xs text-gray-100">{{ data.output }}</pre>
            <div v-else class="flex justify-center py-6">
              <ProgressSpinner />
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


<style scoped>
.custom-grid {
  display: grid;
  grid-template-columns: minmax(16rem, 0.8fr) minmax(26rem, 1.7fr) minmax(14rem, 0.9fr) 9rem;
}
</style>