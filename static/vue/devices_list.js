/* Компонент. */
Vue.component("device-info", {
    props: ["dev"],
    template: `<tr>
                  <td>
                      <a class="badge rounded-pill bg-primary text-light text-decoration-none"
                         style="font-family: 'Yu Gothic UI Semilight', monospace; font-size: 1rem"
                         data-bs-toggle_help="tooltip" data-bs-placement="top"
                         data-bs-title="Просканировать интерфейсы в реальном времени"
                         :href="'/device/' + dev.name + '?current_status=1'"
                      >I</a>
                      
                      <a v-if="dev.port_scan_protocol !== 'snmp'"
                         class="badge rounded-pill bg-info text-dark text-decoration-none"
                         style="font-family: 'Yu Gothic UI Semilight', monospace; font-size: 1rem"
                         data-bs-toggle_help="tooltip" data-bs-placement="top"
                         data-bs-title="Просканировать интерфейсы и VLANS в реальном времени"
                         :href="'/device/' + dev.name + '?current_status=1&vlans=1'"
                      >V</a>
                      
                      <a class="badge rounded-pill bg-secondary text-decoration-none"
                         style="font-family: 'Yu Gothic UI Semilight', monospace; font-size: 1rem"
                         data-bs-toggle_help="tooltip" data-bs-placement="top"
                         data-bs-title="Последние сохраненные интерфейсы"
                         :href="'/device/' + dev.name"
                      >L</a>
                  </td>
                  <td><span class="nowrap">{{ dev.name }}</span></td>
                  <td>{{ dev.ip }}</td>
                  <td>{{ dev.vendor }}</td>
                  <td>{{ dev.model }}</td>
                  <td>{{ dev.group }}</td>
                </tr>`
});

/* Компонент. */
Vue.component("device-table", {
    props: ["devices"],
    template: `<table class="table table-striped">
                  <thead>
                    <tr>
                      <th scope="col"></th>
                      <th scope="col">Имя</th>
                      <th scope="col">IP</th>
                      <th scope="col">Тип</th>
                      <th scope="col">Модель</th>
                      <th scope="col">Группа</th>
                    </tr>
                  </thead>
                  <tbody>
                        <device-info v-for="dev in devices" v-bind:dev="dev"></device-info>
                  </tbody>
                </table>`
})

/* Компонент. */
Vue.component("vendor-select", {
    props: ["vendors"],
    data: function () {
        return { selected: "" }
    },
    "template": `<select class="form-select" v-model="selected" v-on:onchange="onUpdateSelect">
                     <option >Все вендоры</option>
                     <option v-for="vendor in vendors" v-bind:value="vendor">{{vendor}}</option>
                 </select>`,
    methods: {
        onUpdateSelect: function () {
            console.log('update')
            console.log(this.selected)
            this.$emit("changeSelect", this.selected)
        }
    }
})

/* Компонент. */
Vue.component("info", {
    props: ["s"],
    "template": `<p>S - {{s}}</p>`
})

/* Шаблон для Vue.js */
let app_template = `<div>
    <div class="row py-2">
        <div class="col-6">
            <h4 class="fw-bold py-4">Выберите оборудование</h4>
        </div>
        <div class="col-6" style="text-align: right">
            <img style="width: 100%" v-bind:src="'/static/img/device-icon-'+imageIndex+'.svg'" alt="search-description-image">
        </div>
    </div>
    
    <div class="input-group mb-3">
      <input type="text" class="form-control" placeholder="Введите IP или имя" aria-label="Поиск"
             aria-describedby="button-addon2"
             v-model.trim="search"
             autofocus>
    </div>
    
    <ul class="nav nav-tabs">
      
      <li class="nav-link text-dark">
        Всего найдено: {{ count }}
      </li>
      
      <li class="nav-item dropdown noselect">
        <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false">
            {{ selectedGroup || "Group" }}
        </a>
        <ul class="dropdown-menu" style="cursor: pointer">
              <span class="dropdown-item" @click="changeGroup" value="">Все группы</span>

              <option class="dropdown-item"
               v-for="group in groups" 
               @click="changeGroup" v-bind:value="group">{{ group }}</option>

        </ul>
      </li>
    
      <li class="nav-item dropdown noselect">
        <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown" href="#" role="button" aria-expanded="false">
            {{ selectedVendor || "Vendor" }}
        </a>
        <ul class="dropdown-menu" style="cursor: pointer">
              <span class="dropdown-item" @click="changeVendor" >Все вендоры</span>

              <option class="dropdown-item"
               v-for="vendor in vendors" 
               @click="changeVendor" v-bind:value="vendor">{{ vendor }}</option>

        </ul>
      </li>
    </ul>

    <nav aria-label="..." class="py-3 noselect">
        <ul v-if="num_pages > 1" class="pagination justify-content-center">

        <li v-if="page > 2" class="page-item" style="cursor: pointer">
            <a v-if="page > 2" @click="goToPage(0)" class="page-link">1 << </a>
            <a v-else class="page-link">1 << </a>
        </li>
        
        <li class="page-item" v-bind:class="{disabled: page === 0}" style="cursor: pointer">
          <a v-if="page === 0" class="page-link">Предыдущая</a>
          <a v-else @click="goToPage(page)" class="page-link">Предыдущая</a>
        </li>
        
        <li v-if="page !== 0" class="page-item" style="cursor: pointer">
            <a @click="goToPage(page)" class="page-link" >{{ page }}</a>
        </li>
        
        <li class="page-item active" aria-current="page" style="cursor: pointer">
          <a class="page-link">{{ page + 1 }}</a>
        </li>

        <li v-if="num_pages !== (page + 1)" class="page-item" style="cursor: pointer">
            <a @click="goToPage(page+2)" class="page-link">{{ page + 2 }}</a>
        </li>

        <li v-if="(page + 3) <= num_pages" class="page-item" style="cursor: pointer">
            <a @click="goToPage(page+3)" class="page-link">{{ page + 3 }}</a>
        </li>
        
        <li class="page-item" v-bind:class="{disabled: (page + 1) === num_pages}" style="cursor: pointer">
          <a v-if="(page + 1) === num_pages" class="page-link"">Следующая</a>
          <a v-else @click="goToPage(page+2)" class="page-link"">Следующая</a>
        </li>

        <li v-if="(page + 3) < num_pages" class="page-item" style="cursor: pointer">
          <span @click="goToPage(num_pages)" class="page-link"> >> {{ num_pages }}</span>
        </li>

        </ul>
    </nav>
    <div class="table-responsive-lg">
        <device-table v-bind:devices="filteredDevices"></device-table>
    </div>

    

</div>`

/* Создание нового экземпляра Vue. */
let app = new Vue({
    el: "#devices",
    template: app_template,
    data: {
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
    }
});