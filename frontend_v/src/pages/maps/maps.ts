import {
    CircleMarker,
    circleMarker,
    Control,
    divIcon,
    featureGroup,
    GeoJSON,
    LatLng,
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
    point: CircleMarker;
    layer: Layer;
    popupContent: string;
    searchText: string;
    currentProblemsContent?: string;
    _origin?: OriginPointData;
    hasProblems: boolean;
}

interface StaticPointData {
    latlng: LatLngExpression;
    name?: string;
    description?: string;
    searchText: string;
    element: any;
}

const popupDefaultOptions = {maxWidth: 1200};
const defaultMapCenter: LatLngExpression = [44.6, 33.5];
const defaultMapZoom = 12;

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
    public staticElements: StaticPointData[] = [];
    public overlays: LayersObject = {};

    private updateInFlight = false;

    constructor(public mapID: string, public mapHTMLElementID: string) {
        this.map = new LMap(mapHTMLElementID, {layers: [osm], minZoom: 5});
        this.map.setView(defaultMapCenter, defaultMapZoom);
        this.map.attributionControl.getContainer()?.remove();
        this.map.addControl(new Control.Scale());
        this.map.on("overlayadd overlayremove", () => saveLayers(this.mapID, this.map, this.overlays));
    }

    /**
     * Загружает подробные данные карты для текущего экземпляра сервиса.
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
     * Создает группы слоев и панель переключения для карты.
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
     * Загружает все объекты карты для рендера.
     *
     * @returns Массив данных для рендера.
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
     * Рендерит все объекты карты.
     */
    async renderMarkers() {
        const renderData = await this.loadMarkers();

        for (let i = 0; i < renderData.length; i++) {
            if (renderData[i].type === "zabbix") {
                this.renderZabbixMarkers(renderData[i]);
            } else if (renderData[i].type === "geojson") {
                this.renderGeoJSON(renderData[i]);
            }
        }
    }

    /**
     * Рендерит динамические маркеры Zabbix и подготавливает поисковый индекс.
     *
     * @param data - Данные слоя.
     */
    private renderZabbixMarkers(data: any) {
        const layer = this.overlays[data.name] as any;

        for (const feature of data.features.features) {
            const tooltipContent = feature.properties.name || "";
            const popupContent = feature.properties.description || "";
            const point = circleMarker(
                [...feature.geometry.coordinates].reverse() as [number, number],
                feature.properties.style,
            )
                .bindTooltip(tooltipContent)
                .bindPopup(popupContent, popupDefaultOptions)
                .addTo(layer);

            this.points.set(feature.id, {
                point,
                layer,
                popupContent,
                searchText: normalizeSearchText([tooltipContent, popupContent]),
                hasProblems: false,
            });
        }
    }

    /**
     * Рендерит статические GeoJSON-объекты и индексирует их для поиска.
     *
     * @param data - Данные слоя.
     */
    private renderGeoJSON(data: any) {
        const defaultSettings = data.properties;
        const features = data.features.features;
        const layer = this.overlays[data.name] as any;

        for (let j = 0; j < features.length; j++) {
            if (features[j].geometry.type === "Point") {
                const point = createMarker(
                    features[j],
                    GeoJSON.coordsToLatLng(features[j].geometry.coordinates),
                    defaultSettings.Marker,
                ).addTo(layer);

                this.staticElements.push({
                    element: point,
                    latlng: point.getLatLng(),
                    name: features[j].properties.name || features[j].properties.iconCaption,
                    description: features[j].properties.description,
                    searchText: normalizeSearchText([
                        features[j].properties.name,
                        features[j].properties.iconCaption,
                        features[j].properties.description,
                    ]),
                });
            } else if (features[j].geometry.type === "LineString") {
                const line = createPolyline(
                    features[j],
                    GeoJSON.coordsToLatLngs(features[j].geometry.coordinates),
                    defaultSettings.Polygon,
                ).addTo(layer);

                this.staticElements.push({
                    element: line,
                    latlng: line.getLatLngs()[0] as LatLngExpression,
                    name: features[j].properties.name,
                    description: features[j].properties.description,
                    searchText: normalizeSearchText([
                        features[j].properties.name,
                        features[j].properties.description,
                    ]),
                });
            } else if (features[j].geometry.type === "Polygon") {
                const polygonLayer = createPolygon(
                    features[j],
                    GeoJSON.coordsToLatLngs(features[j].geometry.coordinates[0]),
                    defaultSettings.Polygon,
                ).addTo(layer);

                this.staticElements.push({
                    element: polygonLayer,
                    latlng: (polygonLayer.getLatLngs()[0] as LatLng[])[0] as LatLngExpression,
                    name: features[j].properties.name,
                    description: features[j].properties.description,
                    searchText: normalizeSearchText([
                        features[j].properties.name,
                        features[j].properties.description,
                    ]),
                });
            }
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
     * Обновляет состояние аварийных маркеров без параллельных запросов.
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
                const pointID = problems[i].id;
                const marker = this.points.get(pointID);

                if (!marker) {
                    continue;
                }

                if (!marker._origin) {
                    marker._origin = {
                        fillColor: marker.point.options.fillColor,
                        popupContent: marker.popupContent,
                        layer: marker.layer,
                    };
                }

                const problemsText = buildProblemsText(problems[i]);

                if (marker.hasProblems && marker.currentProblemsContent === problemsText) {
                    problemsPointsBeforeUpdate.delete(pointID);
                    continue;
                }

                if (marker.hasProblems && marker.currentProblemsContent !== problemsText) {
                    marker.point.bindPopup(marker._origin.popupContent + problemsText, popupDefaultOptions);
                } else {
                    marker.hasProblems = true;
                    marker.point.setStyle({fillColor: "red"});
                    marker.point.setPopupContent(marker._origin.popupContent + problemsText);
                }

                marker.currentProblemsContent = problemsText;
                problemsPointsBeforeUpdate.delete(pointID);
            }

            problemsPointsBeforeUpdate.forEach((value) => {
                if (!value._origin) {
                    return;
                }

                value.point.setStyle({fillColor: value._origin.fillColor});
                value.point.setPopupContent(value._origin.popupContent);
                value.currentProblemsContent = undefined;
                value._origin = undefined;
                value.hasProblems = false;
            });
        } finally {
            this.updateInFlight = false;
        }
    }

    /**
     * Ищет элементы на карте по заранее подготовленному текстовому индексу.
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
                    this.focusMap(point.point.getLatLng(), 17);
                    marker = point;
                }

                this.highlightMarker(point.point);
            }
        }

        for (const element of this.staticElements) {
            if (element.searchText.includes(normalizedText)) {
                if (!marker) {
                    this.focusMap(element.latlng, 17);
                    marker = element;
                }

                this.highlightMarker(element.element);
            }
        }

        return marker;
    }

    /**
     * Временно подсвечивает найденный объект.
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
     * Центрирует карту на объекте безопасно даже до завершения геолокации.
     *
     * @param latlng - Координаты точки.
     * @param zoom - Целевой зум.
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
 * Создает нормализованную строку для быстрого поиска.
 *
 * @param values - Набор значений для индексации.
 * @returns Нормализованная строка.
 */
function normalizeSearchText(values: unknown[]): string {
    return values
        .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
        .join(" ")
        .toLowerCase();
}

/**
 * Формирует HTML с проблемами узла.
 *
 * @param problem - Описание проблем узла.
 * @returns HTML-строка для popup.
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
 * Создает полигон из GeoJSON feature.
 *
 * @param feature - GeoJSON feature.
 * @param latlng - Координаты полигона.
 * @param defaults - Настройки по умолчанию.
 * @returns Leaflet polygon.
 */
function createPolygon(feature: any, latlng: LatLngExpression[], defaults: any) {
    const options = {
        fillColor: feature.properties.fill || defaults.FillColor,
        color: feature.properties.stroke || defaults.BorderColor,
        weight: Number(feature.properties["stroke-width"]) || 2,
        opacity: feature.properties["stroke-opacity"] || defaults.Opacity,
        fillOpacity: feature.properties["fill-opacity"] || defaults.Opacity,
    };

    const popupText = feature.properties ? feature.properties.description : null;
    const polygonLayer = polygon(latlng, options);

    if (popupText) {
        polygonLayer.bindPopup(wrapLinks(textToHtml(popupText)), popupDefaultOptions);
    }

    return polygonLayer;
}

/**
 * Создает полилинию из GeoJSON feature.
 *
 * @param feature - GeoJSON feature.
 * @param latlng - Координаты линии.
 * @param defaults - Настройки по умолчанию.
 * @returns Leaflet polyline.
 */
function createPolyline(feature: any, latlng: LatLngExpression[], defaults: any) {
    const options = {
        color: feature.properties.stroke || defaults.BorderColor,
        weight: feature.properties["stroke-width"] || 2,
        fillOpacity: feature.properties["stroke-opacity"] || defaults.Opacity,
    };

    const popupText = feature.properties ? feature.properties.description : null;
    const line = polyline(latlng, options);

    if (popupText) {
        line.bindPopup(wrapLinks(textToHtml(popupText)), popupDefaultOptions);
    }

    return line;
}

/**
 * Создает маркер из GeoJSON feature.
 *
 * @param feature - GeoJSON feature.
 * @param latlng - Координаты маркера.
 * @param defaults - Настройки по умолчанию.
 * @returns Leaflet marker.
 */
function createMarker(feature: any, latlng: LatLngExpression, defaults: any) {
    let popupText = null;
    let tooltipText = null;
    let fillColor = defaults.FillColor;
    let size = defaults.Size;
    let iconName = defaults.IconName || "circle-fill";

    if (feature.properties) {
        popupText = feature.properties.description;
        tooltipText = feature.properties.iconCaption || feature.properties.name;
        fillColor = feature.properties["marker-color"] || feature.properties.fillColor || feature.properties.color || defaults.FillColor;
        size = feature.properties.radius || defaults.Size;
        iconName = feature.properties.iconName || defaults.IconName || "circle-fill";
    }

    const svgIcon = divIcon({
        html: strFormatArgs(mapIcons[iconName], size, fillColor, defaults.BorderColor),
        className: "svg-icon",
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });

    const markerLayer = marker(latlng, {
        opacity: 1,
        icon: svgIcon,
    });

    if (popupText) {
        markerLayer.bindPopup(wrapLinks(textToHtml(popupText)), popupDefaultOptions);
    }

    if (tooltipText) {
        markerLayer.bindTooltip(wrapLinks(tooltipText));
    }

    return markerLayer;
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
