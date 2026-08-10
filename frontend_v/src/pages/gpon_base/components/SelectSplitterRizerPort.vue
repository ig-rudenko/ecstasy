<template>
    <h6 class="px-2 flex items-center gap-1 pb-2">
        Выберите {{ verboseType }}
        <Asterisk />
    </h6>
    <Select
        v-model="selectedPort"
        :options="capability"
        filter
        showClear
        @change="(e) => $emit('change', e)"
        :class="valid ? '' : 'p-invalid'"
        class="rounded-2xl"
        optionLabel="port"
        placeholder="Выберите"
    >
        <template #value="slotProps">
            <div v-if="slotProps.value" class="flex items-center">
                <div>
                    {{ slotProps.value.number }}
                    <template v-if="type === 'rizer'">
                        <span class="rizer-fiber-wrap ml-2">
                            <span
                                class="rizer-fiber-circle"
                                :class="fiberInfo(slotProps.value.number)?.className"
                            ></span>
                            <span v-if="fiberInfo(slotProps.value.number)?.marked" class="rizer-fiber-marked"></span>
                            <span class="rizer-fiber-name">{{ fiberInfo(slotProps.value.number)?.name }}</span>
                        </span>
                    </template>
                    <TechCapabilityBadge :status="slotProps.value.status" />
                </div>
            </div>
            <span v-else>
                {{ slotProps.placeholder }}
            </span>
        </template>
        <template #option="slotProps">
            <div v-if="slotProps.option" class="flex items-center">
                <div>
                    {{ slotProps.option.number }}
                    <template v-if="type === 'rizer'">
                        <span class="rizer-fiber-wrap ml-2">
                            <span
                                class="rizer-fiber-circle"
                                :class="fiberInfo(slotProps.option.number)?.className"
                            ></span>
                            <span v-if="fiberInfo(slotProps.option.number)?.marked" class="rizer-fiber-marked"></span>
                            <span class="rizer-fiber-name">{{ fiberInfo(slotProps.option.number)?.name }}</span>
                        </span>
                    </template>
                    <TechCapabilityBadge :status="slotProps.option.status" />
                </div>
            </div>
        </template>
    </Select>
</template>

<script lang="ts">
import TechCapabilityBadge from "./TechCapabilityBadge.vue";

import Asterisk from "./Asterisk.vue";
import errorFmt, { getErrorStatus } from "@/errorFmt";
import { getEnd3TechData } from "@/services/gpon";
import type { PropType } from "vue";
import type { End3Type, End3WithCapability, TechCapability } from "@/types/gpon";
import { getRizerFiberInfo } from "./rizerFiberColors.ts";

export default {
    name: "SelectSplittersRizersPort",
    components: {
        Asterisk,
        TechCapabilityBadge,
    },
    emits: ["change"],
    props: {
        type: { required: true, type: String as PropType<End3Type> },
        getFrom: { required: true, type: Object as PropType<End3WithCapability> },
        end3ID: { required: true, type: Number },
        init: {
            required: false,
            type: Object as PropType<Pick<TechCapability, "number" | "status"> | null>,
            default: null,
        },
        onlyUnusedPorts: { required: false, type: Boolean, default: false },
        valid: { required: false, type: Boolean, default: true },
    },

    data() {
        return {
            selectedPort: null as Pick<TechCapability, "number" | "status"> | null,
            _capability: [] as TechCapability[],
            _initEnd3ID: null as number | null,
            error: {
                status: null as number | string | null,
                message: null as string | null,
            },
        };
    },

    mounted() {
        this.getPorts();
        this.selectedPort = this.init;
        this._initEnd3ID = this.end3ID;
    },

    updated() {
        if (this.end3ID !== this._initEnd3ID) {
            this.getPorts();
            this._initEnd3ID = this.end3ID;
        }
    },

    computed: {
        capability() {
            const onlyUnusedPorts = this.onlyUnusedPorts;

            return this._capability.filter((elem) => {
                if (onlyUnusedPorts) {
                    return elem.status === "empty";
                }
                return true;
            });
        },

        verboseType() {
            if (this.type === "splitter") return "порт сплиттера";
            if (this.type === "rizer") return "волокно райзера";
        },
    },
    methods: {
        /** Returns display metadata for a riser fiber number. */
        fiberInfo(number: number): ReturnType<typeof getRizerFiberInfo> {
            return getRizerFiberInfo(number);
        },
        /** Loads ports of the selected splitter or riser. */
        async getPorts(): Promise<void> {
            try {
                const end3 = await getEnd3TechData(this.end3ID);
                this._capability = end3.capability;
            } catch (reason) {
                this.error.status = getErrorStatus(reason) ?? null;
                this.error.message = errorFmt(reason);
            }
        },
    },
};
</script>
