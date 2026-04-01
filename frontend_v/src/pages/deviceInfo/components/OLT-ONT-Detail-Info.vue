<template>
  <tr :class="lineClasses">
    <td class="btn-fog" style="text-align: right">
      <div class="flex items-center justify-end">
        <Comment :interface="ontInterface" :device-name="deviceName"/>

        <div @click="toggleDetailInfo" class="px-4 text-center text-xl font-mono">
          {{ line[0] }}
        </div>

        <PortControlButtons
          :device-name="deviceName"
          :interface="ontInterface"
          :permission-level="permissionLevel"
        />

        <Button @click="toggleDetailInfo" text class="rounded-2xl">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box" viewBox="0 0 16 16">
            <path
              d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"
            ></path>
          </svg>
        </Button>
      </div>
    </td>

    <td class="px-2">
      <div :style="statusCellStyle" class="dark:text-gray-950 dark:opacity-70 rounded-2xl px-4 py-1.5 font-mono hover:shadow-md">
        {{ line[1] }}
      </div>
    </td>

    <td v-if="showSubscribersData">
      <div v-for="customer in subscriberSummary.customers" :key="customer.id">
        <router-link :to="{ name: 'gpon-view-subscriber', params: { id: customer.id } }" target="_blank">
          <Button text size="small" class="w-full rounded-2xl" icon="pi pi-user" :label="customer.fullName"/>
        </router-link>
      </div>
    </td>
    <td v-else class="font-mono">{{ line[2] }}</td>

    <td v-if="showSubscribersData" class="px-3">
      <div v-for="(address, index) in subscriberSummary.addresses" :key="`${ontID}-address-${index}`">
        {{ address }}
      </div>
    </td>
    <td v-else class="font-mono px-3">{{ line[3] }}</td>

    <td v-if="showSubscribersData" class="font-mono px-3">
      <div v-for="(services, index) in subscriberSummary.services" :key="`${ontID}-services-${index}`">
        {{ services }}
      </div>
    </td>
    <td v-else class="font-mono px-3">{{ line[4] }}</td>

    <td v-if="showSubscribersData" class="font-mono px-3">
      <div v-for="(transit, index) in subscriberSummary.transits" :key="`${ontID}-transit-${index}`">
        {{ transit }}
      </div>
    </td>
    <td v-else class="font-mono px-3" style="text-align: left">{{ line[5] }}</td>
  </tr>

  <tr v-if="showDetailInfo">
    <td colspan="6" class="text-start">
      <div v-if="complexInfo?.portDetailInfo" class="p-3">
        <div v-if="complexInfo.portDetailInfo.type === 'html'" class="py-3 shadow" v-html="complexInfo.portDetailInfo.data"></div>
      </div>

      <ComplexInterfaceInfo
        v-if="complexInfo"
        :complex-info="complexInfo"
        :interface="ontInterface"
        :device-name="deviceName"
      />
    </td>
  </tr>
</template>

<script setup lang="ts">
import {computed, PropType, ref} from "vue";
import {AxiosResponse} from "axios";

import Comment from "@/components/Comment.vue";
import ComplexInterfaceInfo from "@/pages/deviceInfo/components/ComplexInterfaceInfo.vue";
import PortControlButtons from "@/pages/deviceInfo/components/PortControlButtons.vue";
import api from "@/services/api";
import {DeviceInterface} from "@/services/interfaces";
import {ComplexInterfaceInfoType} from "@/pages/deviceInfo/detailInterfaceInfo";
import {OltSubscriberSummary} from "@/pages/deviceInfo/components/oltSubscribers";

const props = defineProps({
  deviceName: {required: true, type: String},
  interface: {required: true, type: Object as PropType<DeviceInterface>},
  line: {required: true, type: Array as PropType<any[]>},
  permissionLevel: {required: true, type: Number},
  showSubscribersData: {required: false, type: Boolean, default: false},
  subscriberRow: {
    required: false,
    type: Object as PropType<OltSubscriberSummary | null>,
    default: null,
  },
});

const showDetailInfo = ref(false);
const complexInfo = ref<ComplexInterfaceInfoType | null>(null);

const ontID = computed(() => String(props.line[0]));
const status = computed(() => String(props.line[1] || ""));
const comments = computed(() => props.line[7] || []);

const subscriberSummary = computed<OltSubscriberSummary>(() => props.subscriberRow || {
  customers: [],
  addresses: [],
  services: [],
  transits: [],
});

const ontInterface = computed<DeviceInterface>(() => ({
  name: `${props.interface.name}/${ontID.value}`,
  status: status.value,
  description: `ONT: ${ontID.value} ${props.interface.description}`,
  vlans: [],
  comments: comments.value,
}));

const lineClasses = computed(() => showDetailInfo.value ? ["shadow", "sticky-top"] : []);

const rowStyle = computed<Record<string, string>>(() => {
  if (status.value.toLowerCase() === "offline") {
    return {"background-color": "rgba(255,138,148,0.13)", top: "0"};
  }
  if (showDetailInfo.value) {
    return {
      "background-color": "rgba(232,239,255,0.5)",
      top: "56px",
    };
  }
  return {"background-color": "transparent", top: "0"};
});

const statusCellStyle = computed<Record<string, string>>(() => {
  if (status.value === "OK") {
    return {"background-color": "#22e58b"};
  }
  if (status.value === "OFFLINE") {
    return {"background-color": "#ffcacf"};
  }
  return {"background-color": "transparent"};
});

function toggleDetailInfo() {
  showDetailInfo.value = !showDetailInfo.value;

  if (showDetailInfo.value && !complexInfo.value) {
    getDetailInfo();
  }
}

function getDetailInfo() {
  if (!showDetailInfo.value) {
    return;
  }

  api.get(`/api/v1/devices/${props.deviceName}/interface-info?port=${ontInterface.value.name}`)
    .then((value: AxiosResponse<ComplexInterfaceInfoType>) => {
      complexInfo.value = value.data;
    });
}
</script>
