import axios from "axios";

import {tokenService} from "@/services/token.service";
import {LoginUser, UserTokens} from "@/services/user";
import UserService from "@/services/auth/user.service";

class AuthService {
    async login(user: LoginUser) {
        let response = await axios.post("/api/token", {
            username: user.username,
            password: user.password
        });
        tokenService.setUser(
            new UserTokens(
                response.data.access,
                response.data.refresh
            )
        );
        return response
    }

    logout() {
        tokenService.removeUser();
        UserService.removeUser();
    }

}

export default new AuthService();