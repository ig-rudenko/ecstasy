<template>
<svg @click="backToAllRings" style="cursor: pointer" xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M1.146 4.854a.5.5 0 0 1 0-.708l4-4a.5.5 0 1 1 .708.708L2.707 4H12.5A2.5 2.5 0 0 1 15 6.5v8a.5.5 0 0 1-1 0v-8A1.5 1.5 0 0 0 12.5 5H2.707l3.147 3.146a.5.5 0 1 1-.708.708l-4-4z"/>
</svg>

<div class="row row-cols-1 row-cols-md-2 mb-3 text-center" style="margin: 20px">

  <div class="col" style="margin-top: 20px">
      <div class="list-group">

<!--          Описание-->
          <div class="rounded-4 list-group-item gap-3 py-3" aria-current="true">
              <p>Разворот кольца {{rings.selectedRing.name}}</p>
              <p>VLAN's для разворота:</p>
              <p>{{rings.selectedRing.vlans.join(",")}}</p>
          </div>

<!--          Кнопка-->
          <div class="gap-3 py-3 rounded-4" aria-current="true">

            <div v-if="!getSolutionsActive" @click="getSolutions" :class="getSolutionsButtonClasses">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-bar-chart-steps" viewBox="0 0 16 16">
                <path d="M.5 0a.5.5 0 0 1 .5.5v15a.5.5 0 0 1-1 0V.5A.5.5 0 0 1 .5 0zM2 1.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-4a.5.5 0 0 1-.5-.5v-1zm2 4a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1-.5-.5v-1zm2 4a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-6a.5.5 0 0 1-.5-.5v-1zm2 4a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1-.5-.5v-1z"></path>
              </svg>

              <span v-if="!solutions.length">
                Проверить статус и сформировать план решений
              </span>
              <span v-else>
                Обновить статус и сформировать новый план решений
              </span>

            </div>

            <div v-else class="py-3">
              <div class="d-flex justify-content-center"><div class="spinner-border" role="status"></div></div>
            </div>

          </div>

<!--          Ошибки-->
          <div class="gap-3 py-3 rounded-4">
            <template v-for="error in reversedErrors" >
              <div class="text-muted" style="text-align: left; font-size: 0.75rem;"> # {{error.time}} </div>
              <div class="alert alert-danger"> {{error.text}} </div>
            </template>
          </div>

<!--          Информация-->
          <div class="gap-3 py-3 rounded-4">
            <template v-for="info in reversedInfos" >
              <div class="text-muted" style="text-align: left; font-size: 0.75rem;"> # {{info.time}} </div>
              <div class="alert alert-primary"> {{info.text}} </div>
            </template>
          </div>

<!--          Перечень решений-->
          <div v-if="solutions.length">
            <div class="text-muted" style="text-align: left; font-size: 0.75rem;">
                # {{getTime()}}
              </div>

            <Solutions
                :solutions="solutions"
                :submit-solutions-active="submitSolutionsActive"
                @submitSolutions="submitSolutions"
            />

          </div>

      </div>
  </div>

  <div class="col">
      <RingView :points="points" />
  </div>

</div>
</template>

<script>
import RingView from "./RingView.vue";
import Solutions from "./Solutions.vue";

export default {
  name: "RingMenu",
  components: {Solutions, RingView},
  props: {
    rings: {
      required: true,
      type: {
        list: Array,
        selectedRing: {name: String, description: String, vlans: Array}
      }
    }
  },
  data() {
    return {
      points: [],
      solutions: [],
      getSolutionsActive: false,
      submitSolutionsActive: false,
      errors: [],
      infos: []
    }
  },
  async mounted() {
    await this.getRing()
  },

  computed: {
    reversedErrors() {
      return this.reverseArray(this.errors)
    },
    reversedInfos() {
      return this.reverseArray(this.infos)
    },

    getSolutionsButtonClasses() {
      if (this.submitSolutionsActive) {
        return ["btn", "btn-success", "disabled"]
      }
      return ["btn", "btn-success"]
    }

  },

  methods: {
    reverseArray(array) {
      let reversed = [];
      for (let i = array.length - 1; i >= 0; i--) {
        reversed.push(array[i]);
      }
      return reversed;
    },

    getTime() {
      let date = new Date()
      let padZero = n => n<10?"0"+n:n
      return padZero(date.getHours()) + ":" + padZero(date.getMinutes()) + ":" + padZero(date.getSeconds())
    },

    async getRing() {
      try {
        let resp = await fetch(
            "/ring-manager/api/transport-ring/" + this.rings.selectedRing.name,
            {method: "get", credentials: "include"}
        )
        this.points = await resp.json()
      } catch (e) {
        console.log(e)
      }
    },

    async getSolutions() {
      if (this.getSolutionsActive) return;
      this.getSolutionsActive = true
      this.solutions = []
      this.errors = []
      this.infos = []

      try {
        const resp = await fetch(
            "/ring-manager/api/transport-ring/" + this.rings.selectedRing.name + "/solutions",
            {
              method: "get",
              credentials: "include",
              headers: {"X-CSRFToken": document.CSRF_TOKEN}
            }
        )
        const data = await resp.json()

        // Этот блок кода обрабатывает ответ от метода getSolutions(). Если статус ответа равен 200 (ОК), он устанавливает
        // свойства данных «точки» и «решения» в соответствующие значения из данных ответа и очищает массив «ошибки». В
        // противном случае он добавляет объект ошибки в массив `errors` с сообщением об ошибке из данных ответа и текущим
        // временем.
        if (resp.status === 200) {
          this.points = data.points
          this.solutions = data.solutions
        } else {
          this.errors.push(
              {
                text: data.error,
                time: this.getTime()
              }
          )
        }

      } catch (e) {
        console.log(e)
      }
      this.getSolutionsActive = false
    },

    async submitSolutions() {
      if (this.submitSolutionsActive) return;
      this.submitSolutionsActive = true
      this.errors = []
      this.infos = []

      try {
        const resp = await fetch(
            "/ring-manager/api/transport-ring/" + this.rings.selectedRing.name + "/solutions",
            {
              method: "post",
              credentials: "include",
              headers: {
                "X-CSRFToken": document.CSRF_TOKEN
              }
            }
        )
        const data = await resp.json()

        if (resp.status === 200) {
            this.infos.push(
                {
                  text: data.status,
                  time: this.getTime()
                }
            )

        } else {
            this.errors.push(
                {
                  text: data.error,
                  time: this.getTime()
                }
            )
        }

        this.solutions = []

      } catch (e) {
        console.log(e)
      }
      this.submitSolutionsActive = false
    },

    backToAllRings() {
      this.rings.selectedRing = null;
    },
  },
}
</script>

<style scoped>

</style>