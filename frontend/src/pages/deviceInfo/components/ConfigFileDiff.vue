<template>

  <div>
    <div class="d-flex flex-wrap align-items-center">
      <Dropdown @change="e => getConfigContent(e.value)" optionLabel="modTime" placeholder="Новая конфигурация" class="w-full md:w-14rem"
                v-model="config1"
                :options="configFiles"/>
      <Dropdown @change="e => getConfigContent(e.value)" optionLabel="modTime" placeholder="Старая конфигурация" class="w-full md:w-14rem"
                v-model="config2"
                :options="configFiles"/>
      <button @click="compareConfigs" class="btn btn-outline-primary">
        <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" class="me-2" viewBox="0 0 16 16">
          <path d="M0 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-2H2a2 2 0 0 1-2-2V2zm5 10v2a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2v5a2 2 0 0 1-2 2H5zm6-8V2a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h2V6a2 2 0 0 1 2-2h5z"/>
        </svg>
        <span>Сравнить</span>
      </button>
    </div>

    <div>
      <div class="form-check form-switch">
        <input class="form-check-input" v-model="showOnlyDiff" type="checkbox" role="switch" id="showOnlyDiff">
        <label class="form-check-label" for="showOnlyDiff">Только различия</label>
      </div>
    </div>

    <div v-if="differences.length > 0">
      <div v-for="(diff, index) in differences" :key="index" class="row hover-line">
        <div class="col-6">
          <template v-if="diff[0]">
            <div v-if="diff[0].removed || diff[0].added" :class="{ removed: diff[0].removed, added: diff[0].added }"
                 v-html="format_to_html(diff[0].value)"></div>
            <div v-else-if="!showOnlyDiff" v-html="format_to_html(diff[0].value)"></div>
          </template>
        </div>
        <div class="col-6">
          <template v-if="diff[1]">
            <div v-if="diff[1].removed || diff[1].added" :class="{ removed: diff[1].removed, added: diff[1].added }"
                 v-html="format_to_html(diff[1].value)"></div>
            <div v-else-if="!showOnlyDiff" v-html="format_to_html(diff[1].value)"></div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Dropdown from "primevue/dropdown/Dropdown.vue";
import {diffLines} from 'diff';
import api_request from "../../../api_request";

export default {
  name: "ConfigFileDiff",
  components: {
    Dropdown,
  },
  props: {
    configFiles: {required: true, type: Array},
    deviceName: {required: true, type: String},
    formattedConfigFunction: {required: true, type: Function},
  },
  data() {
    return {
      config1: null,
      config2: null,
      differences: [],
      showOnlyDiff: false,
    };
  },
  methods: {
    compareConfigs() {
      const diff = diffLines(this.getConfigContent(this.config2), this.getConfigContent(this.config1));
      this.differences = []
      for (const diffElement of diff) {
        if (diffElement.added) {
          this.differences.push([diffElement, null])
        } else if (diffElement.removed) {
          this.differences.push([null, diffElement])
        } else {
          this.differences.push([diffElement, diffElement])
        }

      }
    },
    getConfigContent(config) {
      if (!config.content) {
        api_request.get("/device/api/" + this.deviceName + "/config/" + config.name).then(
            resp => config.content = this.formattedConfigFunction(resp.data)
        )
      }
      return config.content
    },
    /**
     * Превращаем строку в html, для корректного отображения
     *
     * @param string Строка, для форматирования.
     * Заменяем перенос строки на `<br>` пробелы на `&nbsp;`
     */
    format_to_html: function (string) {

      let space_re = new RegExp(' ', 'g');
      let n_re = new RegExp('\n', 'g');

      string = string.replace(space_re, '&nbsp;').replace(n_re, '<br>')
      return string
    },
  },
};
</script>

<style scoped>
.added {
  background-color: #aaffaa;
}

.removed {
  background-color: #ffaaaa;
}
.hover-line:hover {
  background-color: #eaeaea;
}
</style>
