import { reactive } from "vue";

import { tokenService } from "@/services/auth/token.service";
import { normalizeAuthRedirectPath } from "@/services/auth/redirect";

const OIDC_PENDING_STORAGE_KEY = "oidc-pending-state";
const OIDC_LOGIN_STORAGE_KEY = "oidc-login";

export interface OIDCConfig {
    enabled: boolean;
    url: string;
    clientId: string;
    realm: string;
    authorizationEndpoint: string;
    tokenEndpoint: string;
    userinfoEndpoint: string;
    logoutEndpoint: string;
}

interface OIDCPendingState {
    verifier: string;
    state: string;
    redirectPath: string;
}

interface OIDCState {
    initialized: boolean;
    loading: boolean;
    enabled: boolean;
    config: OIDCConfig | null;
}

export const oidcState = reactive<OIDCState>({
    initialized: false,
    loading: false,
    enabled: false,
    config: null,
});

let refreshTimerId: ReturnType<typeof setTimeout> | null = null;

function toBase64Url(buffer: ArrayBuffer): string {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)))
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=/g, "");
}

export function generateRandomString(length = 64): string {
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
    const bytes = crypto.getRandomValues(new Uint8Array(length));
    return Array.from(bytes, (byte) => alphabet[byte % alphabet.length]).join("");
}

export async function createCodeChallenge(verifier: string): Promise<string> {
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
    return toBase64Url(digest);
}

function persistOIDCState(value: OIDCPendingState): void {
    sessionStorage.setItem(OIDC_PENDING_STORAGE_KEY, JSON.stringify(value));
}

function readOIDCState(): OIDCPendingState | null {
    const rawValue = sessionStorage.getItem(OIDC_PENDING_STORAGE_KEY);
    if (!rawValue) return null;

    try {
        return JSON.parse(rawValue) as OIDCPendingState;
    } catch {
        sessionStorage.removeItem(OIDC_PENDING_STORAGE_KEY);
        return null;
    }
}

function clearOIDCState(): void {
    sessionStorage.removeItem(OIDC_PENDING_STORAGE_KEY);
}

function setOIDCLogin(value: boolean): void {
    if (value) {
        localStorage.setItem(OIDC_LOGIN_STORAGE_KEY, "true");
        return;
    }

    localStorage.removeItem(OIDC_LOGIN_STORAGE_KEY);
}

function clearRefreshTimer(): void {
    if (refreshTimerId !== null) {
        clearTimeout(refreshTimerId);
        refreshTimerId = null;
    }
}

function scheduleRefresh(expiresIn: number): void {
    clearRefreshTimer();

    const delay = Math.max(expiresIn * 1000 - 45_000, 10_000);
    refreshTimerId = setTimeout(async () => {
        const refreshed = await refreshOIDCTokens(true);
        if (!refreshed) {
            clearOIDCLogin();
        }
    }, delay);
}

export function isOIDCLogin(): boolean {
    return localStorage.getItem(OIDC_LOGIN_STORAGE_KEY) === "true";
}

export function clearOIDCLogin(): void {
    setOIDCLogin(false);
    clearRefreshTimer();
}

export async function fetchOIDCConfig(): Promise<OIDCConfig> {
    const response = await fetch("/api/v1/accounts/oidc/config", {
        headers: {
            Accept: "application/json",
        },
    });

    if (!response.ok) {
        throw new Error("Не удалось загрузить OIDC-конфигурацию.");
    }

    return (await response.json()) as OIDCConfig;
}

export async function initializeOIDC(): Promise<void> {
    if (oidcState.initialized) return;

    oidcState.loading = true;
    try {
        oidcState.config = await fetchOIDCConfig();
        oidcState.enabled = oidcState.config.enabled;
        oidcState.initialized = true;

        if (oidcState.enabled && isOIDCLogin()) {
            await refreshOIDCTokens();
        }
    } catch (error) {
        oidcState.config = null;
        oidcState.enabled = false;
        console.error("OIDC init error:", error);
    } finally {
        oidcState.loading = false;
        oidcState.initialized = true;
    }
}

async function ensureOIDCConfig(): Promise<OIDCConfig | null> {
    if (!oidcState.initialized) {
        await initializeOIDC();
    }

    return oidcState.config;
}

export async function beginOIDCLogin(redirectPath = "/"): Promise<void> {
    const config = await ensureOIDCConfig();
    if (!config?.enabled) {
        throw new Error("OIDC не включен на backend.");
    }

    const verifier = generateRandomString(96);
    const state = generateRandomString(48);
    const challenge = await createCodeChallenge(verifier);
    const redirectUri = `${window.location.origin}/oidc/callback`;

    persistOIDCState({
        verifier,
        state,
        redirectPath,
    });

    const query = new URLSearchParams({
        client_id: config.clientId,
        redirect_uri: redirectUri,
        response_type: "code",
        scope: "openid profile email offline_access",
        code_challenge: challenge,
        code_challenge_method: "S256",
        state,
    });

    window.location.href = `${config.authorizationEndpoint}?${query.toString()}`;
}

export async function completeOIDCLogin(code: string, state: string): Promise<string> {
    const config = await ensureOIDCConfig();
    if (!config?.enabled) {
        throw new Error("OIDC не включен на backend.");
    }

    const pendingState = readOIDCState();
    if (!pendingState || pendingState.state !== state) {
        throw new Error("Некорректное состояние OIDC-авторизации.");
    }

    const response = await fetch(config.tokenEndpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            grant_type: "authorization_code",
            code,
            client_id: config.clientId,
            redirect_uri: `${window.location.origin}/oidc/callback`,
            code_verifier: pendingState.verifier,
        }),
    });

    if (!response.ok) {
        throw new Error("Не удалось обменять OIDC-код на токены.");
    }

    const payload = (await response.json()) as {
        access_token: string;
        refresh_token?: string;
        expires_in: number;
    };

    if (!payload.refresh_token) {
        throw new Error("OIDC-провайдер не вернул refresh_token. Проверьте scope offline_access и настройки клиента.");
    }

    tokenService.setTokens(payload.access_token, payload.refresh_token);
    setOIDCLogin(true);
    scheduleRefresh(payload.expires_in);
    clearOIDCState();

    return normalizeAuthRedirectPath(pendingState.redirectPath);
}

export async function refreshOIDCTokens(force = false): Promise<boolean> {
    if (!isOIDCLogin()) return false;

    const refreshToken = tokenService.getLocalRefreshToken();
    if (!refreshToken) return false;

    const config = await ensureOIDCConfig();
    if (!config?.enabled) {
        clearOIDCLogin();
        return false;
    }

    if (!force && tokenService.isRefreshing) {
        await tokenService.waitRefreshingIsFinished();
        return true;
    }

    tokenService.isRefreshing = true;

    try {
        const response = await fetch(config.tokenEndpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
                grant_type: "refresh_token",
                refresh_token: refreshToken,
                client_id: config.clientId,
            }),
        });

        if (!response.ok) {
            clearOIDCLogin();
            tokenService.removeTokens();
            return false;
        }

        const payload = (await response.json()) as {
            access_token: string;
            refresh_token?: string;
            expires_in: number;
        };

        tokenService.setTokens(payload.access_token, payload.refresh_token ?? refreshToken);
        scheduleRefresh(payload.expires_in);
        return true;
    } finally {
        tokenService.isRefreshing = false;
    }
}
