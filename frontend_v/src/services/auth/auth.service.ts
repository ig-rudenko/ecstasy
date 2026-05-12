import axios from "axios";

import { LoginUser } from "@/services/user";
import UserService from "@/services/auth/user.service";
import { tokenService } from "@/services/auth/token.service";
import { clearOIDCLogin, isOIDCLogin } from "@/oidc";
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

    async logout() {
        clearOIDCLogin();
        tokenService.removeTokens();
        UserService.removeUser();

        // Очищаем всё хранилище.
        localStorage.clear();

        // Возвращаем в хранилище избранные устройства.
        pinnedDevices.save();
    }
}

export default new AuthService();
