const LOGIN_PATH = "/account/login";
const OIDC_CALLBACK_PATH = "/oidc/callback";

export function normalizeAuthRedirectPath(value: unknown): string {
    const path = Array.isArray(value) ? value[0] : value;

    if (typeof path !== "string" || !path.startsWith("/") || path.startsWith("//")) {
        return "/";
    }

    if (path.startsWith(LOGIN_PATH) || path.startsWith(OIDC_CALLBACK_PATH)) {
        return "/";
    }

    return path;
}
