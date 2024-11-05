import axios from "axios";

import store from "@/store";
import router from "@/router";
import {UserTokens} from "@/services/user";

export async function refreshAccessToken() {
    const refreshToken = tokenService.getLocalRefreshToken()
    if (!refreshToken) return;

    const logout = async () => {
        await store.dispatch("auth/logout")
        await router.push("/account/login");
        return false;
    }

    try {
        const rs = await axios.post(
            "/api/token/refresh",
            {refresh: refreshToken},
        )
        if (rs.status !== 200) return logout()

        const {access, refresh} = rs.data;
        // Обновляем access и refresh токены.
        await store.dispatch('auth/refreshTokens', rs.data);
        tokenService.setTokens(access, refresh);
        return true

    } catch (error) {
        console.error(error);
        return logout();
    }

}

export class TokenService {
    private _tokens: UserTokens|null = null;

    constructor() {
        this.load();
    }

    private load() {
        const data = localStorage.getItem("tokens")
        if (data) this._tokens = JSON.parse(data)
    }

    private save() {
        localStorage.setItem("tokens", JSON.stringify(this._tokens));
    }

    getLocalRefreshToken() {
        const user = this.getUserTokens();
        return user.refreshToken;
    }

    getLocalAccessToken() {
        const user = this.getUserTokens();
        return user.accessToken;
    }

    getUserTokens(): UserTokens {
        return this._tokens || {accessToken: "", refreshToken:""}
    }

    setTokens(access: string, refresh: string) {
        this._tokens = {accessToken: access, refreshToken: refresh};
        this.save();
    }

    removeTokens() {
        localStorage.removeItem("tokens");
        this._tokens = null;
    }
}
const tokenService = new TokenService();

export {tokenService}
