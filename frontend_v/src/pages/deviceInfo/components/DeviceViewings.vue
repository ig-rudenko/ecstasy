<script setup lang="ts">
import api from "@/services/api";
import {computed, onMounted, onUnmounted, ref} from "vue";
import {useStore} from "vuex";
import {User} from "@/services/user.ts";

interface DeviceViewing {
  username: string
  started: string
  updated: string
}

const props = defineProps({
  deviceName: {
    required: true,
    type: String,
  }
})
let timer = null as null | number
const viewings = ref<DeviceViewing[]>([])
const user: User | null = useStore().state.auth.user;

onMounted(() => {
  updateDeviceViewing()
  if (!timer) {
    timer = window.setInterval(() => updateDeviceViewing(), 2000)
  }
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})

const otherViewingUsers = computed(() => {
  return viewings.value.filter(v => v.username != user?.username)
})

async function updateDeviceViewing() {
  try {
    await api.post(`/api/v1/devices/${props.deviceName}/viewings`)
  } catch (e) {
  }
  try {
    const resp = await api.get<DeviceViewing[]>(`/api/v1/devices/${props.deviceName}/viewings`)
    viewings.value = resp.data
  } catch (e) {
  }
}
</script>

<template>
  <div v-if="otherViewingUsers.length" class="flex flex-col items-end gap-2">
    <div class="text-sm">Смотрят сейчас:</div>
    <div v-if="viewings.length" class="flex flex-wrap gap-2">
        <Badge v-for="viewing in otherViewingUsers"
               v-tooltip="'Начало ' + (new Date(viewing.started)).toLocaleTimeString()"
               :key="viewing.username" severity="">
          {{ viewing.username }}
        </Badge>
    </div>
  </div>
</template>
