import {createApp} from "vue";
import {definePreset} from "@primeuix/themes";
import PrimeVue from "primevue/config";
import Aura from '@primeuix/themes/aura';
import App from "@/App.vue";

const MyPreset = definePreset(Aura, {
    semantic: {
        primary: {
            50: '{indigo.50}',
            100: '{indigo.100}',
            200: '{indigo.200}',
            300: '{indigo.300}',
            400: '{indigo.400}',
            500: '{indigo.500}',
            600: '{indigo.600}',
            700: '{indigo.700}',
            800: '{indigo.800}',
            900: '{indigo.900}',
            950: '{indigo.950}'
        },
        colorScheme: {
            dark: {
                formField: {
                    background: 'rgba(17, 24, 39, 0.72)',
                    filledBackground: 'rgba(55, 65, 81, 0.65)',
                    filledHoverBackground: 'rgba(75, 85, 99, 0.7)',
                    filledFocusBackground: 'rgba(75, 85, 99, 0.75)',
                    disabledBackground: '{surface.600}',
                    borderColor: 'rgba(75, 85, 99, 0.85)',
                    hoverBorderColor: 'rgba(107, 114, 128, 0.9)',
                    focusBorderColor: '{primary.color}',
                    color: '{text.color}',
                    iconColor: '{text.muted.color}',
                },
                overlay: {
                    select: {
                        background: 'rgba(31, 41, 55, 0.96)',
                        borderColor: 'rgba(75, 85, 99, 0.65)',
                        color: '{text.color}',
                    },
                    popover: {
                        background: 'rgba(31, 41, 55, 0.96)',
                        borderColor: 'rgba(75, 85, 99, 0.65)',
                        color: '{text.color}',
                    },
                    modal: {
                        background: 'rgba(31, 41, 55, 0.96)',
                        borderColor: 'rgba(75, 85, 99, 0.65)',
                        color: '{text.color}',
                    },
                },
                list: {
                    option: {
                        focusBackground: 'rgba(55, 65, 81, 0.85)',
                        selectedFocusBackground: '{highlight.focus.background}',
                    },
                },
            },
        },
    }
});

export const app = createApp(App);
app.use(PrimeVue, {
    ripple: true, theme: {
        preset: MyPreset,
        options: {
            darkModeSelector: '.dark',
            cssLayer: {
                name: 'primevue',
                order: 'base, primevue, tailwind-utilities'
            }
        }
    }
});