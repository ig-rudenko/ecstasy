import api from "@/services/api";
import { createNewUser, User } from "@/services/user";

function hasStoredAccessToken(): boolean {
    const data = localStorage.getItem("tokens");
    if (!data) return false;

    try {
        const tokens = JSON.parse(data) as { accessToken?: string };
        return Boolean(tokens.accessToken);
    } catch {
        return false;
    }
}

export async function getMyselfData(): Promise<User> {
    // console.log(tokenService.getUserTokens())
    const resp = await api.get("/api/v1/accounts/myself");
    return createNewUser(resp.data);
}

class UserService {
    private user: User | null = null;

    constructor() {
        if (!hasStoredAccessToken()) return;

        setTimeout(
            () =>
                getMyselfData()
                    .then((user: User) => {
                        this.user = user;
                        this.setUser(user);
                    })
                    .catch(() => this.removeUser()),
            0
        );
    }

    getUser(): User | null {
        if (this.user) return this.user;
        const data = localStorage.getItem("user");
        if (data) this.user = JSON.parse(data);
        return this.user;
    }

    setUser(user: User): void {
        this.user = user;
        localStorage.setItem("user", JSON.stringify(user));
    }

    removeUser(): void {
        this.user = null;
        localStorage.removeItem("user");
    }
}

export default new UserService();
