import axios from "axios";

import store from "@/store";
import router from "@/router";
import {UserTokens} from "@/services/user";

export async function refreshAccessToken() {
    if (tokenService.isRefreshing) {
        // Если токен обновляется, то ожидаем его обновления и успешно выходим
        await tokenService.waitRefreshingIsFinished();
        return true;
    }

    const refreshToken = tokenService.getLocalRefreshToken()
    if (!refreshToken) return;

    tokenService.isRefreshing = true;

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
        tokenService.isRefreshing = false;
        return logout();
    }

}

export class TokenService {
    private _tokens: UserTokens | null = null;
    public isRefreshing = false;

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

    async getLocalAccessToken() {
        await this.waitRefreshingIsFinished();
        const user = this.getUserTokens();
        return user.accessToken;
    }

    getUserTokens(): UserTokens {
        this.load();
        return this._tokens || {accessToken: "", refreshToken: ""}
    }

    setTokens(access: string, refresh: string) {
        this._tokens = {accessToken: access, refreshToken: refresh};
        tokenService.isRefreshing = false;
        this.save();
    }

    removeTokens() {
        localStorage.removeItem("tokens");
        this._tokens = null;
    }

    async waitRefreshingIsFinished() {
        while (this.isRefreshing) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
}

const tokenService = new TokenService();

export {tokenService}
