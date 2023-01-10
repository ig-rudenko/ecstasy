<template src="./App_devices_list.html"></template>

<script>
import DevicesTable from "./components/DevicesTable.vue";

export default {
    name: 'devices',
    data() {
        return {
            imageIndex: 0,
            count: 0,
            page: 0,
            rows_per_page: 50,
            next_page: "",
            devices: function () { return [] },
            search: "",
            groups: function () { return [] },
            selectedGroup: "",
            vendors: function () { return [] },
            selectedVendor: "",
        }
    },
    methods: {
        changeImageIndex: function () {
              let min = Math.ceil(1);
              let max = Math.floor(5);
              this.imageIndex = Math.floor(Math.random() * (max - min + 1)) + min;
        },
        /* Метод вызывается при создании
        *  */
        async getDevices(){
            try {
                let response = await fetch(
                    "/device/api/list_all",
                    {method: 'GET', credentials: "same-origin"}
                );
                let data = await response.json()

                this.devices = data
                this.count = data.length

                let devices_groups = []
                let devices_vendors = []
                for (let dev of this.devices) {
                    if (dev.group && devices_groups.indexOf(dev.group) === -1){
                        devices_groups.push(dev.group || "")
                    }
                    if (dev.vendor && devices_vendors.indexOf(dev.vendor) === -1){
                        devices_vendors.push(dev.vendor)
                    }
                }
                this.groups = devices_groups
                this.vendors = devices_vendors

            } catch (error) {
                console.log(error)
            }
        },
        goToPage: function (num) {
            if (num <= 0) {
                this.page = 0
            } else if (num >= this.num_pages){
                this.page = this.num_pages - 1
            } else {
                this.page = num - 1
            }
        },
        changeVendor: function (event) {
            this.selectedVendor = event.target.value || ""
        },
        changeGroup: function (event) {
            this.selectedGroup = event.target.value || ""
        }
    },
    computed: {
        num_pages: function () {
            return Math.floor(this.count / this.rows_per_page) + 1
        },
        filteredDevices: function () {
            let search_str = this.search.toLowerCase()
            let vendor = this.selectedVendor
            let group = this.selectedGroup

            let array = Array.from(this.devices).filter(function (elem) {

                if (vendor && elem.vendor !== vendor) {
                    return false
                }
                if (group && elem.group !== group) {
                    return false
                }

                if (search_str==="") return true;

                let name = elem.name.toLowerCase()
                let ip = elem.ip.toLowerCase()
                return name.indexOf(search_str) > -1 || ip.indexOf(search_str) > -1
            })
            this.count = array.length
            // обрезаем по размеру страницы
            let slice_array = array.slice(this.page*this.rows_per_page, (this.page + 1)*this.rows_per_page)
            if (array.length && slice_array.length === 0){
                // Если имеются данные по фильтру, но в срезе их нет, надо сбросить страницу
                this.page = 0

                // Новый срез
                slice_array = array.slice(this.page*this.rows_per_page, (this.page + 1)*this.rows_per_page)
            }

            this.changeImageIndex()

            return slice_array
        }
    },
    created(){
        this.getDevices()
        this.changeImageIndex()
    },
    components: {
        "devices-table": DevicesTable,
    }
}
</script>