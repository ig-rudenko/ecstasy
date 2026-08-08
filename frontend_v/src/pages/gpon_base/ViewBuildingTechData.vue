<template>
    <div class="mx-auto py-5 xl:w-2/3">
        <Toast />

        <ViewPrintEditButtons
            @print="printData"
            @changeMode="(mode) => (editMode = mode)"
            @exit="() => $router.push({ name: 'gpon-tech-data' })"
            title="Технические данные - дом"
            :has-permission-to-edit="hasAnyPermissionToUpdate"
            :is-mobile="isMobile"
        />

        <!-- ОШИБКА ЗАГРУЗКИ -->
        <Message v-if="errorStatus" severity="error" class="my-2 rounded-xl p-2">
            Ошибка при загрузке данных.
            <br />
            {{ errorMessage || "" }} <br />
            Статус: {{ errorStatus }}
        </Message>

        <div
            v-if="detailData"
            id="tech-data-block"
            class="px-2 md:p-6 border border-gray-300 dark:border-gray-800 rounded-4xl"
        >
            <!-- ДАННЫЕ ДОМА -->
            <div class="py-3">
                <div class="flex items-center py-3">
                    <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
                        <circle cx="8" cy="8" r="8" />
                    </svg>
                    <div class="text-xl font-semibold m-0 me-3">Адрес: {{ getFullAddress(detailDataAddress) }}</div>
                </div>

                <div class="ml-40 items-center">
                    <div class="col-auto">
                        <BuildingIcon class="m-3" :type="detailData.building_type" width="64" height="64" />
                    </div>
                    <div>
                        <template v-if="detailData.building_type === 'building'">
                            Многоквартирный дом. Количество этажей: {{ detailData.floors }} / Количество подъездов:
                            {{ detailData.total_entrances }}
                        </template>
                        <template v-else> Частный дом. </template>
                    </div>
                </div>
            </div>

            <template v-for="(oltState, oltID) in detailData.oltStates">
                <div class="flex items-center py-3">
                    <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
                        <circle cx="8" cy="8" r="8" />
                    </svg>
                    <div class="text-xl font-semibold m-0 me-3">Задействованные подъезды: {{ oltState.entrances }}</div>
                </div>

                <div class="ml-40">
                    <!-- ОПИСАНИЕ 2 -->
                    <div class="py-2 grid gap-2" :class="{ 'grid-cols-2': !editMode }">
                        <div class="pl-6">Описание сплиттера 2го каскада</div>
                        <div v-if="!editMode">{{ oltState.description }}</div>
                        <Textarea
                            v-else
                            fluid
                            auto-resize
                            v-model="oltState.description"
                            rows="5"
                            class="rounded-2xl"
                        />
                    </div>

                    <!-- ОБОРУДОВАНИЕ -->
                    <div class="py-2 sm:grid grid-cols-2 bg-gray-200 dark:bg-gray-800 rounded-2xl">
                        <div class="pl-6 p-2">OLT оборудование</div>
                        <div>
                            <span id="deviceName" class="flex flex-wrap items-center gap-3 text-primary font-mono">
                                <router-link :to="'/device/' + oltState.statement.deviceName" target="_blank">
                                    <Button text>
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            width="24"
                                            height="24"
                                            fill="currentColor"
                                            viewBox="0 0 16 16"
                                        >
                                            <path
                                                d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"
                                            />
                                        </svg>
                                    </Button>
                                </router-link>
                                <span>{{ oltState.statement.deviceName }}</span>
                                <OltPortsSubscriberStatistic :device-name="oltState.statement.deviceName" />
                            </span>
                        </div>
                    </div>

                    <!-- ПОРТ -->
                    <div class="py-2 grid grid-cols-2">
                        <div class="pl-6 p-2">Порт</div>
                        <div>
                            <router-link :to="getOLTTechDataURL(oltState.statement)">
                                <Button text class="font-mono">
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="24"
                                        height="24"
                                        fill="currentColor"
                                        viewBox="0 0 16 16"
                                    >
                                        <path
                                            fill-rule="evenodd"
                                            d="M6 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-2a.5.5 0 0 0-1 0v2A1.5 1.5 0 0 0 6.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 2h-8A1.5 1.5 0 0 0 5 3.5v2a.5.5 0 0 0 1 0v-2z"
                                        />
                                        <path
                                            fill-rule="evenodd"
                                            d="M11.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H1.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"
                                        />
                                    </svg>
                                    {{ oltState.statement.devicePort }}
                                </Button>
                            </router-link>
                        </div>
                    </div>

                    <!-- ВОЛОКНО -->
                    <div class="py-2 grid grid-cols-2 bg-gray-200 dark:bg-gray-800 rounded-2xl">
                        <div class="pl-6 p-2">Волокно</div>
                        <div class="p-2">{{ oltState.statement.fiber }}</div>
                    </div>

                    <!-- ОПИСАНИЕ -->
                    <div class="py-2 grid grid-cols-2">
                        <div class="pl-6 p-2">Описание сплиттера 1го каскада</div>
                        <div class="p-2">{{ oltState.statement.description }}</div>
                    </div>
                </div>

                <!-- Абонентская линия -->
                <div class="py-3">
                    <div class="text-xl font-semibold p-5">Абонентская линия</div>

                    <div class="ml-40">
                        <End3CollapsedView
                            @getInfo="(index) => getEnd3DetailInfo(oltID, index)"
                            @deleteInfo="(index) => deleteEnd3DetailInfo(oltID, index)"
                            @deletedEnd3="(_end3, end3Index) => deleteEnd3FromList(oltID, end3Index)"
                            @createNewEnd3="(newEnd3List) => createNewEnd3(oltID, newEnd3List)"
                            :customer-lines="oltState.customerLines"
                            :user-permissions="userPermissions"
                            :edit-mode="editMode"
                            :device-name="oltState.statement.deviceName"
                            :device-port="oltState.statement.devicePort"
                            :building-address="detailDataAddress"
                        />
                    </div>
                </div>
            </template>
        </div>

        <div v-else class="flex justify-center p-4">
            <ProgressSpinner />
        </div>
    </div>
</template>

<script lang="ts">
import AddressGetCreate from "./components/AddressGetCreate.vue";
import BuildingIcon from "./components/BuildingIcon.vue";
import End3CollapsedView from "./components/End3CollapsedView.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import OltPortsSubscriberStatistic from "./components/OltPortsSubscriberStatistic.vue";
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";

import errorFmt, { getErrorStatus } from "@/errorFmt";
import { addEnd3, getBuildingTechData, getEnd3TechData, getGponPermissions } from "@/services/gpon";
import { formatAddress } from "@/formats";
import printElementById from "@/helpers/print";
import editMedia from "@/pages/deviceInfo/components/EditMedia.vue";
import { getRouteId } from "./gponRoute";
import type { BuildingTechData, CreateTechDataPayload, GponAddress, GponPermission, OltState } from "@/types/gpon";

export default {
    name: "ViewBuildingTechData",
    components: {
        OltPortsSubscriberStatistic,
        ViewPrintEditButtons,
        End3CollapsedView,
        AddressGetCreate,
        BuildingIcon,
        TechCapabilityBadge,
    },
    data() {
        return {
            detailData: null as BuildingTechData | null,
            errorStatus: null as number | string | null | undefined,
            errorMessage: null as string | null,
            windowWidth: window.innerWidth,
            userPermissions: [] as GponPermission[],
            editMode: false,
        };
    },
    mounted() {
        getGponPermissions().then((permissions) => {
            this.userPermissions = permissions;
        });
        this.getTechData();
        window.addEventListener("resize", () => {
            this.windowWidth = window.innerWidth;
        });
    },

    computed: {
        editMedia() {
            return editMedia;
        },
        isMobile() {
            return this.windowWidth <= 768;
        },

        detailDataAddress(): GponAddress | null {
            if (!this.detailData) {
                return null;
            }
            return {
                id: this.detailData.id,
                region: this.detailData.region,
                settlement: this.detailData.settlement,
                planStructure: this.detailData.planStructure,
                street: this.detailData.street,
                house: this.detailData.house,
                block: this.detailData.block,
                building_type: this.detailData.building_type,
                floors: this.detailData.floors,
                total_entrances: this.detailData.total_entrances,
            };
        },

        hasPermissionToUpdateOLTState() {
            return this.userPermissions.includes("gpon.change_oltstate");
        },

        hasPermissionToUpdateHouseOLTState() {
            return this.userPermissions.includes("gpon.change_houseoltstate");
        },

        hasPermissionToUpdateHouseB() {
            return this.userPermissions.includes("gpon.change_houseb");
        },

        hasAnyPermissionToUpdate() {
            return (
                this.hasPermissionToUpdateOLTState ||
                this.hasPermissionToUpdateHouseOLTState ||
                this.hasPermissionToUpdateHouseB
            );
        },
    },

    methods: {
        /** Loads the building and all GPON connections assigned to it. */
        getTechData(): void {
            getBuildingTechData(getRouteId(this.$route.params.id))
                .then((detailData) => (this.detailData = detailData))
                .catch((reason) => {
                    this.errorStatus = getErrorStatus(reason);
                    this.errorMessage = errorFmt(reason);
                });
        },

        /** Formats an address for the page header. */
        getFullAddress(address: GponAddress | null): string {
            return formatAddress(address);
        },

        /** Builds a link to the related OLT port page. */
        getOLTTechDataURL(statement: OltState): string {
            return "/gpon/tech-data/" + statement.deviceName + "?port=" + statement.devicePort;
        },

        /** Loads the ports for one collapsed endpoint. */
        getEnd3DetailInfo(oltID: number, end3Index: number): void {
            const customerLine = this.detailData?.oltStates[oltID]?.customerLines[end3Index];
            if (!customerLine) {
                return;
            }

            getEnd3TechData(customerLine.id)
                .then((end3) => (customerLine.detailInfo = end3.capability))
                .catch((reason) => {
                    customerLine.errorStatus = getErrorStatus(reason);
                    customerLine.errorMessage = errorFmt(reason);
                });
        },

        deleteEnd3DetailInfo(oltID: number, end3Index: number): void {
            const customerLine = this.detailData?.oltStates[oltID]?.customerLines[end3Index];
            if (customerLine) {
                customerLine.detailInfo = null;
            }
        },

        /** Prints the building technical data. */
        printData(): void {
            printElementById("tech-data-block");
        },

        deleteEnd3FromList(oltID: number, end3Index: number): void {
            this.detailData?.oltStates[oltID]?.customerLines.splice(end3Index, 1);
        },

        /**
         * Создаем новый сплиттер/райзер
         * @param {Number} oltID Индекс House OTL State в списке
         * @param {Object} newEnd3 Объект с новыми данными End3
         */
        createNewEnd3(oltID: number, newEnd3: CreateTechDataPayload["end3"]): void {
            const oltState = this.detailData?.oltStates[oltID];
            if (!oltState) {
                return;
            }
            const data = {
                houseOltStateID: oltState.id,
                end3: newEnd3,
            };
            const request = addEnd3(data);
            this.handleRequest(request, "Успешно создано").then(() => {
                // Обновляем все данные, чтобы загрузить новый перечень End3
                this.getTechData();
                // Очищаем список только что созданных End3
                newEnd3.list = [];
            });
        },

        /**
         * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
         * @param {Promise} request
         * @param {String} successInfo
         */
        handleRequest(request: Promise<unknown>, successInfo: string): Promise<void> {
            return request
                .then(() => {
                    this.$toast.add({ severity: "success", summary: "Обновлено", detail: successInfo, life: 3000 });
                })
                .catch((reason) => {
                    const status = getErrorStatus(reason);
                    this.$toast.add({
                        severity: "error",
                        summary: `Ошибка ${status}`,
                        detail: errorFmt(reason),
                        life: 5000,
                    });
                });
        },
    },
};
</script>

<style scoped>
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.grey-back {
    background-color: #ebebeb;
}

.ml-40 {
    margin-left: 40px;
}

@media (max-width: 835px) {
    .container {
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: 100% !important;
    }

    .w-75,
    .col-5 {
        width: 100% !important;
    }

    .plate {
        border: none;
    }

    .ml-40 {
        margin-left: 0;
    }

    .p-5 {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
}
</style>
