<template src="./App_devices_list.html"></template>

<script>
import DevicesTable from "./components/DevicesTable.vue";
import Pagination from "./components/Pagination.vue";
import SearchInput from "./components/SearchInput.vue";

export default {
  name: 'devices',
  data() {
    return {
      imageIndex: 0,
      pagination: {
        count: 0,
        page: 0,
        rows_per_page: 50,
        next_page: null,
      },
      devices: function () { return [] },
      search: "",
      groups: function () { return [] },
      selectedGroup: "",
      vendors: function () { return [] },
      selectedVendor: "",
      displayMode: "default"
    }
  },
  methods: {
    updateSearch: function (event) {
      this.search = event.target.value.trim()
    },

    changeImageIndex: function () {
      let min = Math.ceil(1);
      let max = Math.floor(5);
      this.imageIndex = Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /** Метод вызывается при создании */
    async getDevices(){
      try {
        let response = await fetch(
            "/device/api/list_all",
            {method: 'GET', credentials: "same-origin"}
        );
        let data = await response.json()

        // Список устройств
        this.devices = data || []

        // Кол-во устройств
        this.pagination.count = data.length || 0

        // Режим по умолчанию
        this.displayMode = "default"

        let devices_groups = []
        let devices_vendors = []
        // Определяем список уникальных имен вендоров и групп
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
    async getDeviceWithStats(){
      try {

        // Включаем режим отображения как "загружается"
        this.displayMode = "waiting"

        let response = await fetch(
            "/device/api/statistic/interfaces?free=1&up=1&admin_down=1&abons=1",
            {method: 'GET', credentials: "same-origin"}
        );
        let data = await response.json()

        // Список устройств
        this.devices = data.devices || []

        // Кол-во устройств
        this.pagination.count = data.devices_count || 0

        // Включаем режим отображения нагрузки по интерфейсам
        this.displayMode = "interfaces_loading"

        let devices_groups = []
        let devices_vendors = []
        // Определяем список уникальных имен вендоров и групп
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

    setVendor: function (vendor) {
      this.selectedVendor = vendor
      this.changeImageIndex()
    },
    setGroup: function (group) {
      this.selectedGroup = group
      this.changeImageIndex()
    }
  },
  computed: {
    filteredDevices: function () {
      let search_str = this.search.toLowerCase()
      let vendor = this.selectedVendor
      let group = this.selectedGroup

      // Фильтруем список устройств
      let array = Array.from(this.devices)
          .filter(
              function (elem) {
                if (vendor && elem.vendor !== vendor) {
                    return false
                }
                if (group && elem.group !== group) {
                    return false
                }

                if (search_str === "") return true;

                if (search_str.match(/^::load([<>=])(\d+)/i) && elem.interfaces_count) {
                  let match = search_str.match(/^::load([<>=])(\d+)/i)
                  let load = match[2]
                  let operator = match[1]

                  let device_loading = elem.interfaces_count.abons_up / elem.interfaces_count.abons * 100
                  if (operator === "<") {
                    return device_loading <= Number(load)
                  }
                  if (operator === ">") {
                    return device_loading >= Number(load)
                  }
                  if (operator === "=") {
                    return device_loading === Number(load)
                  }
                }

                let name = elem.name.toLowerCase()
                let ip = elem.ip.toLowerCase()
                return name.indexOf(search_str) > -1 || ip.indexOf(search_str) > -1
              }
          )

      this.pagination.count = array.length

      // Обрезаем по размеру страницы
      let slice_array = array.slice(
          this.pagination.page * this.pagination.rows_per_page,
          (this.pagination.page + 1) * this.pagination.rows_per_page
      )

      if (array.length && slice_array.length === 0) {
        // Если имеются данные по фильтру, но в срезе их нет, надо сбросить страницу
        this.pagination.page = 0

        // Новый срез
        slice_array = array.slice(
            this.pagination.page * this.pagination.rows_per_page,
            (this.pagination.page + 1) * this.pagination.rows_per_page)
      }

      return slice_array
    }
  },
  created(){
    this.getDevices()
    this.changeImageIndex()
  },
  components: {
    "devices-table": DevicesTable,
    "pagination": Pagination,
    "search-form": SearchInput,
  }
}
</script>