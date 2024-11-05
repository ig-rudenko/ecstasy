import {
    Avatar,
    Badge,
    Button,
    Column,
    DataTable,
    Dialog,
    Drawer,
    IftaLabel,
    InputGroup,
    InputNumber,
    InputText,
    Image,
    Menubar,
    Message,
    Paginator,
    Password,
    ProgressSpinner,
    Popover,
    Ripple,
    ScrollTop,
    Select,
    Textarea,
    ToggleSwitch,
    Tooltip
} from "primevue";
import ToastService from "primevue/toastservice";

import "@/assets/base.css";
import 'primeicons/primeicons.css';

import {app} from '@/appInstance';
import store from "@/store";
import router from "@/router";
import setupInterceptors from '@/services/api/setupInterceptors';

setupInterceptors();
app.directive('ripple', Ripple);
app.directive('tooltip', Tooltip);
app.use(ToastService);
app.use(store);
app.use(router);

app.component("Avatar", Avatar);
app.component("Badge", Badge);
app.component("Button", Button);
app.component("Column", Column);
app.component("DataTable", DataTable);
app.component("Dialog", Dialog);
app.component("Drawer", Drawer);
app.component("IftaLabel", IftaLabel);
app.component("InputGroup", InputGroup);
app.component("InputNumber", InputNumber);
app.component("Image", Image);
app.component("InputText", InputText);
app.component("Menubar", Menubar);
app.component("Message", Message);
app.component("Password", Password);
app.component("Paginator", Paginator);
app.component("ProgressSpinner", ProgressSpinner);
app.component("Popover", Popover);
app.component("ScrollTop", ScrollTop);
app.component("Select", Select);
app.component("Textarea", Textarea);
app.component("ToggleSwitch", ToggleSwitch);

app.mount('#app');
