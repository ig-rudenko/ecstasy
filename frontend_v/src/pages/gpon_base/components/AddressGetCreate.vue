<template>
    <div v-if="!show_new_address_form">
        <div v-if="isSubscriberAddress" class="px-2 flex items-center gap-1">
            Укажите адрес подключения
            <Asterisk />
        </div>
        <h6 v-else class="px-2 flex items-center gap-1">
            Выберите существующий адрес дома
            <Asterisk />
        </h6>

        <div class="py-2">
            <Select
                v-model="data.address"
                fluid
                :options="addressesList()"
                filter
                showClear
                :loading="isLoading"
                :class="valid ? [] : ['p-invalid']"
                @change="(e) => $emit('change', e)"
                @filter="onAddressFilter"
                :virtualScrollerOptions="virtualScrollerOptions"
                :optionLabel="getFullAddress"
                placeholder="Выберите"
                class="mb-1 rounded-2xl"
            >
                <template #value="slotProps">
                    <div v-if="slotProps.value" class="items-center flex gap-2">
                        <BuildingIcon :type="slotProps.value.building_type" width="24" height="24"></BuildingIcon>
                        <div>{{ getFullAddress(slotProps.value) }}</div>
                    </div>
                    <span v-else>
                        {{ slotProps.placeholder }}
                    </span>
                </template>
                <template #option="slotProps">
                    <div v-if="slotProps.option" class="flex items-center gap-3">
                        <BuildingIcon :type="slotProps.option.building_type" width="24" height="24"></BuildingIcon>
                        <div>{{ getFullAddress(slotProps.option) }}</div>
                    </div>
                </template>
            </Select>

            <Button
                v-if="allowCreate"
                @click="show_new_address_form = true"
                severity="success"
                size="small"
                class="rounded-2xl"
            >
                Добавить/Редактировать
            </Button>
        </div>
    </div>

    <Dialog
        v-model:visible="show_new_address_form"
        modal
        header="Добавление нового адреса"
        :style="{ width: isMobile ? '100vw' : '50vw' }"
    >
        <AddressForm
            @valid="validNewAddress"
            @dismiss="dismissNewAddress"
            :subscriber-address="isSubscriberAddress"
            :init-address="buildInitAddress()"
        ></AddressForm>
    </Dialog>
</template>

<script>
import AddressForm from "./AddressForm.vue";
import Asterisk from "./Asterisk.vue";
import BuildingIcon from "./BuildingIcon.vue";

import { formatAddress } from "@/formats";
import api from "@/services/api";

export default {
    name: "AddressGetCreate",
    components: {
        AddressForm,
        Asterisk,
        BuildingIcon,
    },

    props: {
        isMobile: { required: true, type: Boolean },
        data: { required: true, type: Object },
        allowCreate: { required: false, default: true },
        getFromDevicePort: { required: false, default: null },
        isSubscriberAddress: { required: false, default: false },
        valid: { required: false, type: Boolean, default: true },
    },

    data() {
        return {
            show_new_address_form: false,
            _addresses: [],
            searchQuery: "",
            isLoading: false,
            hasNextPage: true,
            nextPage: 1,
            debounceTimer: null,
            pageSize: 20,
            formState: {
                address: { valid: true },
                isValid() {
                    return this.address.valid;
                },
            },
            _initData: null,
        };
    },

    mounted() {
        this.getAddresses({ reset: true });
        this._initData = this.getFromDevicePort;
    },

    updated() {
        if (
            this.getFromDevicePort &&
            (this._initData.deviceName !== this.getFromDevicePort.deviceName ||
                this._initData.devicePort !== this.getFromDevicePort.devicePort)
        ) {
            this.getAddresses({ reset: true });
            this._initData = this.getFromDevicePort;
        }
    },

    computed: {
        virtualScrollerOptions() {
            return {
                itemSize: 38,
                lazy: true,
                onLazyLoad: this.onAddressesLazyLoad,
                showLoader: true,
                loading: this.isLoading,
            };
        },
    },

    methods: {
        getFullAddress(address) {
            let address_string = formatAddress(address);
            if (this.isSubscriberAddress && address.building_type === "building") {
                address_string += ` (${address.floor} этаж) кв. ${address.apartment}`;
            }
            return address_string;
        },

        validNewAddress(newAddress) {
            this.show_new_address_form = false;
            this.formState.address.valid = true;
            const copiedAddress = this.normalizeAddress(newAddress);
            if (Object.prototype.hasOwnProperty.call(copiedAddress, "id")) {
                delete copiedAddress.id;
            }
            this.data.address = copiedAddress;
        },

        dismissNewAddress() {
            this.show_new_address_form = false;
            this.data.address = null;
        },

        getAddresses({ reset = false } = {}) {
            if (this.isLoading) return;
            if (!reset && !this.hasNextPage) return;

            if (reset) {
                this._addresses = [];
                this.nextPage = 1;
                this.hasNextPage = true;
            }

            let url = "/api/v1/gpon/addresses/buildings";
            if (this.getFromDevicePort) {
                url += `?device=${this.getFromDevicePort.deviceName}&port=${this.getFromDevicePort.devicePort}`;
            }

            this.isLoading = true;
            api.get(url, {
                params: {
                    page: this.nextPage,
                    page_size: this.pageSize,
                    search: this.searchQuery || undefined,
                },
            })
                .then((resp) => {
                    const newItems = resp.data.results || [];
                    this._addresses = [...this._addresses, ...newItems];
                    this.hasNextPage = Boolean(resp.data.next);
                    this.nextPage += 1;
                })
                .finally(() => {
                    this.isLoading = false;
                });
        },

        onAddressFilter(event) {
            this.searchQuery = (event.value || "").trim();
            if (this.debounceTimer) clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.getAddresses({ reset: true });
            }, 250);
        },

        onAddressesLazyLoad(event) {
            if (!event) return;
            const remaining = this._addresses.length - event.last;
            if (remaining <= 5) {
                this.getAddresses();
            }
        },

        addressesList() {
            let allAddresses = this._addresses;
            if (this.formState.isValid() && this.allowCreate && this.data.address) {
                allAddresses = [this.data.address, ...this._addresses.filter((item) => item.id !== this.data.address.id)];
            }
            return allAddresses;
        },

        buildInitAddress() {
            if (this.data.address) {
                return this.normalizeAddress(this.data.address);
            }
            return this.getNewAddress();
        },

        normalizeAddress(address) {
            return {
                id: address?.id ?? undefined,
                region: address?.region ?? "",
                settlement: address?.settlement ?? "",
                planStructure: address?.planStructure ?? "",
                street: address?.street ?? "",
                house: address?.house ?? "",
                block: address?.block ?? null,
                floor: address?.floor ?? null,
                apartment: address?.apartment ?? null,
                building_type: address?.building_type ?? "building",
                floors: address?.floors ?? 1,
                total_entrances: address?.total_entrances ?? 1,
            };
        },

        getNewAddress() {
            return {
                region: "Севастополь",
                settlement: "Севастополь",
                planStructure: "",
                street: "",
                house: "",
                block: null,
                building_type: "building",
                floors: 1,
                total_entrances: 1,
            };
        },
    },
};
</script>

<style scoped></style>
