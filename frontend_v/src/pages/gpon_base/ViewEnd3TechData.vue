<template>
  <Header/>

  <div class="mx-auto py-5 xl:w-2/3">

    <ViewPrintEditButtons
        @print="printData"
        @changeMode="mode => editMode = mode"
        @exit="() => $router.push($route.query.backref||{name: 'gpon-tech-data'})"
        title="Техническая возможность"
        :has-permission-to-edit="hasAnyPermissionToUpdate"
        :is-mobile="isMobile"/>

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <Message v-if="errorStatus" severity="error">
      Ошибка при загрузке данных.
      <br> {{ errorMessage || '' }}
      <br> Статус: {{ errorStatus }}
    </Message>

    <div v-else id="tech-data-block" class="plate px-10 py-5">

      <div class="flex items-center justify-center flex-wrap">

        <div class="flex flex-col">
          <div class="p-2 text-3xl font-bold">{{ detailData.type }}</div>
          <AddressGetCreate v-if="editMode && hasPermissionToUpdateEnd3" :is-mobile="isMobile" :allow-create="true"
                            :data="detailData"/>
          <span v-else class="p-2 text-2xl">{{ end3Address }}</span>

          <InputText v-if="editMode && hasPermissionToUpdateEnd3" v-model.trim="detailData.location" fluid
                     type="text" placeholder="Локация"/>
          <span v-else class="p-2 text-2xl">{{ detailData.location }}</span>

          <!-- Сохранить изменения -->
          <div v-if="editMode && hasPermissionToUpdateEnd3" class="pt-3">
            <Button @click="updateEnd3Info" class="save-button" text severity="success">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                <path
                    d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
              </svg>
              <span v-if="!isMobile">Обновить</span>
            </Button>
          </div>

        </div>
        <div class="m-2">
          <svg v-if="detailData.type === 'rizer'" style="transform: rotate(300grad);" xmlns="http://www.w3.org/2000/svg"
               viewBox="0 0 26 32" width="128" height="128">
            <path fill="#e6e6e6" d="M23 0H3a1 1 0 0 0-1 1v20a1 1 0 0 0 1 1h20a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1z"
                  class="colore6e6e6 svgShape"></path>
            <path fill="#cccccc" d="M25 10H1a1 1 0 1 0 0 2h24a1 1 0 1 0 0-2z" class="colorccc svgShape"></path>
            <path fill="#ffcc66" d="M4 22h2v10H4z" class="colorfc6 svgShape"></path>
            <path fill="gray" d="M8 22h2v10H8z" class="colorgray svgShape"></path>
            <path fill="#88c057" d="M12 22h2v10h-2z" class="color88c057 svgShape"></path>
            <path fill="#48a0dc" d="M16 22h2v10h-2z" class="color48a0dc svgShape"></path>
            <path fill="#9b7cab" d="M20 22h2v10h-2z" class="color9b7cab svgShape"></path>
          </svg>
          <img v-else class="h-[150px] bg-transparent" src="/img/gpon/splitter.svg" alt="splitter">
        </div>

      </div>

      <!-- Абонентская линия -->
      <div class="py-3">

        <div>
          <template v-if="editMode && (hasPermissionToUpdateEnd3 && hasPermissionToUpdateTechCapability)">
            <div class="flex items-center flex-wrap gap-3">
              <div>Изменение ёмкости</div>
              <Select v-model.number="detailData.capacity" @change="changeCapacity" :options="[4, 8, 12, 16, 24]"
                      class="w-fit"/>

              <Message class="my-2" v-if="capacityWarning" :severity="errorSeverity">
                {{ capacityWarning }}
              </Message>

            </div>

            <Message class="my-2" severity="warn">
              Будьте осторожны при выборе новой ёмкости! Данное действие необходимо только после физического
              переключения линии либо в случае ошибки.
            </Message>
          </template>

          <End3PortsViewEdit
              @getInfo="updateEnd3Info"
              :user-permissions="userPermissions"
              :end3-ports-array="detailData.capability"
              :end3-object="detailData"
              :edit-mode="editMode"/>

        </div>

      </div>

    </div>

  </div>

  <Footer/>

</template>

<script>
import AddressGetCreate from "./components/AddressGetCreate.vue";
import End3PortsViewEdit from "./components/End3PortsViewEdit.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue"
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import api from "@/services/api";
import {formatAddress} from "@/formats";
import printElementById from "@/helpers/print";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "ViewEnd3TechData",
  components: {
    Footer,
    Header,
    ViewPrintEditButtons,
    End3PortsViewEdit,
    TechCapabilityBadge,
    AddressGetCreate,
  },
  data() {
    return {
      detailData: {
        "id": 1,
        "address": {
          "region": "Севастополь",
          "settlement": "Севастополь",
          "planStructure": "",
          "street": "улица Колобова",
          "house": "22А",
          "block": null,
          "floor": null,
          "apartment": null
        },
        "capacity": 8,
        "location": "1 подъезд 5 этаж",
        "type": "splitter",
        "capability": [
          {
            "id": 1,
            "status": "empty",
            "number": "1",
            "subscribers": [
              {
                "id": 1,
                "name": "ФИО",
                "transit": 1234567890
              }
            ]
          }
        ]
      },
      errorStatus: null,
      errorMessage: null,
      errorSeverity: null,

      userPermissions: [],
      originalCapacity: null,
      capacityWarning: null,

      windowWidth: window.innerWidth,
      editMode: false,
    }
  },
  mounted() {
    api.get("/api/v1/gpon/permissions").then(resp => {
      this.userPermissions = resp.data
    })

    let url = window.location.href
    api.get("/api/v1/gpon/" + url.match(/tech-data\S+/)[0])
        .then(resp => this.detailData = resp.data)
        .catch(reason => {
          this.errorStatus = reason.response.status
          this.errorMessage = reason.response.data
        })

    this.originalCapacity = this.detailData.capacity
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  },

  computed: {

    hasPermissionToUpdateEnd3() {
      return this.userPermissions.includes("gpon.change_end3")
    },

    hasPermissionToUpdateTechCapability() {
      return this.userPermissions.includes("gpon.change_techcapability")
    },

    hasAnyPermissionToUpdate() {
      return this.hasPermissionToUpdateEnd3 || this.hasPermissionToUpdateTechCapability
    },

    isMobile() {
      return this.windowWidth <= 768
    },

    end3Address() {
      return formatAddress(this.detailData.address)
    },

  },

  methods: {

    changeCapacity() {
      if (this.detailData.capacity < this.originalCapacity) {
        if (this.deletionUsersAffected()) {
          this.errorSeverity = "error"
          this.capacityWarning = "Изменение затронет существующие подключения абонентов. " +
              "Необходимо их перенести на другую линию, а затем изменить ёмкость."
        } else {
          this.errorSeverity = "warn"
          this.capacityWarning = "Внимание, вы указали ёмкость меньше, чем была изначально! Будут удалены последние записи"
        }
      } else if (this.detailData.capacity > this.originalCapacity) {
        this.errorSeverity = "info"
        this.capacityWarning = "Будут добавлены новые"
      } else {
        this.capacityWarning = null
      }
    },

    updateEnd3Info() {
      this.handleRequest(
          api.patch("/api/v1/gpon/tech-data/end3/" + this.detailData.id, this.detailData)
      )
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     */
    handleRequest(request) {
      return request.then(
          () => {
            this.$toast.add({severity: 'success', summary: 'Обновлено', detail: 'Статус был изменён', life: 3000})
          }
      )
          .catch(
              reason => {
                const status = reason.response.status
                this.$toast.add({
                  severity: 'error',
                  summary: `Ошибка ${status}`,
                  detail: reason.response.data,
                  life: 5000
                })
              }
          )
    },

    deletionUsersAffected() {
      const shift = this.originalCapacity - this.detailData.capacity
      for (let i = shift - 1; i < this.detailData.capability.length; i++) {
        if (this.detailData.capability[i].subscribers.length) {
          return true
        }
      }
      return false
    },

    printData() {
      printElementById('tech-data-block')
    },

  }
}
</script>

<style scoped>
.plate {
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}

.save-button {
  border-radius: 12px;
  color: #008b1e;
  border: 1px #008b1e solid;
}

.save-button:hover {
  box-shadow: 0 0 3px #008b1e;
}

@media (max-width: 835px) {
  .container {
    margin-left: 0 !important;
    margin-right: 0 !important;
    max-width: 100% !important;
  }

  .plate {
    border: none;
  }
}

</style>