import Keycloak from "keycloak-js";
import axios from "axios";


class KeycloakLoginState {
    setAutoLogin() {
        localStorage.setItem("keycloak-auto-login", "true")
    }

    deleteAutoLogin() {
        localStorage.removeItem("keycloak-auto-login")
    }

    get autoLogin(): boolean {
        return localStorage.getItem("keycloak-auto-login") === "true"
    }

    setLogin() {
        localStorage.setItem("keycloak-login", "true")
    }

    setLogout() {
        localStorage.removeItem("keycloak-login")
    }

    get isLogin(): boolean {
        return localStorage.getItem("keycloak-login") === "true"
    }
}

class KeycloakConfigState {
    setConfig(config: OIDCConfig) {
        localStorage.setItem("keycloak-config-state", JSON.stringify(config))
    }

    getConfig(): OIDCConfig | null {
        return JSON.parse(localStorage.getItem("keycloak-config-state") || "null") as OIDCConfig | null
    }
}


export interface OIDCConfig {
    enabled: boolean;
    url: string;
    clientId: string;
    realm: string;
}


class KeycloakConnector {
    public _keycloak: Keycloak | null = null
    public keycloakLoginState: KeycloakLoginState = new KeycloakLoginState()
    private configState: KeycloakConfigState = new KeycloakConfigState()
    public isKeycloakInitialized: boolean = false;  // Флаг для отслеживания инициализации
    public refreshTokenTimeout: number = 30000;  // Таймаут для обновления токена в мс.
    public enabled: boolean = false;

    get keycloak(): Keycloak {
        if (this._keycloak) return this._keycloak;
        throw new Error("Keycloak not initialized")
    }

    private async getOIDConfig(): Promise<OIDCConfig> {
        const config = this.configState.getConfig()
        if (config) return config;
        const resp = await axios.get<OIDCConfig>('/api/v1/accounts/oidc/config')
        this.configState.setConfig(resp.data);
        return resp.data;
    }

    async initKeycloak() {
        // Если уже инициализирован, не делаем повторную инициализацию
        if (this.isKeycloakInitialized) {
            return
        }
        try {
            const config = await this.getOIDConfig()
            this.enabled = config.enabled
            if (!this.enabled) return;

            this._keycloak = new Keycloak({
                url: config.url,
                realm: config.realm,
                clientId: config.clientId,
            })
            await this.keycloak.init({
                onLoad: "check-sso",
                pkceMethod: "S256",
                checkLoginIframe: false,
            });
            this.isKeycloakInitialized = true;

        } catch (e) {
            console.error("Keycloak init error:", e);
        }
    }

    autoRefreshToken() {
        const update = async () => {
            await this.keycloak.updateToken(this.refreshTokenTimeout + 10)
            setTimeout(update, this.refreshTokenTimeout)
        }
        setTimeout(update, this.refreshTokenTimeout)
    }

    getTokens(): { access: string, refresh: string } {
        if (this.keycloak.token && this.keycloak.refreshToken) {
            return {access: this.keycloak.token, refresh: this.keycloak.refreshToken}
        }
        return {access: "", refresh: ""}
    }

}


const keycloakConnector = new KeycloakConnector()
export default keycloakConnector