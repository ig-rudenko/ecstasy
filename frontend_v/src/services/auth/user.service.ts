import {createNewUser, User} from "@/services/user";
import api from "@/services/api";

export async function getMyselfData(): Promise<User> {
    const resp = await api.get("/auth/myself")
    return createNewUser(resp.data)
}

class UserService {
    getUser(): User | null {
        const data = localStorage.getItem("user")
        if (data) {
            return JSON.parse(data)
        }
        return null
    }

    setUser(user: User): void {
        localStorage.setItem("user", JSON.stringify(user));
    }

    removeUser(): void {
        localStorage.removeItem("user");
    }

}

export default new UserService();