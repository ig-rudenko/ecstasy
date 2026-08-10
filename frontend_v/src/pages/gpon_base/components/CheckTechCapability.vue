<script setup lang="ts">
import { ref } from "vue";
import Paginator from "primevue/paginator";

import errorFmt from "@/errorFmt";
import { getEnd3CapabilityList } from "@/services/gpon";
import { TechCapabilityStatus } from "@/types/gpon";
import type {
    End3CapabilitySearchQuery,
    End3WithCapability,
    GponPaginatedResponse,
    TechCapability,
} from "@/types/gpon";
import { errorToast } from "@/services/my.toast";

import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import End3CollapsedView from "@/pages/gpon_base/components/End3CollapsedView.vue";

const visible = ref(false);
const loading = ref(false);
const formValue = ref<Omit<End3CapabilitySearchQuery, "page">>({
    street: "",
    house: "",
    block: "",
    tech_capability_status: TechCapabilityStatus.empty,
});
const resultData = ref<GponPaginatedResponse<End3WithCapability> | null>(null);
const capabilityMap = new Map<number, TechCapability[]>(); // для хранения данных об подключениях абонентов.

const permissions = ["gpon.view_customer", "gpon.view_subscriberconnection"]; // Права только на просмотр.

/** Searches available technical capabilities using the current filters. */
function findTechCapability(page: number = 1): void {
    loading.value = true;

    getEnd3CapabilityList({ ...formValue.value, page })
        .then((result) => {
            resultData.value = result;
            result.results.forEach((item) => {
                capabilityMap.set(item.id, item.capability); // сохраняем данные для отображения.
            });
        })
        .catch((error) => {
            errorToast("Ошибка при проверке технической возможности", errorFmt(error));
        })
        .finally(() => {
            loading.value = false;
        });
}

/** Функция для удаления данных о подключении абонентов */
function deleteTechCapabilityInfo(id: number): void {
    if (resultData.value) {
        resultData.value.results[id].capability = [];
    }
}

/** Функция для получения данных о подключении абонентов */
function getTechCapabilityInfo(id: number): void {
    if (resultData.value) {
        const item = resultData.value.results[id];
        if (capabilityMap.has(item.id)) {
            item.capability = capabilityMap.get(item.id) || [];
        }
    }
}
</script>

<template>
    <Button
        class="check-tech-button rounded-2xl!"
        @click="visible = true"
        outlined
        icon="pi pi-search"
        severity="success"
        label="Техническая возможность"
    />

    <Dialog v-model:visible="visible" modal maximizable header="Техническая возможность">
        <div class="flex flex-col gap-3 p-4">
            <div class="flex gap-5 flex-wrap">
                <div class="flex flex-col gap-2 max-md:w-full">
                    <label for="street">Улица, пр-кт, шоссе, бульвар и т.д.</label>
                    <InputText
                        fluid
                        class="w-full rounded-2xl"
                        id="street"
                        v-model="formValue.street"
                        @keydown.enter="() => findTechCapability()"
                    />
                    <Message size="small" severity="secondary" variant="simple"
                        >Введите название частично или полностью
                    </Message>
                </div>
                <div class="flex flex-col gap-2 max-md:w-full">
                    <label for="house">Дом</label>
                    <InputText
                        fluid
                        class="w-full rounded-2xl"
                        id="house"
                        v-model="formValue.house"
                        @keydown.enter="() => findTechCapability()"
                    />
                    <Message size="small" severity="secondary" variant="simple">Также укажите букву</Message>
                </div>
                <div class="flex flex-col gap-2 max-md:w-full">
                    <label for="block">Корпус</label>
                    <InputText
                        fluid
                        class="w-full rounded-2xl"
                        id="block"
                        v-model="formValue.block"
                        @keydown.enter="() => findTechCapability()"
                    />
                    <Message size="small" severity="secondary" variant="simple">Если есть</Message>
                </div>
                <div class="flex flex-col gap-2 max-md:w-full">
                    <label for="block">Статус подключения</label>
                    <Select
                        fluid
                        class="w-full rounded-2xl"
                        v-model="formValue.tech_capability_status"
                        :options="Object.values(TechCapabilityStatus)"
                        @change="(e) => $emit('change', e)"
                    >
                        <template #value="slotProps">
                            <div v-if="slotProps.value" class="flex items-center">
                                <TechCapabilityBadge :status="slotProps.value" />
                            </div>
                            <span v-else>{{ slotProps.placeholder }}</span>
                        </template>
                        <template #option="slotProps">
                            <div v-if="slotProps.option" class="flex items-center">
                                <TechCapabilityBadge :status="slotProps.option" />
                            </div>
                        </template>
                    </Select>
                </div>
            </div>
            <div>
                <Button
                    label="Проверить"
                    icon="pi pi-search"
                    class="rounded-2xl"
                    :loading="loading"
                    @click="() => findTechCapability()"
                />
            </div>
        </div>

        <Divider v-if="resultData" />

        <div v-if="resultData" class="p-4">
            <div class="pb-5 text-xl">Всего найдено: {{ resultData.count }}</div>

            <div v-if="resultData.count">
                <div class="flex flex-col gap-5 border rounded-2xl border-gray-300 dark:border-gray-800">
                    <End3CollapsedView
                        @delete-info="deleteTechCapabilityInfo"
                        @get-info="getTechCapabilityInfo"
                        :user-permissions="permissions"
                        :customer-lines="resultData.results"
                        :showAddButton="false"
                    />
                </div>
                <Paginator
                    @page="(event) => findTechCapability(event.page + 1)"
                    :rows="10"
                    :totalRecords="resultData.count"
                />
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
