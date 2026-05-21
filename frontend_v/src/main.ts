import {
    Avatar,
    Badge,
    Button,
    Checkbox,
    Column,
    ConfirmationService,
    ConfirmPopup,
    DataTable,
    DatePicker,
    Dialog,
    Divider,
    Drawer,
    Fieldset,
    FloatLabel,
    IconField,
    IftaLabel,
    Image,
    InlineMessage,
    InputGroup,
    InputIcon,
    InputMask,
    InputNumber,
    InputText,
    Menubar,
    Message,
    OverlayBadge,
    Paginator,
    Password,
    Popover,
    ProgressSpinner,
    RadioButton,
    Ripple,
    ScrollTop,
    Select,
    SplitButton,
    Textarea,
    ToggleSwitch,
    Tooltip,
} from "primevue";
import ToastService from "primevue/toastservice";

import "@/assets/base.css";
import "primeicons/primeicons.css";

import { app } from "@/appInstance";
import store from "@/store";
import router from "@/router";
import setupInterceptors from "@/services/api/setupInterceptors";
import { initializeOIDC, isOIDCLogin } from "@/oidc";

setupInterceptors();
app.directive("ripple", Ripple);
app.directive("tooltip", Tooltip);
app.use(ToastService);
app.use(ConfirmationService);
app.use(store);
app.use(router);

app.component("Avatar", Avatar);
app.component("Badge", Badge);
app.component("Button", Button);
app.component("Checkbox", Checkbox);
app.component("Column", Column);
app.component("ConfirmPopup", ConfirmPopup);
app.component("DatePicker", DatePicker);
app.component("DataTable", DataTable);
app.component("Dialog", Dialog);
app.component("Divider", Divider);
app.component("Drawer", Drawer);
app.component("IconField", IconField);
app.component("IftaLabel", IftaLabel);
app.component("InlineMessage", InlineMessage);
app.component("InputGroup", InputGroup);
app.component("InputIcon", InputIcon);
app.component("InputNumber", InputNumber);
app.component("Image", Image);
app.component("InputMask", InputMask);
app.component("InputText", InputText);
app.component("Fieldset", Fieldset);
app.component("FloatLabel", FloatLabel);
app.component("Menubar", Menubar);
app.component("Message", Message);
app.component("OverlayBadge", OverlayBadge);
app.component("Password", Password);
app.component("Paginator", Paginator);
app.component("ProgressSpinner", ProgressSpinner);
app.component("Popover", Popover);
app.component("RadioButton", RadioButton);
app.component("ScrollTop", ScrollTop);
app.component("Select", Select);
app.component("SplitButton", SplitButton);
app.component("Textarea", Textarea);
app.component("ToggleSwitch", ToggleSwitch);

initializeOIDC()
    .then(() => {
        if (isOIDCLogin()) {
            store.dispatch("auth/oidcLogin");
        }
    })
    .finally(() => {
        app.mount("#app");
    });
