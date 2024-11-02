import axios from "axios";

const instance = axios.create({
    baseURL: "/api/",
    headers: {
        "Content-Type": "application/json",
    },
    withCredentials: false // do not send cookies
});

export default instance;