import axios from "axios";

import {LoginUser} from "@/services/user";
import UserService from "@/services/auth/user.service";
import {tokenService} from "@/services/auth/token.service";
import keycloakConnector from "@/keycloak";

class AuthService {
    async login(user: LoginUser) {
        let response = await axios.post("/api/token", {
            username: user.username,
            password: user.password
        });
        tokenService.setTokens(response.data.access, response.data.refresh);
        return response
    }

    async keycloakLogin() {
        const {access, refresh} = keycloakConnector.getTokens()
        if (access && refresh) {
            keycloakConnector.keycloakLoginState.setLogin()  // OIDC используется для входа.
            tokenService.setTokens(access, refresh)
            return Promise.resolve()
        }
        return Promise.reject()
    }

    async logout() {
        keycloakConnector.keycloakLoginState.deleteAutoLogin()
        keycloakConnector.keycloakLoginState.setLogout()  // Выход из OIDC
        tokenService.removeTokens();
        UserService.removeUser();
        localStorage.clear();
    }

}

export default new AuthService();