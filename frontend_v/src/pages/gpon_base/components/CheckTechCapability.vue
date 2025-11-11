<script setup lang="ts">
import {ref} from "vue";
import Paginator from 'primevue/paginator';

import api from "@/services/api";
import errorFmt from "@/errorFmt.ts";
import {End3WithCapability, TechCapability, TechCapabilityStatus} from "@/types/gpon.ts";
import {errorToast} from "@/services/my.toast.ts";
import {Paginator as PaginatorType} from "@/types/paginator.ts";

import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import End3CollapsedView from "@/pages/gpon_base/components/End3CollapsedView.vue";


const visible = ref(false);
const loading = ref(false);
const formValue = ref({
  street: '',
  house: '',
  block: '',
  tech_capability_status: TechCapabilityStatus.empty,
  page: '1',
})
const resultData = ref<null | PaginatorType<End3WithCapability>>(null)
const capabilityMap = new Map<number, TechCapability[]>()   // для хранения данных об подключениях абонентов.

const permissions = ["gpon.view_customer", "gpon.view_subscriberconnection"]  // Права только на просмотр.

function findTechCapability(page: number = 1) {
  formValue.value.page = page.toString();
  const urlParams = new URLSearchParams(formValue.value)
  const url = `/api/v1/gpon/tech-data/end3?${urlParams.toString()}`
  loading.value = true;

  api.get<PaginatorType<End3WithCapability>>(url).then(response => {
    resultData.value = response.data;
    response.data.results.forEach(item => {
      capabilityMap.set(item.id, item.capability);  // сохраняем данные для отображения.
    })
    loading.value = false;
  }).catch(error => {
    errorToast("Ошибка при проверке технической возможности", errorFmt(error));
    loading.value = false;
  })
}

/** Функция для удаления данных о подключении абонентов */
function deleteTechCapabilityInfo(id: number) {
  if (resultData.value) {
    resultData.value.results[id].capability = []
  }
}

/** Функция для получения данных о подключении абонентов */
function getTechCapabilityInfo(id: number) {
  if (resultData.value) {
    const item = resultData.value.results[id];
    if (capabilityMap.has(item.id)) {
      item.capability = capabilityMap.get(item.id) || [];
    }
  }
}

</script>

<template>

  <Button class="check-tech-button" @click="visible = true" outlined icon="pi pi-search"
          label="Техническая возможность"/>

  <Dialog v-model:visible="visible" modal maximizable header="Техническая возможность">
    <div class="flex flex-col gap-5 p-4">
      <div class="flex gap-5 flex-wrap">
        <div class="flex flex-col gap-2 max-md:w-full">
          <label for="street">Улица, пр-кт, шоссе, бульвар и т.д.</label>
          <InputText fluid class="w-full" id="street" v-model="formValue.street" @keydown.enter="() => findTechCapability()"/>
          <Message size="small" severity="secondary" variant="simple">Введите название частично или полностью
          </Message>
        </div>
        <div class="flex flex-col gap-2 max-md:w-full">
          <label for="house">Дом</label>
          <InputText fluid class="w-full" id="house" v-model="formValue.house" @keydown.enter="() => findTechCapability()"/>
          <Message size="small" severity="secondary" variant="simple">Также укажите букву</Message>
        </div>
        <div class="flex flex-col gap-2 max-md:w-full">
          <label for="block">Корпус</label>
          <InputText fluid class="w-full" id="block" v-model="formValue.block" @keydown.enter="() => findTechCapability()"/>
          <Message size="small" severity="secondary" variant="simple">Если есть</Message>
        </div>
        <div class="flex flex-col gap-2 max-md:w-full">
          <label for="block">Статус подключения</label>
          <Select fluid class="w-full" v-model="formValue.tech_capability_status" :options="Object.values(TechCapabilityStatus)" @change="e => $emit('change', e)">
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex items-center">
                <TechCapabilityBadge :status="slotProps.value"/>
              </div>
              <span v-else>{{ slotProps.placeholder }}</span>
            </template>
            <template #option="slotProps">
              <div v-if="slotProps.option" class="flex items-center">
                <TechCapabilityBadge :status="slotProps.option"/>
              </div>
            </template>
          </Select>
        </div>
      </div>
      <div>
        <Button label="Проверить" icon="pi pi-search" :loading="loading" @click="() => findTechCapability()"/>
      </div>
    </div>

    <Divider v-if="resultData"/>

    <div v-if="resultData" class="p-4">
      <div class="pb-5 text-xl">
        Всего найдено: {{ resultData.count }}
      </div>

      <div v-if="resultData.count">
        <div class="flex flex-col gap-5 border">
          <End3CollapsedView @delete-info="deleteTechCapabilityInfo" @get-info="getTechCapabilityInfo"
                             :user-permissions="permissions"
                             :customer-lines="resultData.results" :showAddButton="false"/>
        </div>
        <Paginator @page="event => findTechCapability(event.page + 1)" :rows="10"
                   :totalRecords="resultData.count"/>
      </div>
    </div>

  </Dialog>
</template>

<style scoped>

.check-tech-button {
  border-radius: 12px;
  color: #0fa625;
  border: 1px #0fa625 solid;
}

.check-tech-button:hover {
  box-shadow: 0 0 3px #0fa625;
}

</style>