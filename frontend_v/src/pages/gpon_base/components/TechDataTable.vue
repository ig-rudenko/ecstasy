<template>
  <div class="table-plate shadow-xl dark:shadow-gray-500 rounded">
    <div>
      <Button @click="show_filter = !show_filter" class="filter-button" outlined>
        <svg v-if="filteredData.length !== data.length" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
             fill="#8B83BA" viewBox="0 0 16 16">
          <path
              d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#8B83BA" class="me-1"
             viewBox="0 0 16 16">
          <path
              d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2zm1 .5v1.308l4.372 4.858A.5.5 0 0 1 7 8.5v5.306l2-.666V8.5a.5.5 0 0 1 .128-.334L13.5 3.308V2h-11z"/>
        </svg>
        <div>Фильтрация</div>
      </Button>

      <!-- ФИЛЬТР -->
      <div v-show="show_filter" id="filter"
           class="table-plate rounded-xl filter-plate border bg-gray-50 dark:bg-gray-900 p-4">
        <div class="flex flex-wrap">
          <div style="width: 200px" class="me-2">
            <label for="filter-region" class="mx-2">Регион</label>
            <InputText style="width: 200px" id="filter-region" v-model.trim="filter.address.region" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-settlement" class="mx-2">Населенный пункт</label>
            <InputText style="width: 200px" id="filter-settlement" v-model.trim="filter.address.settlement" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-planStructure" class="mx-2">СНТ/ТСН</label>
            <InputText style="width: 200px" id="filter-planStructure" v-model.trim="filter.address.planStructure"
                       @keydown.enter="doFilter"/>
          </div>
        </div>

        <div class="flex flex-wrap">
          <div style="width: 300px" class="me-2">
            <label for="filter-street" class="mx-2 form-check-label">Улица/проспект</label>
            <InputText style="width: 300px" id="filter-street" v-model.trim="filter.address.street" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 100px" class="me-2">
            <label for="filter-house" class="mx-2 form-check-label">Дом</label>
            <InputText style="width: 100px" id="filter-house" v-model.trim="filter.address.house" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 100px" class="me-2">
            <label for="filter-block" class="mx-2 form-check-label">Корпус</label>
            <InputText style="width: 100px" id="filter-block" v-model.number="filter.address.block" type="text"
                       @keydown.enter="doFilter"/>
          </div>
        </div>

        <div class="flex flex-wrap">
          <div style="width: 300px" class="me-2">
            <label for="filter-deviceName" class="mx-2 form-check-label">Название оборудования</label>
            <InputText style="width: 300px" id="filter-deviceName" v-model.trim="filter.deviceName" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-devicePort" class="mx-2 form-check-label">Порт OLT</label>
            <InputText style="width: 200px" id="filter-devicePort" v-model="filter.devicePort" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <Button class="search-button dark:!text-white" outlined severity="success" @click="doFilter">Поиск</Button>
        </div>
      </div>

    </div>

    <!-- TABLE -->
    <div class="overflow-auto">
      <table :style="{opacity: show_filter?0.4:1}" class="w-full">
        <thead class="dark:border-gray-600 border-b-2">
        <tr>
          <th scope="col" class="py-2">Адрес</th>
          <th scope="col" class="py-2">Порт olt</th>
          <th scope="col" class="py-2">Абонентская линия</th>
          <th scope="col" class="py-2"></th>
        </tr>
        </thead>

        <tbody>
        <tr v-for="line in tableData"
            class="dark:hover:bg-gray-800 hover:bg-purple-50 dark:border-gray-600 border-b-2">

          <!-- АДРЕС -->
          <td class="items-center flex font-bold py-2 px-10 gap-3">
            <BuildingIcon :type="line.building_type" width="32" height="32"/>
            <div>
              <span @click="goToBuildingDetailView(line.building_id)"
                    class="address-name dark:text-gray-300">{{ getFullAddress(line.address) }}</span>
              <br>
              <span class="secondary-text">{{ line.address.settlement || line.address.region }}</span>
            </div>
          </td>

          <!-- ПОРТ OLT -->
          <td>
            <div class="items-center flex gap-2 px-10">
              <span class="secondary-text">{{ line.deviceName }}</span>
              <Pill @click="goToOLTDetailView(line.deviceName, line.devicePort)" :hover="true"
                    :text="line.devicePort"/>
              <span class="secondary-text">
                <span class="me-2">подъезды:</span>
                <span class="font-mono font-bold text-[0.9rem]">{{ line.entrances }}</span>
              </span>
            </div>
          </td>

          <!-- АБОНЕНТСКАЯ ЛИНИЯ -->
          <td>
            <div class="px-10 flex items-center gap-2">
              <Pill :text="customerLineTypeName(line.customerLine.type) + ' x' + line.customerLine.typeCount"
                    :color="customerLineTypeColor(line.customerLine.type)"
                    :back-color="customerLineTypeBackColor(line.customerLine.type)">
              </Pill>
              <span class="secondary-text">
                <span class="me-2">Кол-во:</span>
                <span class="font-mono font-bold text-[1rem]">{{ line.customerLine.count }}</span>
              </span>
            </div>
          </td>

        </tr>
        </tbody>
      </table>
    </div>

    <!-- TABLE FOOTER -->
    <Paginator :paginator="paginator" :data-length="filteredData.length"/>

  </div>
</template>

<script>
import Pill from "./Pill.vue";
import BuildingIcon from "./BuildingIcon.vue";
import Paginator from "./Paginator.vue";

export default {
  name: "Table",
  components: {
    BuildingIcon,
    Paginator,
    Pill,
  },
  props: {
    data: {required: true}
  },
  data() {
    return {
      paginator: {
        max_pages: 0,
        pages: {
          rows_per_page: 10
        },
        limit_offset: 0,
        current_page: 1,
      },

      show_filter: false,
      filteredData: this.data,
      filter: {
        address: {
          region: "",
          settlement: "",
          planStructure: "",
          street: "",
          house: "",
          block: null,
        },
        deviceName: "",
        devicePort: ""
      }
    }
  },

  mounted() {
    let urlObj = new URL(window.location.href);
    this.current_page = Number(urlObj.searchParams.get("page")) || 1
    this.doFilter()
  },

  computed: {
    tableData() {
      if (this.paginator.limit_offset >= this.filteredData.length) {
        this.paginator.current_page = 1
      }
      return this.filteredData.slice(
          this.paginator.limit_offset,
          this.paginator.limit_offset + this.paginator.pages.rows_per_page
      )
    }
  },

  methods: {

    getFullAddress(address) {
      let str = ""
      if (address.planStructure.length) str += `СНТ ${address.planStructure},`;
      if (address.street.length) str += ` ${address.street},`;
      str += ` д. ${address.house}`;
      if (address.block) str += `/${address.block}`;
      return str
    },

    doFilter() {
      let address_filter = this.filter.address
      let devicePort_filter = this.filter.devicePort
      let deviceName_filter = this.filter.deviceName

      this.filteredData = Array.from(this.data).filter(
          function (elem) {

            // Поиск по адресу
            const match_region = address_filter.region.length === 0 || elem.address.region.toLowerCase().indexOf(address_filter.region.toLowerCase()) > -1
            const match_settlement = address_filter.settlement.length === 0 || elem.address.settlement.toLowerCase().indexOf(address_filter.settlement.toLowerCase()) > -1
            const match_planStructure = address_filter.planStructure.length === 0 || elem.address.planStructure.toLowerCase().indexOf(address_filter.planStructure.toLowerCase()) > -1
            const match_street = address_filter.street.length === 0 || elem.address.street.toLowerCase().indexOf(address_filter.street.toLowerCase()) > -1
            const match_house = address_filter.house.length === 0 || elem.address.house.toLowerCase().indexOf(address_filter.house.toLowerCase()) > -1
            const match_block = !address_filter.block || address_filter.block === elem.address.block

            // Поиск по OLT порту
            const match_devicePort = devicePort_filter.length === 0 || elem.devicePort.toLowerCase().indexOf(devicePort_filter.toLowerCase()) > -1
            const match_deviceName = deviceName_filter.length === 0 || elem.deviceName.toLowerCase().indexOf(deviceName_filter.toLowerCase()) > -1

            return match_region && match_settlement && match_planStructure && match_street && match_house && match_block && match_devicePort && match_deviceName
          }
      )
      this.show_filter = false
    },

    customerLineTypeName(type) {
      if (type === "splitter") {
        return "Сплиттер"
      } else if (type === "rizer") {
        return "Райзер"
      } else {
        return type
      }
    },
    customerLineTypeBackColor(type) {
      if (type === "splitter") {
        return "#CDFFCD"
      } else if (type === "rizer") {
        return "#DAE8FC"
      } else {
        return "#f2dafc"
      }
    },
    customerLineTypeColor(type) {
      if (type === "splitter") {
        return "#007F00"
      } else if (type === "rizer") {
        return "#7572FF"
      } else {
        return "#d572ff"
      }
    },

    goToOLTDetailView(device_name, olt_port) {
      window.location.href = `/gpon/tech-data/${device_name}?port=${olt_port}`
    },

    goToBuildingDetailView(houseID) {
      window.location.href = `/gpon/tech-data/building/${houseID}`
    }
  }
}
</script>

<style scoped>

.address-name {
  cursor: pointer;
}

.address-name:hover {
  color: #2198ff;
}

.olt-port-badge:hover {
  cursor: pointer;
  box-shadow: 0 .5rem 1rem rgba(0, 0, 0, .15) !important;
  border: 1px solid #a48eff;
}

.search-button {
  font-size: 14px;
  margin-top: 23px;
  border: 1px solid green;
  padding: 6px 30px;
  border-radius: 14px;
  color: darkgreen;
}

.search-button:hover {
  box-shadow: 0 0 3px green;
}

label {
  font-size: 12px;
  font-weight: 700;
}

input[type=text] {
  border-radius: 14px;
  font-size: 14px;
}

table {
  margin: 0;
}

thead {
  color: #6E6893;
  font-size: 12px;
  text-transform: uppercase;
}

tbody {
  color: #25213B;
}

tr, tr * {
  text-wrap: nowrap;
}

.filter-button {
  margin: 15px;
  padding: 7px 10px;
  border-radius: 6px;
}

.secondary-text {
  color: #6E6893;
  font-size: 14px;
  font-weight: 500;
}

.secondary-text:where(.dark, .dark *) {
  color: #9088c3;
}

.table-plate {
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.20);
}

.filter-plate {
  width: max-content;
  position: absolute;
  z-index: 10;
}

@media (max-width: 770px) {
  .filter-plate {
    width: 450px
  }
}

@media (max-width: 500px) {
  .filter-plate {
    max-width: 450px;
    width: min-content;
    margin: 0;
  }
}

</style>