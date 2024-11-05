import axios from "axios";

import {LoginUser} from "@/services/user";
import UserService from "@/services/auth/user.service";
import {tokenService} from "@/services/auth/token.service";

class AuthService {
    async login(user: LoginUser) {
        let response = await axios.post("/api/token", {
            username: user.username,
            password: user.password
        });
        tokenService.setTokens(response.data.access, response.data.refresh);
        return response
    }

    logout() {
        tokenService.removeTokens();
        UserService.removeUser();
    }

}

export default new AuthService();