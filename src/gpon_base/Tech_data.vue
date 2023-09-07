<template>
  <div id="app">

    <div class="header">
      <h2>Технические данные</h2>

      <button class="add-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#6D5BD0" class="me-2" viewBox="0 0 16 16">
          <path fill-rule="evenodd"
                d="M8 5.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V10a.5.5 0 0 1-1 0V8.5H6a.5.5 0 0 1 0-1h1.5V6a.5.5 0 0 1 .5-.5z"/>
          <path
              d="m10.273 2.513-.921-.944.715-.698.622.637.89-.011a2.89 2.89 0 0 1 2.924 2.924l-.01.89.636.622a2.89 2.89 0 0 1 0 4.134l-.637.622.011.89a2.89 2.89 0 0 1-2.924 2.924l-.89-.01-.622.636a2.89 2.89 0 0 1-4.134 0l-.622-.637-.89.011a2.89 2.89 0 0 1-2.924-2.924l.01-.89-.636-.622a2.89 2.89 0 0 1 0-4.134l.637-.622-.011-.89a2.89 2.89 0 0 1 2.924-2.924l.89.01.622-.636a2.89 2.89 0 0 1 4.134 0l-.715.698a1.89 1.89 0 0 0-2.704 0l-.92.944-1.32-.016a1.89 1.89 0 0 0-1.911 1.912l.016 1.318-.944.921a1.89 1.89 0 0 0 0 2.704l.944.92-.016 1.32a1.89 1.89 0 0 0 1.912 1.911l1.318-.016.921.944a1.89 1.89 0 0 0 2.704 0l.92-.944 1.32.016a1.89 1.89 0 0 0 1.911-1.912l-.016-1.318.944-.921a1.89 1.89 0 0 0 0-2.704l-.944-.92.016-1.32a1.89 1.89 0 0 0-1.912-1.911l-1.318.016z"/>
        </svg>
        Добавить
      </button>
    </div>

    <Table :data="testTableData"></Table>

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
      gponTechData: [
        {
          id: 1,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 18, block: 10},
          oltPort: "0/4/9",
          deviceName: "MSAN_Gstal64_down",
          entrances: "1-8",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 2,
          address: {
            region: "Севастополь",
            settlement: "Сахарная головка",
            street: "Трактористов",
            house: 2,
            block: null
          },
          oltPort: "0/4/10",
          deviceName: "MSAN_Gstal64_up",
          entrances: "1-8",
          customerLine: {
            type: "rizer",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 19, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 20, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 21, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 22, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 23, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 24, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 25, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 26, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 27, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 28, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 29, block: 10},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 30, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 31, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 32, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 33, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 34, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 35, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 36, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 37, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 38, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        },
        {
          id: 3,
          address: {region: "Севастополь", settlement: "", street: "Колобова", house: 39, block: null},
          oltPort: "0/4/11",
          deviceName: "MSAN_Gstal64_up",
          entrances: "9-12",
          customerLine: {
            type: "splitter",
            count: 3,
            typeCount: 8,
          },
        }
      ]
    }
  },
  computed: {
    testTableData() {
      let testData = Array()
      for (let i = 0; i < 1000; i++) {
        testData.push(...this.gponTechData)
      }
      return testData
    }
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

.add-button {
  margin: 15px;
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.add-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

</style>