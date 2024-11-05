import {app} from '@/appInstance';

const basicLifeTime = 3000;

export function newToast(
    title: string, body: string,
    severity: 'success' | 'info' | 'warn' | 'error' | 'secondary' | 'contrast' | undefined,
    lifeTime: number = basicLifeTime,
    group: string = 'toast',
): void {
    app.config.globalProperties.$toast.add({
        severity: severity,
        summary: title,
        detail: body,
        life: lifeTime,
        group: group
    });
}

export function infoToast(title: string, body: string, lifeTime: number = basicLifeTime): void {
    app.config.globalProperties.$toast.add({
        severity: "info",
        summary: title,
        detail: body,
        life: lifeTime
    });
}

export function successToast(title: string, body: string, lifeTime: number = basicLifeTime): void {
    app.config.globalProperties.$toast.add({
        severity: "success",
        summary: title,
        detail: body,
        life: lifeTime
    });
}

export function errorToast(title: string, body: string, lifeTime: number = basicLifeTime): void {
    app.config.globalProperties.$toast.add({
        severity: "error",
        summary: title,
        detail: body,
        life: lifeTime
    });
}