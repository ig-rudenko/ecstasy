import type { LocationQueryValue, RouteParamValue } from "vue-router";

/** Returns the first scalar value from a Vue Router route parameter or query value. */
export function getSingleRouteValue(
    value: RouteParamValue | RouteParamValue[] | LocationQueryValue | LocationQueryValue[] | undefined
): string {
    if (Array.isArray(value)) {
        return value[0] ?? "";
    }
    return value ?? "";
}

/** Converts a route parameter to a numeric identifier. */
export function getRouteId(value: RouteParamValue | RouteParamValue[] | undefined): number {
    return Number(getSingleRouteValue(value));
}
