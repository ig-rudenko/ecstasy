import axios from "axios";

import api from "@/services/api";
import { LoginUser } from "@/services/user";
import UserService from "@/services/auth/user.service";
import { tokenService } from "@/services/auth/token.service";
import { clearOIDCLogin, getOIDCLogoutUrl, isOIDCLogin } from "@/oidc";
import pinnedDevices from "@/services/pinnedDevices.ts";

class AuthService {
    async login(user: LoginUser) {
        let response = await axios.post("/api/token", {
            username: user.username,
            password: user.password,
        });
        tokenService.setTokens(response.data.access, response.data.refresh);
        return response;
    }

    async oidcLogin() {
        const { accessToken, refreshToken } = tokenService.getUserTokens();
        if (isOIDCLogin() && accessToken && refreshToken) {
            return Promise.resolve();
        }
        return Promise.reject();
    }

    async logout(endKeycloakSession = false): Promise<string> {
        const oidcLogin = isOIDCLogin();
        let redirectUrl = "/account/login";

        if (oidcLogin) {
            if (endKeycloakSession) {
                redirectUrl = (await getOIDCLogoutUrl()) ?? redirectUrl;
            }
            await api.delete("/api/v1/accounts/oidc/session");
        }

        clearOIDCLogin();
        tokenService.removeTokens();
        UserService.removeUser();

        // Очищаем всё хранилище.
        localStorage.clear();

        // Возвращаем в хранилище избранные устройства.
        pinnedDevices.save();

        return redirectUrl;
    }
}

export default new AuthService();
