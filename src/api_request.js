import axios from "axios"

const token = document.querySelector("input[name=csrfmiddlewaretoken]").value

const api_request = axios.create({
  headers: {
    // Добавляем токен в заголовок "X-CSRFToken"
    'X-CSRFToken': token
  }
});

export default api_request
