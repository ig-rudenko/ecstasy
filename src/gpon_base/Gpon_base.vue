<template src="./Gpon_base.html"></template>

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

</style>