import {tokenService} from "./token.service.ts";
import UserService from "@/services/auth/user.service.ts";
import {LoginUser, UserTokens} from "@/services/user.ts";
import axios from "axios";

class AuthService {
    async login(user: LoginUser) {
        let response = await axios.post("/api/v1/auth/token", {
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