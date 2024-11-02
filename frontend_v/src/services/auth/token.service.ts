import {UserTokens} from "@/services/user.ts";
import axios from "axios";
import store from "@/store";
import router from "@/router.ts";

export async function refreshAccessToken() {
    const refreshToken = tokenService.getLocalRefreshToken()
    if (!refreshToken) return;

    const rs = await axios.post(
        "/api/token/refresh",
        {refresh: refreshToken},
    )

    if (rs.status !== 200) {
        await store.dispatch("auth/logout")
        await router.push("/login");
        return false
    }

    const {access, refresh} = rs.data;
    // Обновляем access и refresh токены.
    await store.dispatch('auth/refreshTokens', rs.data);
    tokenService.updateLocalTokens(access, refresh);
    return true
}

export class TokenService {
    getLocalRefreshToken() {
        const user = this.getUserTokens();
        return user.refreshToken;
    }

    getLocalAccessToken() {
        const user = this.getUserTokens();
        return user.accessToken;
    }

    updateLocalTokens(access: string, refresh: string) {
        let user = this.getUserTokens();
        user.accessToken = access;
        user.refreshToken = refresh;
        localStorage.setItem("tokens", JSON.stringify(user));
    }

    setUser(tokens: UserTokens) {
        localStorage.setItem("tokens", JSON.stringify(tokens));
    }

    removeUser() {
        localStorage.removeItem("tokens");
    }

    getUserTokens(): UserTokens {
        const data = localStorage.getItem("tokens")
        if (data) {
            const jsonData = JSON.parse(data)
            return new UserTokens(jsonData.accessToken, jsonData.refreshToken)
        }
        return new UserTokens()
    }
}
const tokenService = new TokenService();

export {tokenService}
