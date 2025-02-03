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


interface CommandContext {
  port: string;
  ip: string;
  mac: string;
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
}

const visible = ref(false);
const results = ref<CommandResult[]>([]);

const commands = ref<CommandType[]>([]);

const open = async () => {
  visible.value = true;
  try {
    const resp = await api.get<CommandType[]>(`/api/v1/devices/${props.deviceName}/commands`);
    commands.value = resp.data
    commands.value.forEach((c: CommandType) => c.context = {port: "", ip: "", mac: ""});
  } catch (e) {
    console.error(e);
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

function isValidIPAddress(ip: string): boolean {
  // Регулярное выражение для проверки IPv4-адреса
  const ipRegex = /^(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)$/;
  return ipRegex.test(ip);
}

function commandIsValid(command: CommandType) {
  if (command.command.indexOf("{port}") >= 0 && command.context.port.length === 0) {
    return false;
  }
  if (command.command.indexOf("{ip}") >= 0 && !isValidIPAddress(command.context.ip)) {
    return false;
  }
  return !(command.command.indexOf("{mac}") >= 0 && cleanMacAddress(command.context.mac).length === 0);
}

function createCommand(command: CommandType): string {
  let cmd = command.command.replace("{port}", command.context.port)
  cmd = cmd.replace("{ip}", command.context.ip)
  cmd = cmd.replace("{mac}", command.context.mac)
  return cmd;
}

async function executeCommand(command: CommandType) {
  if (!commandIsValid(command)) return;
  try {
    const resp = await api.post(`/api/v1/devices/${props.deviceName}/commands/${command.id}/execute`, command.context);
    results.value.push(
        {command: createCommand(command), output: resp.data, error: ""}
    )
  } catch (e: any) {
    console.error(e);
    results.value.push(
        {command: createCommand(command), output: "", error: errorFmt(e)}
    )
  }
}

</script>

<template>
  <div>
    <Button v-tooltip.right="'Команды'" outlined @click="open">
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
        <Column field="command" header="Команда">
          <template #body="{ data }">
            <div class="flex gap-2 items-center">
              <template v-for="part in data.command.split(' ')">
                <Select v-if="part === '{port}'" :options="interfacesNames" v-model="data.context.port" filter
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

                <InputText v-else-if="part === '{mac}'" v-model="data.context.mac" placeholder="MAC адрес"/>
                <InputText v-else-if="part === '{ip}'" v-model="data.context.ip" placeholder="IP адрес"/>

                <div v-else class="font-mono">{{ part }}</div>
              </template>
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
        <Column field="command" header="Команда"></Column>
        <Column field="result" header="Результат">
          <template #body="{ data }">
            <Message severity="error" v-if="data.error">
              <div v-html="textToHtml(data.error)"></div>
            </Message>
            <div class="font-mono" v-html="textToHtml(data.output)"></div>
          </template>
        </Column>
      </DataTable>
    </div>

  </Dialog>

</template>
