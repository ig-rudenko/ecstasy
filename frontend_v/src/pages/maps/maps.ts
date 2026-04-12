import {
    CircleMarker,
    circleMarker,
    canvas,
    Control,
    divIcon,
    featureGroup,
    GeoJSON,
    LatLng,
    LatLngBounds,
    LatLngExpression,
    Layer,
    Map as LMap,
    marker,
    polygon,
    polyline,
    tileLayer,
} from "leaflet";

import api from "@/services/api";
import errorFmt from "@/errorFmt";
import {Paginator} from "@/types/paginator";
import {errorToast} from "@/services/my.toast";
import {strFormatArgs, textToHtml, wrapLinks} from "@/formats";
import {loadLayers, saveLayers} from "@/pages/maps/layers";
import LayersObject = Control.LayersObject;

enum mapType {
    zabbix = "zabbix",
    file = "file",
    external = "external",
    none = "none",
}

export interface MapBrief {
    id: number;
    name: string;
    description: string;
    interactive: boolean;
    preview_image: string;
    type: mapType;
}

export interface MapDetail extends MapBrief {
    map_url: string;
    from_file: string;
}

export interface Problems {
    id: string;
    acknowledges: string[][];
}

interface OriginPointData {
    fillColor: string | undefined;
    popupContent: string;
    layer: Layer;
}

interface PointData {
    id: string;
    sourceId: string;
    latlng: LatLngExpression;
    layerName: string;
    style: Record<string, unknown>;
    popupContent: string;
    tooltipContent: string;
    searchText: string;
    point?: CircleMarker;
    currentProblemsContent?: string;
    _origin?: OriginPointData;
    hasProblems: boolean;
}

interface StaticElementData {
    id: string;
    layerName: string;
    feature: any;
    geometryType: "Point" | "LineString" | "Polygon";
    bounds: LatLngBounds;
    latlng: LatLngExpression;
    name?: string;
    description?: string;
    searchText: string;
    element?: any;
}

const popupDefaultOptions = {maxWidth: 1200};
const defaultMapCenter: LatLngExpression = [44.6, 33.5];
const defaultMapZoom = 12;
const renderBatchSize = 250;
const viewportPadding = 0.2;
const spatialCellSize = 0.25;

export type MapsPage = Paginator<MapBrief>;

const geoGoogle = tileLayer("https://www.google.com/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}", {attribution: "google"});
const arcgisonline = tileLayer("http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}");
const osm = tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");

/**
 * Загружает подробные данные карты.
 *
 * @param mapID - Идентификатор карты.
 * @returns Подробные данные карты или null.
 */
export async function getMapDetail(mapID: string): Promise<MapDetail | null> {
    try {
        const resp = await api.get<MapDetail>("/api/v1/maps/" + mapID);
        return resp.data;
    } catch (error: any) {
        errorToast("Не удалось загрузить карту", errorFmt(error));
        return null;
    }
}

export class MapService {
    public mapData: MapDetail | null = null;
    public mapGroups: string[] = [];
    public map: LMap;
    public points: Map<string, PointData> = new Map();
    public staticElements: StaticElementData[] = [];
    public overlays: LayersObject = {};

    private updateInFlight = false;
    private canvasRenderer = canvas({padding: 0.5});
    private visibilityRefreshQueued = false;
    private pointSpatialIndex: Map<string, PointData[]> = new Map();
    private staticSpatialIndex: Map<string, StaticElementData[]> = new Map();
    private visiblePointIds: Set<string> = new Set();
    private visibleStaticElementIds: Set<string> = new Set();
    private pointsBySourceId: Map<string, PointData[]> = new Map();

    constructor(public mapID: string, public mapHTMLElementID: string) {
        this.map = new LMap(mapHTMLElementID, {layers: [osm], minZoom: 5, preferCanvas: true});
        this.map.setView(defaultMapCenter, defaultMapZoom);
        this.map.attributionControl.getContainer()?.remove();
        this.map.addControl(new Control.Scale());
        this.map.on("overlayadd overlayremove", () => {
            saveLayers(this.mapID, this.map, this.overlays);
            this.queueVisibilityRefresh();
        });
        this.map.on("moveend zoomend", () => this.queueVisibilityRefresh());
    }

    /**
     * Загружает подробные данные карты.
     *
     * @returns Подробные данные карты или null.
     */
    async getMapData(): Promise<MapDetail | null> {
        this.mapData = await getMapDetail(this.mapID);
        return this.mapData;
    }

    /**
     * Загружает список групп слоев карты.
     *
     * @returns Список групп или undefined при ошибке.
     */
    async getMapGroups() {
        try {
            const response = await api.get<{ groups: string[] }>(`/api/v1/maps/${this.mapID}/layers`);
            this.mapGroups = response.data.groups;
            return response.data.groups;
        } catch (error: any) {
            errorToast("Не удалось получить список групп", errorFmt(error));
        }
    }

    /**
     * Создает группы слоев и панель переключения.
     */
    async renderMapGroups() {
        if (!this.mapGroups.length) {
            await this.getMapGroups();
        }

        for (let i = 0; i < this.mapGroups.length; i++) {
            this.overlays[this.mapGroups[i]] = featureGroup([]);
        }

        this.map.addControl(new Control.Layers(
            {"Спутник старый": geoGoogle, "Спутник новый": arcgisonline, "Схема": osm},
            this.overlays,
            {autoZIndex: true, collapsed: true, position: "topright", sortLayers: true},
        ));

        loadLayers(this.mapID, this.map, this.overlays);
    }

    /**
     * Загружает объекты карты для рендера.
     *
     * @returns Данные слоев.
     */
    async loadMarkers() {
        try {
            const response = await api.get<any[]>(`/api/v1/maps/${this.mapID}/render`);
            return response.data;
        } catch (error: any) {
            errorToast("Не удалось получить данные", errorFmt(error));
            return [];
        }
    }

    /**
     * Подготавливает данные объектов и рендерит только видимую область.
     */
    async renderMarkers() {
        const renderData = await this.loadMarkers();

        for (let i = 0; i < renderData.length; i++) {
            if (renderData[i].type === "zabbix") {
                this.prepareZabbixMarkers(renderData[i]);
            } else if (renderData[i].type === "geojson") {
                this.prepareGeoJSON(renderData[i]);
            }
        }

        await this.refreshVisibleElements();
    }

    /**
     * Подготавливает динамические точки Zabbix без немедленного создания Leaflet-слоев.
     *
     * @param data - Данные слоя.
     */
    private prepareZabbixMarkers(data: any) {
        const features = data.features.features as any[];

        for (let i = 0; i < features.length; i++) {
            const feature = features[i];
            const tooltipContent = feature.properties.name || "";
            const popupContent = feature.properties.description || "";
            const latlng = [...feature.geometry.coordinates].reverse() as [number, number];
            const sourceId = String(feature.id);

            const pointData = {
                id: `${data.name}:${sourceId}`,
                sourceId,
                latlng,
                layerName: data.name,
                style: feature.properties.style || {},
                popupContent,
                tooltipContent,
                searchText: normalizeSearchText([tooltipContent, popupContent]),
                hasProblems: false,
            };

            this.points.set(pointData.id, pointData);
            addPointToSpatialIndex(this.pointSpatialIndex, pointData);
            addPointToSourceIndex(this.pointsBySourceId, pointData);
        }
    }

    /**
     * Подготавливает статические GeoJSON-объекты без немедленного создания Leaflet-слоев.
     *
     * @param data - Данные слоя.
     */
    private prepareGeoJSON(data: any) {
        const defaultSettings = data.properties;
        const features = data.features.features as any[];

        for (let i = 0; i < features.length; i++) {
            const feature = features[i];
            const geometryType = feature.geometry.type as "Point" | "LineString" | "Polygon";
            const latlng = getFeatureAnchor(feature);
            const bounds = getFeatureBounds(feature);

            const staticElement = {
                id: `${data.name}:${feature.id || i}`,
                layerName: data.name,
                feature: {
                    ...feature,
                    __defaults: defaultSettings,
                },
                geometryType,
                bounds,
                latlng,
                name: feature.properties?.name || feature.properties?.iconCaption,
                description: feature.properties?.description,
                searchText: normalizeSearchText([
                    feature.properties?.name,
                    feature.properties?.iconCaption,
                    feature.properties?.description,
                ]),
            };

            this.staticElements.push(staticElement);
            addElementToSpatialIndex(this.staticSpatialIndex, staticElement);
        }
    }

    /**
     * Загружает список проблем на карте.
     *
     * @returns Список проблем.
     */
    async getProblems(): Promise<Problems[]> {
        try {
            const resp = await api.get<{ problems: Problems[] }>(`/api/v1/maps/${this.mapID}/update`);
            return resp.data.problems;
        } catch (error: any) {
            errorToast("Не удалось получить данные", errorFmt(error));
            return [];
        }
    }

    /**
     * Обновляет состояние аварийных узлов без влияния на текущий zoom/center.
     */
    async update() {
        if (this.updateInFlight) {
            return;
        }

        this.updateInFlight = true;

        try {
            const problems = await this.getProblems();
            const problemsPointsBeforeUpdate: Map<string, PointData> = new Map();

            this.points.forEach((value, key) => {
                if (value.hasProblems) {
                    problemsPointsBeforeUpdate.set(key, value);
                }
            });

            for (let i = 0; i < problems.length; i++) {
                const points = this.pointsBySourceId.get(String(problems[i].id));

                if (!points?.length) {
                    continue;
                }

                const problemsText = buildProblemsText(problems[i]);

                for (let pointIndex = 0; pointIndex < points.length; pointIndex++) {
                    const point = points[pointIndex];

                    if (!point._origin) {
                        point._origin = {
                            fillColor: typeof point.style.fillColor === "string" ? point.style.fillColor : undefined,
                            popupContent: point.popupContent,
                            layer: this.overlays[point.layerName] as Layer,
                        };
                    }

                    point.hasProblems = true;
                    point.currentProblemsContent = problemsText;
                    problemsPointsBeforeUpdate.delete(point.id);

                    if (point.point) {
                        point.point.setStyle({fillColor: "red"});
                        ensurePointPopupBound(point);
                        point.point.setPopupContent(point._origin.popupContent + problemsText);
                    }
                }
            }

            problemsPointsBeforeUpdate.forEach((point) => {
                if (!point._origin) {
                    return;
                }

                point.hasProblems = false;
                point.currentProblemsContent = undefined;

                if (point.point) {
                    point.point.setStyle({fillColor: point._origin.fillColor});
                    point.point.setPopupContent(point._origin.popupContent);
                }

                point._origin = undefined;
            });
        } finally {
            this.updateInFlight = false;
        }
    }

    /**
     * Ищет объект на карте и рендерит его при необходимости.
     *
     * @param text - Текст поиска.
     * @returns Первый найденный объект или null.
     */
    searchPoint(text: string) {
        const normalizedText = text.toString().trim().toLowerCase();
        let marker = null;

        if (!normalizedText) {
            return marker;
        }

        for (const point of this.points.values()) {
            if (point.searchText.includes(normalizedText)) {
                if (!marker) {
                    this.focusMap(point.latlng, 17);
                    this.refreshVisibleElementsSync();
                    marker = point;
                }

                if (point.point) {
                    this.highlightMarker(point.point);
                }
            }
        }

        for (let i = 0; i < this.staticElements.length; i++) {
            const element = this.staticElements[i];
            if (element.searchText.includes(normalizedText)) {
                if (!marker) {
                    this.focusMap(element.latlng, 17);
                    this.refreshVisibleElementsSync();
                    marker = element;
                }

                if (element.element) {
                    this.highlightMarker(element.element);
                }
            }
        }

        return marker;
    }

    /**
     * Освежает видимые слои батчами после перемещения карты.
     */
    async refreshVisibleElements() {
        const paddedBounds = this.map.getBounds().pad(viewportPadding);
        const nextVisiblePoints = this.collectVisiblePointIds(paddedBounds);
        const nextVisibleStaticElements = this.collectVisibleStaticElementIds(paddedBounds);

        await this.applyPointVisibilityDiff(nextVisiblePoints);
        await this.applyStaticVisibilityDiff(nextVisibleStaticElements);
    }

    /**
     * Синхронно обновляет видимость сразу после поиска/переключения слоя.
     */
    private refreshVisibleElementsSync() {
        const paddedBounds = this.map.getBounds().pad(viewportPadding);
        const nextVisiblePoints = this.collectVisiblePointIds(paddedBounds);
        const nextVisibleStaticElements = this.collectVisibleStaticElementIds(paddedBounds);

        this.applyPointVisibilityDiffSync(nextVisiblePoints);
        this.applyStaticVisibilityDiffSync(nextVisibleStaticElements);
    }

    /**
     * Ставит обновление видимости в очередь следующего animation frame.
     */
    private queueVisibilityRefresh() {
        if (this.visibilityRefreshQueued) {
            return;
        }

        this.visibilityRefreshQueued = true;
        requestAnimationFrame(async () => {
            this.visibilityRefreshQueued = false;
            await this.refreshVisibleElements();
        });
    }

    /**
     * Проверяет, включен ли слой в панели overlays.
     *
     * @param layerName - Имя слоя.
     * @returns Признак активности слоя.
     */
    private isOverlayVisible(layerName: string) {
        const overlay = this.overlays[layerName];
        return Boolean(overlay && this.map.hasLayer(overlay));
    }

    /**
     * Возвращает идентификаторы точек, попадающих в текущий viewport.
     *
     * @param bounds - Границы viewport.
     * @returns Набор идентификаторов видимых точек.
     */
    private collectVisiblePointIds(bounds: LatLngBounds) {
        const visibleIds = new Set<string>();
        const candidates = collectSpatialCandidates(this.pointSpatialIndex, bounds);

        for (let i = 0; i < candidates.length; i++) {
            const point = candidates[i];
            if (!this.isOverlayVisible(point.layerName)) {
                continue;
            }

            if (bounds.contains(toLatLng(point.latlng))) {
                visibleIds.add(point.id);
            }
        }

        return visibleIds;
    }

    /**
     * Возвращает идентификаторы статических объектов, попадающих в viewport.
     *
     * @param bounds - Границы viewport.
     * @returns Набор идентификаторов видимых объектов.
     */
    private collectVisibleStaticElementIds(bounds: LatLngBounds) {
        const visibleIds = new Set<string>();
        const candidates = collectSpatialCandidates(this.staticSpatialIndex, bounds);

        for (let i = 0; i < candidates.length; i++) {
            const element = candidates[i];
            if (!this.isOverlayVisible(element.layerName)) {
                continue;
            }

            if (bounds.intersects(element.bounds)) {
                visibleIds.add(element.id);
            }
        }

        return visibleIds;
    }

    /**
     * Применяет diff видимости точек батчами.
     *
     * @param nextVisiblePoints - Новый набор видимых точек.
     */
    private async applyPointVisibilityDiff(nextVisiblePoints: Set<string>) {
        const idsToHide = difference(this.visiblePointIds, nextVisiblePoints);
        const idsToShow = difference(nextVisiblePoints, this.visiblePointIds);

        await renderInBatches(idsToHide, renderBatchSize, (pointId) => {
            const point = this.points.get(pointId);
            if (point) {
                this.syncPointVisibility(point, false);
            }
        });

        await renderInBatches(idsToShow, renderBatchSize, (pointId) => {
            const point = this.points.get(pointId);
            if (point) {
                this.syncPointVisibility(point, true);
            }
        });

        this.visiblePointIds = nextVisiblePoints;
    }

    /**
     * Применяет diff видимости статических объектов батчами.
     *
     * @param nextVisibleStaticElements - Новый набор видимых статических объектов.
     */
    private async applyStaticVisibilityDiff(nextVisibleStaticElements: Set<string>) {
        const idsToHide = difference(this.visibleStaticElementIds, nextVisibleStaticElements);
        const idsToShow = difference(nextVisibleStaticElements, this.visibleStaticElementIds);

        await renderInBatches(idsToHide, renderBatchSize, (elementId) => {
            const element = findStaticElementById(this.staticElements, elementId);
            if (element) {
                this.syncStaticElementVisibility(element, false);
            }
        });

        await renderInBatches(idsToShow, renderBatchSize, (elementId) => {
            const element = findStaticElementById(this.staticElements, elementId);
            if (element) {
                this.syncStaticElementVisibility(element, true);
            }
        });

        this.visibleStaticElementIds = nextVisibleStaticElements;
    }

    /**
     * Синхронно применяет diff видимости точек.
     *
     * @param nextVisiblePoints - Новый набор видимых точек.
     */
    private applyPointVisibilityDiffSync(nextVisiblePoints: Set<string>) {
        const idsToHide = difference(this.visiblePointIds, nextVisiblePoints);
        const idsToShow = difference(nextVisiblePoints, this.visiblePointIds);

        for (let i = 0; i < idsToHide.length; i++) {
            const point = this.points.get(idsToHide[i]);
            if (point) {
                this.syncPointVisibility(point, false);
            }
        }

        for (let i = 0; i < idsToShow.length; i++) {
            const point = this.points.get(idsToShow[i]);
            if (point) {
                this.syncPointVisibility(point, true);
            }
        }

        this.visiblePointIds = nextVisiblePoints;
    }

    /**
     * Синхронно применяет diff видимости статических объектов.
     *
     * @param nextVisibleStaticElements - Новый набор видимых статических объектов.
     */
    private applyStaticVisibilityDiffSync(nextVisibleStaticElements: Set<string>) {
        const idsToHide = difference(this.visibleStaticElementIds, nextVisibleStaticElements);
        const idsToShow = difference(nextVisibleStaticElements, this.visibleStaticElementIds);

        for (let i = 0; i < idsToHide.length; i++) {
            const element = findStaticElementById(this.staticElements, idsToHide[i]);
            if (element) {
                this.syncStaticElementVisibility(element, false);
            }
        }

        for (let i = 0; i < idsToShow.length; i++) {
            const element = findStaticElementById(this.staticElements, idsToShow[i]);
            if (element) {
                this.syncStaticElementVisibility(element, true);
            }
        }

        this.visibleStaticElementIds = nextVisibleStaticElements;
    }

    /**
     * Создает или удаляет динамическую точку в зависимости от видимости.
     *
     * @param point - Данные точки.
     * @param isVisible - Должна ли точка быть видимой.
     */
    private syncPointVisibility(point: PointData, isVisible: boolean) {
        const overlay = this.overlays[point.layerName] as any;

        if (isVisible) {
            if (!point.point) {
                const circle = circleMarker(point.latlng, {
                    radius: Number(point.style.radius || 6),
                    ...point.style,
                    renderer: this.canvasRenderer,
                }).addTo(overlay);

                attachLazyInteractions(circle, {
                    tooltipContent: point.tooltipContent,
                    popupContent: point.popupContent,
                });

                if (point.hasProblems) {
                    circle.setStyle({fillColor: "red"});
                    ensurePointPopupBound({...point, point: circle});
                    circle.setPopupContent(point.popupContent + (point.currentProblemsContent || ""));
                }

                point.point = circle;
            } else if (!overlay.hasLayer(point.point)) {
                point.point.addTo(overlay);
            }

            return;
        }

        if (point.point && overlay.hasLayer(point.point)) {
            overlay.removeLayer(point.point);
        }
    }

    /**
     * Создает или удаляет статический объект в зависимости от видимости.
     *
     * @param element - Данные объекта.
     * @param isVisible - Должен ли объект быть видимым.
     */
    private syncStaticElementVisibility(element: StaticElementData, isVisible: boolean) {
        const overlay = this.overlays[element.layerName] as any;

        if (isVisible) {
            if (!element.element) {
                element.element = instantiateStaticElement(element, this.canvasRenderer);
            }

            if (element.element && !overlay.hasLayer(element.element)) {
                element.element.addTo(overlay);
            }

            return;
        }

        if (element.element && overlay.hasLayer(element.element)) {
            overlay.removeLayer(element.element);
        }
    }

    /**
     * Подсвечивает найденный объект.
     *
     * @param marker - Leaflet-объект.
     */
    private highlightMarker(marker: any) {
        if (!marker._path) {
            return;
        }

        if (!marker.options._originFillColor) {
            marker.options._originFillColor = marker.options.fillColor;
        }

        for (let i = 1; i <= 20; i++) {
            setTimeout(() => {
                marker._path.style.fill = i % 2 === 0 ? marker.options._originFillColor : "orange";
            }, 250 * i);
        }

        setTimeout(() => {
            marker._path.style.fill = marker.options._originFillColor;
        }, 5100);
    }

    /**
     * Центрирует карту на объекте.
     *
     * @param latlng - Координаты точки.
     * @param zoom - Целевой zoom.
     */
    private focusMap(latlng: LatLngExpression, zoom: number) {
        if ((this.map as any)._loaded) {
            this.map.flyTo(latlng, zoom);
            return;
        }

        this.map.setView(latlng, zoom);
    }
}

/**
 * Нормализует строку для поиска.
 *
 * @param values - Значения для индексации.
 * @returns Строка поиска.
 */
function normalizeSearchText(values: unknown[]): string {
    return values
        .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
        .join(" ")
        .toLowerCase();
}

/**
 * Формирует HTML проблем узла.
 *
 * @param problem - Описание проблем.
 * @returns HTML строки проблем.
 */
function buildProblemsText(problem: Problems): string {
    let problemsText = "";

    for (let j = 0; j < problem.acknowledges.length; j++) {
        const ackTime = problem.acknowledges[j][1];
        const ackText = problem.acknowledges[j][0];
        const html = textToHtml(ackText, false);
        problemsText += `<div><p><span style="color: #2400ff; font-family: monospace;">${ackTime}</span> -> ${html}</p></div>`;
    }

    return problemsText;
}

/**
 * Создает статический Leaflet-объект по заранее подготовленным данным.
 *
 * @param element - Данные статического объекта.
 * @param renderer - Canvas renderer.
 * @returns Leaflet layer.
 */
function instantiateStaticElement(element: StaticElementData, renderer: any) {
    const defaults = element.feature.__defaults;

    if (element.geometryType === "Point") {
        return createMarker(
            element.feature,
            GeoJSON.coordsToLatLng(element.feature.geometry.coordinates),
            defaults.Marker,
            renderer,
        );
    }

    if (element.geometryType === "LineString") {
        return createPolyline(
            element.feature,
            GeoJSON.coordsToLatLngs(element.feature.geometry.coordinates),
            defaults.Polygon,
            renderer,
        );
    }

    return createPolygon(
        element.feature,
        GeoJSON.coordsToLatLngs(element.feature.geometry.coordinates[0]),
        defaults.Polygon,
        renderer,
    );
}

/**
 * Создает полигон.
 *
 * @param feature - GeoJSON feature.
 * @param latlng - Координаты.
 * @param defaults - Настройки по умолчанию.
 * @param renderer - Canvas renderer.
 * @returns Leaflet polygon.
 */
function createPolygon(feature: any, latlng: LatLngExpression[], defaults: any, renderer?: any) {
    const polygonLayer = polygon(latlng, {
        fillColor: feature.properties.fill || defaults.FillColor,
        color: feature.properties.stroke || defaults.BorderColor,
        weight: Number(feature.properties["stroke-width"]) || 2,
        opacity: feature.properties["stroke-opacity"] || defaults.Opacity,
        fillOpacity: feature.properties["fill-opacity"] || defaults.Opacity,
        renderer,
    });

    const popupText = feature.properties?.description;
    attachLazyInteractions(polygonLayer, {popupContent: popupText ? wrapLinks(textToHtml(popupText)) : ""});
    return polygonLayer;
}

/**
 * Создает полилинию.
 *
 * @param feature - GeoJSON feature.
 * @param latlng - Координаты.
 * @param defaults - Настройки по умолчанию.
 * @param renderer - Canvas renderer.
 * @returns Leaflet polyline.
 */
function createPolyline(feature: any, latlng: LatLngExpression[], defaults: any, renderer?: any) {
    const line = polyline(latlng, {
        color: feature.properties.stroke || defaults.BorderColor,
        weight: feature.properties["stroke-width"] || 2,
        fillOpacity: feature.properties["stroke-opacity"] || defaults.Opacity,
        renderer,
    });

    const popupText = feature.properties?.description;
    attachLazyInteractions(line, {popupContent: popupText ? wrapLinks(textToHtml(popupText)) : ""});
    return line;
}

/**
 * Создает точечный объект.
 *
 * @param feature - GeoJSON feature.
 * @param latlng - Координаты.
 * @param defaults - Настройки по умолчанию.
 * @param renderer - Canvas renderer.
 * @returns Leaflet marker.
 */
function createMarker(feature: any, latlng: LatLngExpression, defaults: any, renderer?: any) {
    let popupText = feature.properties?.description || null;
    let tooltipText = feature.properties?.iconCaption || feature.properties?.name || null;
    let fillColor = feature.properties?.["marker-color"] || feature.properties?.fillColor || feature.properties?.color || defaults.FillColor;
    let size = feature.properties?.radius || defaults.Size;
    let iconName = feature.properties?.iconName || defaults.IconName || "circle-fill";

    if (size <= 12 || iconName === "circle-fill") {
        const point = circleMarker(latlng, {
            radius: size / 2,
            fillColor,
            color: defaults.BorderColor,
            weight: 1,
            opacity: 1,
            fillOpacity: 1,
            renderer,
        });

        attachLazyInteractions(point, {
            popupContent: popupText ? wrapLinks(textToHtml(popupText)) : "",
            tooltipContent: tooltipText ? wrapLinks(tooltipText) : "",
        });

        return point;
    }

    const svgIcon = divIcon({
        html: strFormatArgs(mapIcons[iconName], size, fillColor, defaults.BorderColor),
        className: "svg-icon",
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });

    const markerLayer = marker(latlng, {opacity: 1, icon: svgIcon});
    attachLazyInteractions(markerLayer, {
        popupContent: popupText ? wrapLinks(textToHtml(popupText)) : "",
        tooltipContent: tooltipText ? wrapLinks(tooltipText) : "",
    });
    return markerLayer;
}

/**
 * Выполняет обработку батчами.
 *
 * @param items - Элементы.
 * @param batchSize - Размер батча.
 * @param renderItem - Функция обработки.
 */
async function renderInBatches<T>(items: T[], batchSize: number, renderItem: (item: T) => void) {
    for (let index = 0; index < items.length; index += batchSize) {
        const batch = items.slice(index, index + batchSize);

        for (let itemIndex = 0; itemIndex < batch.length; itemIndex++) {
            renderItem(batch[itemIndex]);
        }

        if (index + batchSize < items.length) {
            await nextAnimationFrame();
        }
    }
}

/**
 * Возвращает promise следующего animation frame.
 *
 * @returns Promise кадра.
 */
function nextAnimationFrame(): Promise<void> {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

/**
 * Ленивая инициализация popup и tooltip.
 *
 * @param layer - Leaflet layer.
 * @param config - Конфигурация взаимодействий.
 */
function attachLazyInteractions(layer: any, config: { popupContent?: string; tooltipContent?: string }) {
    if (config.tooltipContent) {
        layer.on("mouseover", () => {
            if (!layer.getTooltip()) {
                layer.bindTooltip(config.tooltipContent);
            }
        });
    }

    if (config.popupContent) {
        layer.on("click", () => {
            if (!layer.getPopup()) {
                layer.bindPopup(config.popupContent, popupDefaultOptions);
            }

            layer.openPopup();
        });
    }
}

/**
 * Убеждается, что popup уже создан.
 *
 * @param marker - Данные точки.
 */
function ensurePointPopupBound(marker: PointData) {
    if (marker.point && !marker.point.getPopup()) {
        marker.point.bindPopup(marker.popupContent, popupDefaultOptions);
    }
}

/**
 * Добавляет точку в spatial index.
 *
 * @param index - Пространственный индекс.
 * @param point - Данные точки.
 */
function addPointToSpatialIndex(index: Map<string, PointData[]>, point: PointData) {
    const key = getCellKey(toLatLng(point.latlng).lat, toLatLng(point.latlng).lng);
    const bucket = index.get(key);

    if (bucket) {
        bucket.push(point);
        return;
    }

    index.set(key, [point]);
}

/**
 * Добавляет точку в индекс по исходному идентификатору backend.
 *
 * @param index - Индекс точек.
 * @param point - Данные точки.
 */
function addPointToSourceIndex(index: Map<string, PointData[]>, point: PointData) {
    const bucket = index.get(point.sourceId);

    if (bucket) {
        bucket.push(point);
        return;
    }

    index.set(point.sourceId, [point]);
}

/**
 * Добавляет статический объект в spatial index.
 *
 * @param index - Пространственный индекс.
 * @param element - Данные объекта.
 */
function addElementToSpatialIndex(index: Map<string, StaticElementData[]>, element: StaticElementData) {
    const keys = getBoundsCellKeys(element.bounds);

    for (let i = 0; i < keys.length; i++) {
        const bucket = index.get(keys[i]);
        if (bucket) {
            bucket.push(element);
        } else {
            index.set(keys[i], [element]);
        }
    }
}

/**
 * Собирает кандидатов из spatial index для заданных bounds.
 *
 * @param index - Пространственный индекс.
 * @param bounds - Границы viewport.
 * @returns Список кандидатов без дубликатов.
 */
function collectSpatialCandidates<T extends { id: string }>(index: Map<string, T[]>, bounds: LatLngBounds): T[] {
    const keys = getBoundsCellKeys(bounds);
    const ids = new Set<string>();
    const result: T[] = [];

    for (let i = 0; i < keys.length; i++) {
        const bucket = index.get(keys[i]);
        if (!bucket) {
            continue;
        }

        for (let j = 0; j < bucket.length; j++) {
            const item = bucket[j];
            if (!ids.has(item.id)) {
                ids.add(item.id);
                result.push(item);
            }
        }
    }

    return result;
}

/**
 * Возвращает cell keys для bounds.
 *
 * @param bounds - Географические границы.
 * @returns Набор ключей spatial grid.
 */
function getBoundsCellKeys(bounds: LatLngBounds) {
    const southWest = bounds.getSouthWest();
    const northEast = bounds.getNorthEast();
    const latStart = Math.floor(southWest.lat / spatialCellSize);
    const latEnd = Math.floor(northEast.lat / spatialCellSize);
    const lngStart = Math.floor(southWest.lng / spatialCellSize);
    const lngEnd = Math.floor(northEast.lng / spatialCellSize);
    const keys: string[] = [];

    for (let latIndex = latStart; latIndex <= latEnd; latIndex++) {
        for (let lngIndex = lngStart; lngIndex <= lngEnd; lngIndex++) {
            keys.push(`${latIndex}:${lngIndex}`);
        }
    }

    return keys;
}

/**
 * Возвращает ключ grid cell по координатам.
 *
 * @param lat - Широта.
 * @param lng - Долгота.
 * @returns Ключ ячейки.
 */
function getCellKey(lat: number, lng: number) {
    return `${Math.floor(lat / spatialCellSize)}:${Math.floor(lng / spatialCellSize)}`;
}

/**
 * Возвращает элементы множества, которых нет в другом множестве.
 *
 * @param left - Исходное множество.
 * @param right - Множество исключения.
 * @returns Разность множеств в виде массива.
 */
function difference(left: Set<string>, right: Set<string>) {
    const result: string[] = [];

    left.forEach((value) => {
        if (!right.has(value)) {
            result.push(value);
        }
    });

    return result;
}

/**
 * Ищет статический объект по идентификатору.
 *
 * @param elements - Список статических объектов.
 * @param id - Идентификатор объекта.
 * @returns Найденный объект или undefined.
 */
function findStaticElementById(elements: StaticElementData[], id: string) {
    for (let i = 0; i < elements.length; i++) {
        if (elements[i].id === id) {
            return elements[i];
        }
    }

    return undefined;
}

/**
 * Преобразует выражение координат в LatLng.
 *
 * @param latlng - Координаты.
 * @returns LatLng.
 */
function toLatLng(latlng: LatLngExpression): LatLng {
    if (latlng instanceof LatLng) {
        return latlng;
    }

    if (Array.isArray(latlng)) {
        return new LatLng(Number(latlng[0]), Number(latlng[1]));
    }

    return new LatLng(Number(latlng.lat), Number(latlng.lng));
}

/**
 * Возвращает bounds GeoJSON feature.
 *
 * @param feature - GeoJSON feature.
 * @returns Bounds feature.
 */
function getFeatureBounds(feature: any): LatLngBounds {
    if (feature.geometry.type === "Point") {
        const latlng = GeoJSON.coordsToLatLng(feature.geometry.coordinates);
        return new LatLngBounds(latlng, latlng);
    }

    if (feature.geometry.type === "LineString") {
        return new LatLngBounds(GeoJSON.coordsToLatLngs(feature.geometry.coordinates) as LatLng[]);
    }

    return new LatLngBounds(GeoJSON.coordsToLatLngs(feature.geometry.coordinates[0]) as LatLng[]);
}

/**
 * Возвращает anchor-координату feature для поиска и центрирования.
 *
 * @param feature - GeoJSON feature.
 * @returns Координата привязки.
 */
function getFeatureAnchor(feature: any): LatLngExpression {
    if (feature.geometry.type === "Point") {
        return GeoJSON.coordsToLatLng(feature.geometry.coordinates);
    }

    if (feature.geometry.type === "LineString") {
        return (GeoJSON.coordsToLatLngs(feature.geometry.coordinates) as LatLng[])[0];
    }

    return (GeoJSON.coordsToLatLngs(feature.geometry.coordinates[0]) as LatLng[])[0];
}

const mapIcons: Record<string, string> = {
    "circle-fill": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="0 0 16 16">
          <circle cx="8" cy="8" r="7" stroke="{2}" />
        </svg>`,
    "half-circle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="-1 -1 18 18">
          <path d="M8 15A7 7 0 1 0 8 1zm0 1A8 8 0 1 1 8 0a8 8 0 0 1 0 16"/>
        </svg>`,
    "triangle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="0 0 16 17">
          <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{2}" />
        </svg>`,
    "square": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="-1 -1 18 18">
          <path stroke="{2}" d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2z"/>
        </svg>`,
    "record-circle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
          <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" stroke="{2}" />
        </svg>`,
    "wrench-circle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="0 0 16 16">
          <path d="M12.496 8a4.491 4.491 0 0 1-1.703 3.526L9.497 8.5l2.959-1.11c.027.2.04.403.04.61Z"/>
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1 0a7 7 0 1 0-13.202 3.249l1.988-1.657a4.5 4.5 0 0 1 7.537-4.623L7.497 6.5l1 2.5 1.333 3.11c-.56.251-1.18.39-1.833.39a4.49 4.49 0 0 1-1.592-.29L4.747 14.2A7 7 0 0 0 15 8Zm-8.295.139a.25.25 0 0 0-.288-.376l-1.5.5.159.474.808-.27-.595.894a.25.25 0 0 0 .287.376l.808-.27-.595.894a.25.25 0 0 0 .287.376l1.5-.5-.159-.474-.808.27.596-.894a.25.25 0 0 0-.288-.376l-.808.27.596-.894Z"/>
        </svg>`,
    "diamond": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="-1 -1 18 18">
          <path fill-rule="evenodd" d="M6.95.435c.58-.58 1.52-.58 2.1 0l6.515 6.516c.58.58.58 1.519 0 2.098L9.05 15.565c-.58.58-1.519.58-2.098 0L.435 9.05a1.482 1.482 0 0 1 0-2.098L6.95.435z" stroke="{2}" />
        </svg>`,
    "pentagon": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="-1 -1 18 18">
          <path stroke="{2}" d="M7.685.256a.5.5 0 0 1 .63 0l7.421 6.03a.5.5 0 0 1 .162.538l-2.788 8.827a.5.5 0 0 1-.476.349H3.366a.5.5 0 0 1-.476-.35L.102 6.825a.5.5 0 0 1 .162-.538l7.42-6.03Z"/>
        </svg>`,
    "hexagon": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="-1 -1 18 18">
          <path stroke="{2}" fill-rule="evenodd" d="M8.5.134a1 1 0 0 0-1 0l-6 3.577a1 1 0 0 0-.5.866v6.846a1 1 0 0 0 .5.866l6 3.577a1 1 0 0 0 1 0l6-3.577a1 1 0 0 0 .5-.866V4.577a1 1 0 0 0-.5-.866z"/>
        </svg>`,
    "circle-in-triangle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
          <circle cx="8" cy="10" r="4" stroke="{2}" />
        </svg>`,
    "warning": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" viewBox="-1 -1 18 18">
          <path stroke="{2}" d="M9.05.435c-.58-.58-1.52-.58-2.1 0L.436 6.95c-.58.58-.58 1.519 0 2.098l6.516 6.516c.58.58 1.519.58 2.098 0l6.516-6.516c.58-.58.58-1.519 0-2.098zM8 4c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
        </svg>`,
};
