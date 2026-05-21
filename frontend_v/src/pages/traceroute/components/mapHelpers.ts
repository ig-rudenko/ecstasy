import type { EdgeTitlePayload, TracerouteMapEdge, TracerouteMapNode, VlanMatchInfo } from "./types";

export interface EdgeEndpoint {
    device?: string;
    port?: string;
}

export interface LoadedInterfaceInfo {
    device: string;
    port: string;
    status: string;
    vlans: number[];
    collected: string;
}

/**
 * Escapes text used in Leaflet popup HTML.
 */
export function escapeHtml(value: string): string {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Creates equipment information popup HTML for a map node.
 */
export function createNodePopup(node: TracerouteMapNode): string {
    const device = node.device;
    if (!device) {
        return `
            <div class="traceroute-map-popup">
                <div class="traceroute-map-popup__title">${escapeHtml(node.label)}</div>
                <div class="traceroute-map-popup__muted">${escapeHtml(node.id)}</div>
                ${
                    node.inherited_from
                        ? `<div class="traceroute-map-popup__hint">Координаты унаследованы от ${escapeHtml(node.inherited_from)}</div>`
                        : ""
                }
            </div>
        `;
    }

    const rows = [
        ["Name", device.name],
        ["IP", device.ip],
        ["Vendor", device.vendor],
        ["Model", device.model],
        ["Group", device.group],
        ["Serial", device.serial_number],
        ["OS", device.os_version],
    ].filter(([, value]) => String(value || "").trim());

    return `
        <div class="traceroute-map-popup">
            <div class="traceroute-map-popup__title">${escapeHtml(device.name)}</div>
            <div class="traceroute-map-popup__grid">
                ${rows
                    .map(
                        ([label, value]) => `
                            <span class="traceroute-map-popup__label">${escapeHtml(label)}</span>
                            <span class="traceroute-map-popup__value">${escapeHtml(String(value))}</span>
                        `
                    )
                    .join("")}
            </div>
            <a class="traceroute-map-popup__link" href="${escapeHtml(device.url)}" target="_blank" rel="noopener noreferrer">
                Открыть оборудование
            </a>
        </div>
    `;
}

/**
 * Creates edge tooltip with device and port details.
 */
export function createEdgeTooltip(
    edge: TracerouteMapEdge,
    source: TracerouteMapNode,
    target: TracerouteMapNode
): string {
    const title = getEdgeTitle(edge);
    const src = title.src;
    const dst = title.dst;
    const srcText = formatEndpoint(src, source.label);
    const dstText = dst ? formatEndpoint(dst, target.label) : escapeHtml(title.destination_description || target.label);
    return `
        <div class="traceroute-map-edge-tooltip">
            <div><b>${srcText}</b></div>
            <div>${dstText}</div>
            ${createVlanMatchSummary(title.vlan_match)}
        </div>
    `;
}

/**
 * Creates edge popup with loaded interface history.
 */
export function createEdgePopup(
    edge: TracerouteMapEdge,
    loaded: LoadedInterfaceInfo[] | null,
    loading: boolean
): string {
    const title = getEdgeTitle(edge);
    const endpoints = getEdgeEndpoints(edge);
    return `
        <div class="traceroute-map-popup">
            <div class="traceroute-map-popup__title">Связь</div>
            <div class="traceroute-map-popup__grid">
                ${endpoints
                    .map(
                        (endpoint, index) => `
                            <span class="traceroute-map-popup__label">${index === 0 ? "Src" : "Dst"}</span>
                            <span class="traceroute-map-popup__value">${formatEndpoint(endpoint, "-")}</span>
                        `
                    )
                    .join("")}
                ${
                    title.destination_description
                        ? `<span class="traceroute-map-popup__label">Desc</span><span class="traceroute-map-popup__value">${escapeHtml(title.destination_description)}</span>`
                        : ""
                }
                ${createVlanMatchRows(title.vlan_match)}
            </div>
            ${loading ? '<div class="traceroute-map-popup__hint">Загрузка VLAN...</div>' : ""}
            ${
                loaded
                    ? `<div class="traceroute-map-popup__interfaces">
                        ${loaded.map(createInterfaceInfoHtml).join("") || '<div class="traceroute-map-popup__hint">Данные по портам не найдены</div>'}
                    </div>`
                    : ""
            }
        </div>
    `;
}

/**
 * Returns ports mentioned in an edge payload.
 */
export function getEdgeEndpoints(edge: TracerouteMapEdge): EdgeEndpoint[] {
    const title = getEdgeTitle(edge);
    return [title.src, title.dst].filter(Boolean) as EdgeEndpoint[];
}

/**
 * Returns edge title payload.
 */
function getEdgeTitle(edge: TracerouteMapEdge): EdgeTitlePayload {
    return (edge.title || {}) as EdgeTitlePayload;
}

/**
 * Creates compact VLAN match summary for edge tooltip.
 */
function createVlanMatchSummary(match: VlanMatchInfo | undefined): string {
    if (!match || !match.confidence || match.confidence === "normal" || match.confidence === "high") {
        return "";
    }
    return `<div class="traceroute-map-popup__muted">${escapeHtml(getVlanMatchLabel(match.confidence))}</div>`;
}

/**
 * Creates VLAN match diagnostic rows for edge popup.
 */
function createVlanMatchRows(match: VlanMatchInfo | undefined): string {
    if (!match || !match.confidence || match.confidence === "normal" || match.confidence === "high") {
        return "";
    }
    const source = match.src;
    const range = source?.matched_range ? `${source.matched_range.from}-${source.matched_range.to}` : "-";
    return `
        <span class="traceroute-map-popup__label">VLAN match</span>
        <span class="traceroute-map-popup__value">
            <span class="traceroute-map-popup__confidence traceroute-map-popup__confidence--${escapeHtml(match.confidence)}">
                ${escapeHtml(getVlanMatchLabel(match.confidence))}
            </span>
        </span>
        <span class="traceroute-map-popup__label">Src VLAN</span>
        <span class="traceroute-map-popup__value">
            ${escapeHtml(String(source?.vlan_count ?? "-"))} VLAN, диапазон ${escapeHtml(range)}
        </span>
    `;
}

/**
 * Returns readable VLAN match label.
 */
function getVlanMatchLabel(confidence: string): string {
    if (confidence === "exact") {
        return "точное совпадение VLAN";
    }
    if (confidence === "low") {
        return "низкая уверенность: широкий trunk";
    }
    if (confidence === "medium") {
        return "средняя уверенность: broad trunk подтвержден соседним портом";
    }
    return "обычное совпадение VLAN";
}

/**
 * Creates HTML for loaded interface data.
 */
function createInterfaceInfoHtml(info: LoadedInterfaceInfo): string {
    return `
        <div class="traceroute-map-popup__interface">
            <div class="traceroute-map-popup__interface-head">
                <div class="traceroute-map-popup__value"><b>${escapeHtml(info.device)} ${escapeHtml(info.port)}</b></div>
                <span class="traceroute-map-popup__status traceroute-map-popup__status--${getStatusClass(info.status)}">
                    ${escapeHtml(info.status || "-")}
                </span>
            </div>
            <div class="traceroute-map-popup__muted">Опрос: ${escapeHtml(formatCollectedTime(info.collected))}</div>
            <div class="traceroute-map-popup__vlan-block">
                <span class="traceroute-map-popup__label">VLAN</span>
                <span class="traceroute-map-popup__vlan-list">${escapeHtml(formatVlansAsRanges(info.vlans))}</span>
            </div>
        </div>
    `;
}

/**
 * Returns CSS modifier for interface status badge.
 */
function getStatusClass(status: string): string {
    const normalized = status.trim().toLowerCase();
    if (normalized === "up") {
        return "up";
    }
    if (normalized === "down") {
        return "down";
    }
    if (normalized.includes("ошибка")) {
        return "error";
    }
    return "unknown";
}

/**
 * Formats VLAN list as compact ranges, for example: 1-172,200,233-239.
 */
function formatVlansAsRanges(vlans: number[]): string {
    const uniqueVlans = [...new Set(vlans.map(Number).filter((vlan) => Number.isInteger(vlan)))].sort(
        (left, right) => left - right
    );
    if (!uniqueVlans.length) {
        return "-";
    }

    const ranges: string[] = [];
    let rangeStart = uniqueVlans[0];
    let previous = uniqueVlans[0];

    for (const vlan of uniqueVlans.slice(1)) {
        if (vlan === previous + 1) {
            previous = vlan;
            continue;
        }
        ranges.push(formatVlanRange(rangeStart, previous));
        rangeStart = vlan;
        previous = vlan;
    }
    ranges.push(formatVlanRange(rangeStart, previous));
    return ranges.join(", ");
}

/**
 * Formats a single VLAN range.
 */
function formatVlanRange(start: number, end: number): string {
    return start === end ? String(start) : `${start}-${end}`;
}

/**
 * Formats a device/port endpoint for UI.
 */
function formatEndpoint(endpoint: EdgeEndpoint | undefined, fallback: string): string {
    if (!endpoint) {
        return escapeHtml(fallback);
    }
    const device = endpoint.device || fallback;
    const port = endpoint.port ? `:${endpoint.port}` : "";
    return `${escapeHtml(device)}${escapeHtml(port)}`;
}

/**
 * Formats collected timestamp from interface API.
 */
function formatCollectedTime(value: string): string {
    if (!value) {
        return "-";
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
