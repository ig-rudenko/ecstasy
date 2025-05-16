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
})

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

const visible = ref(false);
const results = ref<CommandResult[]>([]);

const commands = ref<CommandType[]>([]);

async function openCommands() {
  try {
    const resp = await api.get<CommandType[]>(`/api/v1/devices/${props.deviceName}/commands`);
    resp.data.forEach(
        (c: CommandType) => {
          c.context = {};
          markCommandKeys(c);
        }
    );
    console.log(resp.data)
    commands.value = resp.data
  } catch (e) {
    console.error(e);
  }
  visible.value = true;
}


function getKeyName(key: string): string {
  const regex = /#(\S+)?}/
  const match = regex.exec(key);
  if (match) {
    return match[1];
  }
  return "_";
}


const numberRegex = /\{number:?(-?\d+)?:?(-?\d+)?(#(\S+)?)?}/
const portRegex = /\{port(#(\S+)?)?}/
const ipRegex = /\{ip(#(\S+)?)?}/
const macRegex = /\{mac(#(\S+)?)?}/
const wordRegex = /\{word(#(\S+)?)?}/


function markCommandKeys(command: CommandType) {
  command.context.number = {};
  command.context.port = {};
  command.context.ip = {};
  command.context.mac = {};
  command.context.word = {};

  const numberRegex = /\{number:?(-?\d+)?:?(-?\d+)?(#(\S+)?)?}/g
  const portRegex = /\{port(#(\S+)?)?}/g
  const ipRegex = /\{ip(#(\S+)?)?}/g
  const macRegex = /\{mac(#(\S+)?)?}/g
  const wordRegex = /\{word(#(\S+)?)?}/g

  let match;

  while ((match = numberRegex.exec(command.command)) !== null) {
    command.context.number[getKeyName(match[0])] = null;
  }

  while ((match = portRegex.exec(command.command)) !== null) {
    command.context.port[getKeyName(match[0])] = "";
  }

  while ((match = ipRegex.exec(command.command)) !== null) {
    command.context.ip[getKeyName(match[0])] = "";
  }

  while ((match = macRegex.exec(command.command)) !== null) {
    command.context.mac[getKeyName(match[0])] = "";
  }

  while ((match = wordRegex.exec(command.command)) !== null) {
    command.context.word[getKeyName(match[0])] = "";
  }

}


function numberVerboseRange(command: string): string {
  const numberMatch = numberRegex.exec(command)
  if (numberMatch && numberMatch.length >= 3) {
    const start = Number(numberMatch[1]);
    const end = Number(numberMatch[2]);
    return "целое число от " + start + " до " + end;
  }
  return "любое целое число";
}

function numberMinValue(command: string): number | undefined {
  const numberMatch = numberRegex.exec(command)
  if (numberMatch && numberMatch.length >= 3) {
    return Number(numberMatch[1]);
  }
}


function numberMaxValue(command: string): number | undefined {
  const numberMatch = numberRegex.exec(command)
  if (numberMatch && numberMatch.length >= 3) {
    return Number(numberMatch[2]);
  }
}


const interfacesNames = computed(() => {
  return props.interfaces.map(i => i.name);
})

function cleanMacAddress(mac: string): string {
  // Приводим к верхнему регистру и извлекаем только символы 0-9, A-F
  const cleaned = mac.toUpperCase().match(/[0-9A-F]/g);

  // Проверяем, что длина полученной строки ровно 12 символов
  return cleaned && cleaned.length === 12 ? cleaned.join('') : "";
}

function isValidWord(word: string): boolean {
  return word.match(/^\S+$/g) != null;
}

function isValidIPAddress(ip: string): boolean {
  // Регулярное выражение для проверки IPv4-адреса
  const ipRegex = /^(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)$/;
  return ipRegex.test(ip);
}

function commandIsValid(command: CommandType) {
  if (command.context.port) {
    for (const key in command.context.port) {
      if (!command.context.port[key].length) {
        console.log("PORT INVALID")
        return false;
      }
    }
  }

  if (command.context.ip) {
    for (const key in command.context.ip) {
      if (!isValidIPAddress(command.context.ip[key])) {
        console.log("IP INVALID")
        return false;
      }
    }
  }

  if (command.context.mac) {
    for (const key in command.context.mac) {
      if (!cleanMacAddress(command.context.mac[key])) {
        console.log("MAC INVALID")
        return false;
      }
    }
  }

  if (command.context.word) {
    for (const key in command.context.word) {
      if (!isValidWord(command.context.word[key])) {
        console.log("WORD INVALID")
        return false;
      }
    }
  }

  if (command.context.number) {
    for (const key in command.context.number) {
      if (!command.context.number[key] || isNaN(command.context.number[key])) {
        console.log("NUMBER INVALID")
        return false;
      }
    }
  }

  return true;
}


async function getValidatedCommand(command: CommandType): Promise<string> {
  try {
    let url = `/api/v1/devices/${props.deviceName}/commands/${command.id}/validate`
    const validateRes = await api.post<{ command: string }>(url, command.context);
    return validateRes.data.command;
  } catch (e: any) {
    console.error(e);
    return command.command;
  }
}


async function executeCommand(command: CommandType) {
  if (!commandIsValid(command)) return;

  const validCommand = await getValidatedCommand(command)

  const resultRow = ref<CommandResult>({command: validCommand, output: "", error: "", isRunning: true})
  results.value.unshift(resultRow.value)
  try {
    let url = `/api/v1/devices/${props.deviceName}/commands/${command.id}/execute`
    const resp = await api.post<{ output: string }>(url, command.context);
    resultRow.value.output = resp.data.output
  } catch (e: any) {
    console.error(e);
    resultRow.value.error = errorFmt(e)
  }
  resultRow.value.isRunning = false;
}

</script>

<template>
  <div>
    <Button v-tooltip.right="'Команды'" outlined @click="openCommands">
      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
        <path
            d="M2 3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h5.5a.5.5 0 0 1 0 1H2a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v4a.5.5 0 0 1-1 0V4a1 1 0 0 0-1-1z"/>
        <path
            d="M3.146 5.146a.5.5 0 0 1 .708 0L5.177 6.47a.75.75 0 0 1 0 1.06L3.854 8.854a.5.5 0 1 1-.708-.708L4.293 7 3.146 5.854a.5.5 0 0 1 0-.708M5.5 9a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1H6a.5.5 0 0 1-.5-.5M16 12.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0m-3.5-2a.5.5 0 0 0-.5.5v1h-1a.5.5 0 0 0 0 1h1v1a.5.5 0 0 0 1 0v-1h1a.5.5 0 0 0 0-1h-1v-1a.5.5 0 0 0-.5-.5"/>
      </svg>
    </Button>
  </div>

  <Dialog modal v-model:visible="visible" maximizable header="Выполнение команд">
    <div>
      <DataTable :value="commands" paginator :always-show-paginator="false" :rows="10">
        <Column field="name" header="Название"></Column>
        <Column header="Команда">
          <template #body="{ data }">
            <div class="flex flex-col gap-2 items-start">
              <div v-for="line in data.command.split('\n')" class="flex gap-2 items-center">
                <template v-for="part in line.split(' ')" :key="part">
                  <Select v-if="data.context.port && portRegex.test(part)" :options="interfacesNames"
                          v-tooltip="getKeyName(part)"
                          v-model="data.context.port[getKeyName(part)]" filter
                          placeholder="Порт">
                    <template #value="slotProps">
                      <div v-if="slotProps.value" class="flex items-center">
                        <div>{{ slotProps.value }}</div>
                      </div>
                      <span v-else>
                          {{ slotProps.placeholder }}
                      </span>
                    </template>
                  </Select>

                  <InputText v-tooltip="getKeyName(part)" v-else-if="data.context.mac && macRegex.test(part)"
                             v-model="data.context.mac[getKeyName(part)]" placeholder="MAC адрес"/>
                  <InputText v-tooltip="getKeyName(part)" v-else-if="data.context.ip && ipRegex.test(part)"
                             v-model="data.context.ip[getKeyName(part)]" placeholder="IP адрес"/>
                  <InputText v-tooltip="getKeyName(part)" v-else-if="data.context.word && wordRegex.test(part)"
                             v-model="data.context.word[getKeyName(part)]" placeholder=""/>

                  <InputNumber v-tooltip="getKeyName(part)+': '+numberVerboseRange(part)"
                               v-else-if="data.context.number && numberRegex.test(part)"
                               :min="numberMinValue(part)" :max="numberMaxValue(part)"
                               v-model="data.context.number[getKeyName(part)]" placeholder="Целое число"/>

                  <div v-else class="font-mono">{{ part }}</div>
                </template>
              </div>
            </div>
          </template>
        </Column>
        <Column field="description" header="Описание"></Column>
        <Column header="Выполнить">
          <template #body="{ data }">
            <Button severity="success" :disabled="!commandIsValid(data)"
                    @click="() => executeCommand(data)" icon="pi pi-check"
                    label="Выполнить"/>
          </template>
        </Column>
      </DataTable>
    </div>

    <div class="pt-10 font-mono">
      <DataTable v-if="results.length" :value="results" paginator :always-show-paginator="false" :rows="5">
        <Column field="result" class="font-mono">
          <template #body="{ data, index }">
            <Fieldset toggleable>
              <template #legend="{toggleCallback}">
                <div class="flex items-center gap-2 p-2">
                  <i class="pi pi-fw pi-angle-double-down cursor-pointer" @click="toggleCallback"/>
                  <div class="p-2"><span v-html="textToHtml(data.command)"></span></div>
                  <Button severity="danger" icon="pi pi-trash" rounded outlined @click="results.splice(index, 1)"/>
                </div>
              </template>
              <div>
                <Message v-if="data.error" severity="error">
                  <div v-html="textToHtml(data.error)"></div>
                </Message>
                <div v-else-if="data.output" class="" v-html="textToHtml(data.output)"></div>
                <div v-else>
                  <ProgressSpinner/>
                </div>
              </div>
            </Fieldset>
          </template>
        </Column>
      </DataTable>
    </div>

  </Dialog>

</template>
