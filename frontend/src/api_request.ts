import axios from "axios"

const tokenItem = document.querySelector("input[name=csrfmiddlewaretoken]")

const token = tokenItem?(<HTMLInputElement>tokenItem).value:""

const defaultConfig = {
  headers: {
    // Добавляем токен в заголовок "X-CSRFToken"
    'X-CSRFToken': token
  }
}
export {defaultConfig}

const api_request = axios.create(defaultConfig);

export default api_request
