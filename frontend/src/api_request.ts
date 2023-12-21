import axios from "axios"

const tokenItem: HTMLInputElement = document.querySelector("input[name=csrfmiddlewaretoken]")

const token: string = tokenItem?tokenItem.value:""

const api_request = axios.create({

});

export default api_request
