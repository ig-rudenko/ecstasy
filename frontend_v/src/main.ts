import Avatar from "primevue/avatar";
import Badge from "primevue/badge";
import Button from "primevue/button";
import ButtonGroup from "primevue/buttongroup";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from 'primevue/datatable';
import Dialog from "primevue/dialog";
import IconField from "primevue/iconfield";
import InputNumber from "primevue/inputnumber";
import Image from "primevue/image";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import {IftaLabel, Menubar, Message, Password} from "primevue";
import Paginator from "primevue/paginator";
import ProgressSpinner from "primevue/progressspinner";
import Popover from "primevue/popover";
import Drawer from "primevue/drawer";
import Ripple from "primevue/ripple";
import SelectButton from "primevue/selectbutton";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import Timeline from "primevue/timeline";
import Tooltip from 'primevue/tooltip';
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
app.component("ButtonGroup", ButtonGroup);
app.component("Card", Card);
app.component("Column", Column);
app.component("DataTable", DataTable);
app.component("Dialog", Dialog);
app.component("Drawer", Drawer);
app.component("IconField", IconField);
app.component("IftaLabel", IftaLabel);
app.component("InputNumber", InputNumber);
app.component("Image", Image);
app.component("InputIcon", InputIcon);
app.component("InputText", InputText);
app.component("Menubar", Menubar);
app.component("Message", Message);
app.component("Password", Password);
app.component("Paginator", Paginator);
app.component("ProgressSpinner", ProgressSpinner);
app.component("Popover", Popover);
app.component("SelectButton", SelectButton);
app.component("Splitter", Splitter);
app.component("SplitterPanel", SplitterPanel);
app.component("Timeline", Timeline);

app.mount('#app');
