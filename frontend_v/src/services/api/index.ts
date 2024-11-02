import axios from "axios";

const instance = axios.create({
    headers: {
        "Content-Type": "application/json",
    },
    withCredentials: false // do not send cookies
});

export default instance;