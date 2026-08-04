import { CRS, tileLayer, type Layer, type Map as LMap, type TileLayer } from "leaflet";

import api from "@/services/api";

export type TileLayerCrs = "EPSG:3857" | "EPSG:3395" | "EPSG:4326";

export interface MapTileLayer {
    name: string;
    url: string;
    crs: TileLayerCrs;
}

export type TileLayersObject = Record<string, Layer>;

export const defaultTileLayerName = "Open Street Map";
export const defaultTileLayerCrs: TileLayerCrs = "EPSG:3857";

/**
 * Загружает список подложек географических карт.
 *
 * @returns Список подложек.
 */
export async function getMapTileLayers(): Promise<MapTileLayer[]> {
    const resp = await api.get<MapTileLayer[]>("/api/v1/maps/tile-layers/");
    return resp.data;
}

/**
 * Создает OSM-подложку по умолчанию.
 *
 * @returns Leaflet tile layer.
 */
export function createDefaultTileLayer(): TileLayer {
    return tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");
}

/**
 * Возвращает поддерживаемую клиентом CRS подложки.
 *
 * @param crs - CRS из API.
 * @returns Поддерживаемая CRS.
 */
export function normalizeTileLayerCrs(crs: string): TileLayerCrs {
    if (crs === "EPSG:3395") {
        return "EPSG:3395";
    }
    if (crs === "EPSG:4326") {
        return "EPSG:4326";
    }

    return "EPSG:3857";
}

/**
 * Преобразует имя CRS в объект Leaflet.
 *
 * @param crs - CRS подложки.
 * @returns CRS Leaflet.
 */
export function getLeafletTileLayerCrs(crs: TileLayerCrs) {
    if (crs === "EPSG:3395") {
        return CRS.EPSG3395;
    }
    if (crs === "EPSG:4326") {
        return CRS.EPSG4326;
    }

    return CRS.EPSG3857;
}

export class LeafletTileLayerManager {
    private readonly layerCrs = new Map<Layer, TileLayerCrs>();
    private activeName = defaultTileLayerName;

    constructor(
        private readonly map: LMap,
        private readonly defaultLayer: TileLayer,
        private readonly storageKey?: string,
        private readonly onCrsChange?: () => void
    ) {
        this.layerCrs.set(defaultLayer, defaultTileLayerCrs);
    }

    get activeLayerName(): string {
        return this.activeName;
    }

    /**
     * Создает список подложек карты из OSM и API.
     *
     * @returns Подложки для Leaflet control.
     */
    async getTileLayers(): Promise<TileLayersObject> {
        const baseLayers: TileLayersObject = { [defaultTileLayerName]: this.defaultLayer };
        const tileLayers = await getMapTileLayers();

        for (let i = 0; i < tileLayers.length; i++) {
            const layer = tileLayer(tileLayers[i].url);
            baseLayers[tileLayers[i].name] = layer;
            this.layerCrs.set(layer, normalizeTileLayerCrs(tileLayers[i].crs));
        }

        return baseLayers;
    }

    /**
     * Возвращает только OSM-подложку по умолчанию.
     *
     * @returns Подложка по умолчанию для Leaflet control.
     */
    getDefaultTileLayers(): TileLayersObject {
        return { [defaultTileLayerName]: this.defaultLayer };
    }

    /**
     * Обрабатывает выбор подложки в Leaflet control.
     *
     * @param name - Имя выбранной подложки.
     * @param layer - Выбранная подложка.
     */
    selectTileLayer(name: string, layer: Layer): void {
        this.activeName = name;
        this.applyTileLayerCrs(layer);
        this.saveActiveTileLayer();
    }

    /**
     * Восстанавливает выбранную подложку по имени.
     *
     * @param tileLayers - Доступные подложки.
     * @param name - Имя подложки.
     * @returns Была ли восстановлена подложка.
     */
    restoreTileLayer(tileLayers: TileLayersObject, name: string | undefined): boolean {
        if (!name || !tileLayers[name]) {
            return false;
        }

        for (const tileLayerName in tileLayers) {
            this.map.removeLayer(tileLayers[tileLayerName]);
        }

        this.map.addLayer(tileLayers[name]);
        this.activeName = name;
        this.applyTileLayerCrs(tileLayers[name]);
        return true;
    }

    /**
     * Восстанавливает выбранную подложку из localStorage.
     *
     * @param tileLayers - Доступные подложки.
     * @returns Была ли восстановлена подложка.
     */
    restoreStoredTileLayer(tileLayers: TileLayersObject): boolean {
        if (!this.storageKey) {
            return false;
        }

        return this.restoreTileLayer(tileLayers, localStorage.getItem(this.storageKey) || undefined);
    }

    /**
     * Применяет CRS выбранной подложки к карте.
     *
     * @param layer - Выбранная подложка.
     */
    applyTileLayerCrs(layer: Layer): void {
        const crs = this.layerCrs.get(layer) || defaultTileLayerCrs;
        const leafletCrs = getLeafletTileLayerCrs(crs);

        if (this.map.options.crs === leafletCrs) {
            return;
        }

        this.map.options.crs = leafletCrs;

        if (!(this.map as LMap & { _loaded?: boolean })._loaded) {
            (layer as { redraw?: () => void }).redraw?.();
            return;
        }

        const center = this.map.getCenter();
        const zoom = this.map.getZoom();
        this.map.setView(center, zoom, { animate: false });
        (layer as { redraw?: () => void }).redraw?.();
        this.onCrsChange?.();
    }

    /**
     * Сохраняет выбранную подложку в localStorage.
     */
    saveActiveTileLayer(): void {
        if (this.storageKey) {
            localStorage.setItem(this.storageKey, this.activeName);
        }
    }
}
