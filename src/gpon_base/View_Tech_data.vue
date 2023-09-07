<template>
  <div id="app" class="container w-75">

    <div class="header">
      <h2 class="py-3">Технические данные - просмотр</h2>

      <button @click="printData" class="print-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
             viewBox="0 0 16 16">
          <path
              d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
          <path
              d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
        </svg>
        Печать
      </button>
    </div>


    <div id="tech-data-block" class="plate">

      <div class="py-3">

        <div class="d-flex">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4>Станционные данные</h4>
        </div>

        <div style="margin-left: 40px;">
          <table class="table table-striped" style="width: max-content; margin: 10px 0 0 0">
            <tbody>
            <tr>
              <th scope="row">OLT оборудование</th>
              <td>{{ detailData.oltState.deviceName }}</td>
            </tr>
            <tr>
              <th scope="row">Порт</th>
              <td>
                {{ detailData.oltState.oltPort }}
                <button class="btn btn-outline-primary rounded-5 py-1">
                  status
                </button>
              </td>
            </tr>
            <tr>
              <th scope="row">Волокно</th>
              <td>{{ detailData.oltState.fiber }}</td>
            </tr>
            <tr>
              <th scope="row">Описание сплиттера 1го каскада</th>
            </tr>
            </tbody>
          </table>
          <div style="padding: 10px">{{ detailData.oltState.description }}</div>
        </div>

      </div>

      <div class="py-3">

        <div class="d-flex">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4>
            Адрес: {{ detailData.houseData.address.settlement || "" }}
            {{ detailData.houseData.address.street }}
            д. {{
              detailData.houseData.address.house
            }}{{ detailData.houseData.address.block ? "/" + detailData.houseData.address.block : "" }}</h4>
        </div>

        <div style="margin-left: 40px;">
          <table class="table table-striped" style="width: max-content; margin: 10px 0 0 0">
            <tbody>
            <tr>
              <th scope="row">Задействованные подъезды в доме для данного OLT порта</th>
              <td>{{ detailData.houseData.entrances }}</td>
            </tr>
            <tr>
              <th scope="row">Описание сплиттера 2го каскада</th>
            </tr>
            </tbody>
          </table>
          <div style="padding: 10px">{{ detailData.houseData.description }}</div>
        </div>

      </div>

      <div class="py-3">

        <div class="d-flex">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4>Абонентская линия</h4>
        </div>

        <div style="margin-left: 40px;">
          <table class="table table-striped" style="width: max-content; margin: 10px 0 0 0">
            <tbody>
            <tr v-for="(line, index) in detailData.customerLines">
              <th scope="row">{{ customerLineTypeName(line.type) }} {{ index + 1 }}</th>
              <td>{{ line.location }}</td>
              <td>{{ customerLineNumbers(line) }}</td>
              <td>
                <button class="btn btn-outline-primary rounded-5 py-1">
                  detail
                </button>
              </td>
            </tr>
            </tbody>
          </table>
        </div>

      </div>


    </div>

  </div>
</template>

<script>
import Table from "./components/Table.vue";

export default {
  name: "Gpon_base.vue",
  components: {
    Table
  },
  data() {
    return {
      data: {
        id: 1,
        houseData: {
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 18, block: 10},
          entrances: "1-8",
          description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        },
        oltState: {
          oltPort: "0/4/9",
          deviceName: "MSAN_Gstal64_down",
          fiber: "ВОЛС 1203",
          description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        },
        customerLines: [
          {
            type: "splitter",
            location: "п. 1 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 2 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 3 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 4 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 5 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 6 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 7 этаж 4",
            count: 8,
          },
          {
            type: "splitter",
            location: "п. 8 этаж 4",
            count: 8,
          },
        ],
      }
    }
  },
  computed: {
    detailData() {
      return this.data
    },
  },
  methods: {
    customerLineTypeName(type) {
      if (type === "splitter") {
        return "Сплиттер"
      } else if (type === "rizer") {
        return "Райзер"
      } else {
        return type
      }
    },

    customerLineNumbers(line) {
      if (line.type === "splitter") {
        return `${line.count} портов`
      } else if (line.type === "rizer") {
        return `${line.count} волокон`
      } else {
        return line
      }
    },

    printData() {
      let prtHtml = document.getElementById('tech-data-block').innerHTML
      // remove all buttons
      prtHtml = prtHtml.replace(/<button.*?>.*?<\/button>/g, "")

      // Get all stylesheets HTML
      let stylesHtml = '';
      for (const node of [...document.querySelectorAll('link[rel="stylesheet"], style')]) {
        stylesHtml += node.outerHTML;
      }
      // Open the print window
      const WinPrint = window.open('', '', 'width=1200,height=900,toolbar=0,scrollbars=0,status=0');
      WinPrint.document.write(`<!DOCTYPE html>
      <html lang="ru">
        <head>
          ${stylesHtml}
          <title></title>
        </head>
        <body>
          ${prtHtml}
        </body>
      </html>`);
      WinPrint.document.close();
      WinPrint.focus();
      WinPrint.print();
    },
  }
}
</script>

<style scoped>
.header {
  text-align: right;
  display: flex;
  justify-content: space-between;
  align-items: center;
}


.print-button {
  margin: 15px;
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.print-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

.plate {
  padding: 40px;
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}
</style>