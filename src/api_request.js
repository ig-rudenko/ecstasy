import axios from "axios"

const tokenItem = document.querySelector("input[name=csrfmiddlewaretoken]")

const token = tokenItem?tokenItem.value:""

const api_request = axios.create({
  headers: {
    // Добавляем токен в заголовок "X-CSRFToken"
    'X-CSRFToken': token
  }
});

export default api_request
