import axiosInstance from "./index";
import {refreshAccessToken, tokenService} from "../auth/token.service";

const ignoreURLs = ["/api/v1/auth/token", "/api/v1/auth/users"];

const setup = () => {
    axiosInstance.interceptors.request.use(
        config => {
            const token = tokenService.getLocalAccessToken();
            if (token) config.headers["Authorization"] = 'Bearer ' + token;
            return config;
        },
        error => Promise.reject(error)
    );

    axiosInstance.interceptors.response.use(
        response => response,
        async (err) => {
            const originalConfig = err.config;
            if (ignoreURLs.includes(originalConfig.url) || !err.response) return Promise.reject(err);

            // Access Token was expired
            if (err.response.status === 401 && !originalConfig._retry) {
                originalConfig._retry = true;
                originalConfig.headers["Content-Type"] = "application/json";
                try {
                    const status = await refreshAccessToken()
                    if (status) return axiosInstance(originalConfig);
                } catch (_error) {
                    return Promise.reject(_error);
                }
            }
            return Promise.reject(err);
        }
    );
};

export default setup;