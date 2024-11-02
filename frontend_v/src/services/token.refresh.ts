import axios from "axios";
import store from "@/store";
import router from "@/router.ts";
import {TokenService} from "@/services/token.service";

const refreshTokenURL = "/api/jwt/refresh/"

export async function refreshAccessToken(tokenService: TokenService) {
    const refreshToken = tokenService.getLocalRefreshToken()
    if (!refreshToken) return;
    const rs = await axios.post(
        refreshTokenURL,
        { refresh: refreshToken },
    )
        .then(value => value, reason => reason.response)
        .catch(reason => reason.response);

    if (rs.status !== 200) {
        await store.dispatch("auth/logout")
        await router.push("/auth/login");
        return false
    }

    const { access } = rs.data;

    await store.dispatch('auth/refreshToken', access);
    tokenService.updateLocalAccessToken(access);
    return true
}