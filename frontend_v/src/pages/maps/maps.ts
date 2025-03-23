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
    point: CircleMarker,
    layer: Layer,
    _origin?: OriginPointData,
    hasProblems: boolean;
}

interface StaticPointData {
    latlng: LatLngExpression;
    name?: string;
    description?: string;
    element: any;
}


const popupDefaultOptions = {maxWidth: 1200}

export type MapsPage = Paginator<MapBrief>;

const geoGoogle = tileLayer('https://www.google.com/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}', {attribution: 'google'});
const arcgisonline = tileLayer('http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}');
const osm = tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");

export class MapService {
    public mapData: MapBrief | null = null;
    public mapGroups: string[] = [];

    public map: LMap;

    // Объект для хранения всех динамических маркеров, добавленных на карту.
    public points: Map<string, PointData> = new Map();

    // Объект для хранения всех статических элементов.
    public staticElements: StaticPointData[] = [];

    /* Переменная, используемая для хранения всех слоев, добавляемых на карту. */
    public overlays: LayersObject = {};

    constructor(public mapID: string, public mapHTMLElementID: string) {
        this.map = new LMap(mapHTMLElementID, {layers: [osm], minZoom: 5}); // Оставляем только OSM при инициализации
        this.map.attributionControl.getContainer()?.remove();
        this.map.addControl(new Control.Scale());

        // Подписываемся на изменение слоев
        this.map.on('overlayadd overlayremove', () => saveLayers(this.mapID, this.map, this.overlays));
    }

    async getMapData() {
        try {
            const resp = await api.get<MapDetail>("/api/v1/maps/" + this.mapID);
            this.mapData = resp.data;
            return resp.data;
        } catch (error: any) {
            errorToast("Не удалось загрузить карту", errorFmt(error))
            return null;
        }
    }

    async getMapGroups() {
        try {
            let response = await api.get<{ groups: string[] }>(`/api/v1/maps/${this.mapID}/layers`);
            this.mapGroups = response.data.groups;
            return response.data.groups;
        } catch (error: any) {
            errorToast("Не удалось получить список групп", errorFmt(error))
        }
    }

    async renderMapGroups() {
        if (!this.mapGroups.length) await this.getMapGroups();

        for (let i = 0; i < this.mapGroups.length; i++) {
            this.overlays[this.mapGroups[i]] = featureGroup([])
        }

        this.map.addControl(new Control.Layers(
            {"Спутник старый": geoGoogle, "Спутник новый": arcgisonline, "Схема": osm},
            this.overlays,
            {autoZIndex: true, collapsed: true, position: "topright", sortLayers: true})
        );

        loadLayers(this.mapID, this.map, this.overlays);
    }

    async loadMarkers() {
        try {
            let response = await api.get<any[]>(`/api/v1/maps/${this.mapID}/render`);
            return response.data
        } catch (error: any) {
            errorToast("Не удалось получить данные", errorFmt(error))
            return []
        }
    }

    async renderMarkers() {
        const renderData = await this.loadMarkers();

        for (let i = 0; i < renderData.length; i++) {
            if (renderData[i].type == "zabbix") {
                this.renderZabbixMarkers(renderData[i]);
            } else if (renderData[i].type == "geojson") {
                this.renderGeoJSON(renderData[i])
            }
        }
    }

    private renderZabbixMarkers(data: any) {
        // Отображаем данные узлов сети Zabbix на карте
        console.log(data)
        for (const feature of data.features.features) {
            /* Он проверяет, является ли маркер кругом. */
            // if (feature.properties.figure === "circle") {
            const point = circleMarker(feature.geometry.coordinates.reverse(), feature.properties.style)
                .bindTooltip(feature.properties.name)
                // @ts-ignore
                .bindPopup(feature.properties.description, popupDefaultOptions).addTo(this.overlays[data.name]);

            /* Он создает новый маркер круга и добавляет его к объекту точек. */
            this.points.set(feature.id, {
                    point: point,
                    layer: this.overlays[data.name],
                    hasProblems: false
                }
            )
        }
    }

    private renderGeoJSON(data: any) {

        // Настройки по умолчанию для слоя
        let defaultSettings = data.properties
        // Коллекция
        let features = data.features.features
        // Слой
        let layer = this.overlays[data.name]

        for (let j = 0; j < features.length; j++) {

            /* Создание маркера из объекта GeoJSON */
            if (features[j].geometry.type === "Point") {
                let point = createMarker(
                    features[j],
                    GeoJSON.coordsToLatLng(features[j].geometry.coordinates),
                    defaultSettings.Marker
                    // @ts-ignore
                ).addTo(layer)
                this.staticElements.push(
                    {
                        element: point,
                        latlng: point.getLatLng(),
                        name: features[j].properties.name || features[j].properties.iconCaption,
                        description: features[j].properties.description,
                    }
                )

                /* Создание полилинии из объекта GeoJSON */
            } else if (features[j].geometry.type === "LineString") {
                let polyline = createPolyline(
                    features[j],
                    GeoJSON.coordsToLatLngs(features[j].geometry.coordinates),
                    defaultSettings.Polygon
                    // @ts-ignore
                ).addTo(layer)
                this.staticElements.push(
                    {
                        element: polyline,
                        latlng: <LatLngExpression>polyline.getLatLngs()[0],
                        name: features[j].properties.name,
                        description: features[j].properties.description,
                    }
                )

                /* Создание многоугольника из объекта GeoJSON */
            } else if (features[j].geometry.type === "Polygon") {
                let polygon = createPolygon(
                    features[j],
                    GeoJSON.coordsToLatLngs(features[j].geometry.coordinates[0]),
                    defaultSettings.Polygon
                    // @ts-ignore
                ).addTo(layer)
                this.staticElements.push(
                    {
                        element: polygon,
                        latlng: <LatLngExpression>(<LatLng[]>polygon.getLatLngs()[0])[0],
                        name: features[j].properties.name,
                        description: features[j].properties.description,
                    }
                )
            }
        }
    }

    async getProblems(): Promise<Problems[]> {
        try {
            let resp = await api.get<{ problems: Problems[] }>(`/api/v1/maps/${this.mapID}/update`)
            return resp.data.problems;
        } catch (error: any) {
            errorToast("Не удалось получить данные", errorFmt(error))
            return []
        }
    }

    async update() {
        const problems = await this.getProblems();
        if (!problems.length) return;

        // Список из точек текущих недоступных узлов сети на карте
        let problemsPointsBeforeUpdate: Map<string, PointData> = new Map();
        this.points.forEach((value, key) => {
            if (value.hasProblems) problemsPointsBeforeUpdate.set(key, value)
        })

        for (let i = 0; i < problems.length; i++) {
            // console.log(problems[i])

            // pointID недоступного узла сети
            let pointID = problems[i].id

            const marker = this.points.get(pointID)

            if (!marker) continue;

            if (!marker._origin) {
                marker._origin = {
                    fillColor: marker.point.options.fillColor,
                    // @ts-ignore
                    popupContent: marker.point._popup._content,
                    layer: marker.layer
                }
            }

            // Текст проблем
            let problems_text = ""
            for (let j = 0; j < problems[i].acknowledges.length; j++) {
                let ack_time = problems[i].acknowledges[j][1]
                let ack_text = problems[i].acknowledges[j][0]
                let html = textToHtml(ack_text, false)
                problems_text += `<div><p><span style="color: #2400ff; font-family: monospace;">${ack_time}</span> -> ${html}</p></div>`
            }

            // Если уже недоступен и описание проблем не изменилось, то пропускаем
            // @ts-ignore
            if (marker.hasProblems && marker.point._popup._content === problems_text) {
                continue

                // @ts-ignore
            } else if (marker.hasProblems && marker.point._popup._content !== problems_text) {
                // Если уже недоступен, НО описание проблем изменилось.
                marker.point.bindPopup(
                    marker._origin.popupContent + problems_text, popupDefaultOptions
                )
            } else {
                // Новое недоступное оборудование
                marker.hasProblems = true;
                marker.point.setStyle({fillColor: "red"})
                marker.point.setPopupContent(marker._origin.popupContent + problems_text)
            }

            // Удаляем маркер, так как он ещё проблемный.
            problemsPointsBeforeUpdate.delete(pointID)
        }

        /* Восстановление устройств, которые раньше были отключены, а теперь работают. */
        problemsPointsBeforeUpdate.forEach((value) => {
            if (!value._origin) return;
            value.point.setStyle({fillColor: value._origin.fillColor})   // Восстанавливаем цвет
            value.point.setPopupContent(value._origin.popupContent)
            // value.point.bindPopup(value._origin.popupContent, {"maxWidth": 500})  // Восстанавливаем описание
            value._origin = undefined;
            value.hasProblems = false;
        });

    }

    searchPoint(text: string) {
        text = text.toString().toLowerCase()
        let marker = null
        for (let point of this.points.values()) {
            let name = point.point.getTooltip()?.getContent()?.toString()
            let desc = point.point.getPopup()?.getContent()?.toString()
            if (name && name.toLowerCase().includes(text) || desc && desc.toLowerCase().includes(text)) {
                if (!marker) {
                    this.map.flyTo(point.point.getLatLng(), 17)
                    marker = point
                }
                this.highlightMarker(point.point)
            }
        }

        for (let element of this.staticElements) {
            if (element.name && element.name.toLowerCase().includes(text) || element.description && element.description.toLowerCase().includes(text)) {
                if (!marker) {
                    this.map.flyTo(element.latlng, 17)
                    marker = element
                }
                this.highlightMarker(element.element)
            }
        }

        return marker;
    }

    private highlightMarker(marker: any) {
        if (!marker._path) return;

        if (!marker.options._originFillColor) {
            marker.options._originFillColor = marker.options.fillColor
        }

        for (let i = 1; i <= 20; i++) {
            setTimeout(() => {
                marker._path.style.fill = i % 2 === 0 ? marker.options._originFillColor : "orange";
                marker._path.style.fill = i % 2 === 0 ? marker.options._originFillColor : "orange";
            }, 250 * i)
        }

        setTimeout(() => marker._path.style.fill = marker.options._originFillColor, 5100)
    }

}


/**
 * Эта функция создает полилинию из объекта GeoJSON, используя значения по умолчанию для цвета, веса и непрозрачности,
 * если объект не имеет этих свойств.
 *  Возвращает полигональный объект Leaflet.
 *
 * @param feature - Объект функции GeoJSON
 * @param latlng - Координаты многоугольника
 * @param defaults - Это словарь значений по умолчанию для полигона.
 * @returns Полигональный объект
 */
function createPolygon(feature: any, latlng: LatLngExpression[], defaults: any) {
    /* Создание словаря вариантов стиля полигона. */
    let options = {
        "fillColor": feature.properties["fill"] || defaults["FillColor"],
        "color": feature.properties["stroke"] || defaults["BorderColor"],
        "weight": Number(feature.properties["stroke-width"]) || 2,
        "opacity": feature.properties["stroke-opacity"] || defaults.Opacity,
        "fillOpacity": feature.properties["fill-opacity"] || defaults.Opacity,
    }

    let popup_text = null

    if (feature.properties) {
        popup_text = feature.properties.description
    }

    let p = polygon(latlng, options)

    if (popup_text) {
        p.bindPopup(wrapLinks(textToHtml(popup_text)), popupDefaultOptions)
    }

    return p
}

/**
 * Эта функция создает полилинию из объекта GeoJSON, используя значения по умолчанию для цвета, веса и непрозрачности,
 * если объект не имеет этих свойств.
 *  Возвращает полигональный объект Leaflet.
 *
 * @param feature - Объект функции GeoJSON
 * @param latlng - массив координат широты/долготы
 * @param defaults - Значения по умолчанию для карты.
 * @returns Полилинейный объект
 */
function createPolyline(feature: any, latlng: LatLngExpression[], defaults: any) {
    /* Создание словаря опций стиля для полилинии. */
    let options = {
        "color": feature.properties.stroke || defaults.BorderColor,
        "weight": feature.properties["stroke-width"] || 2,
        "fillOpacity": feature.properties["stroke-opacity"] || defaults.Opacity,
    }

    let popup_text = null

    if (feature.properties) {
        popup_text = feature.properties.description
    }

    let p = polyline(latlng, options)

    if (popup_text) {
        p.bindPopup(wrapLinks(textToHtml(popup_text)), popupDefaultOptions)
    }

    /* Возврат полилинейного объекта. */
    return p
}


/**
 * Эта функция создает маркер из объекта GeoJSON, используя значения по умолчанию для цвета, имени иконки и размера,
 * если объект не имеет этих свойств.
 * @param feature - функция GeoJSON
 * @param latlng - Широта и долгота маркера
 * @param defaults - словарь значений по умолчанию для маркера
 * @returns Маркер
 */
function createMarker(feature: any, latlng: LatLngExpression, defaults: any) {
    // console.log(feature, defaults)

    let popup_text = null
    let tooltip_text = null
    let fillColor = defaults["FillColor"]
    let size = defaults["Size"]
    let icon_name = defaults["IconName"] || "circle-fill"

    /* Приведенный выше код устанавливает значения по умолчанию для текста всплывающего окна, текста всплывающей подсказки,
    цвета заливки, размера и имени значка. */
    if (feature.properties) {
        popup_text = feature.properties.description

        tooltip_text = feature.properties.iconCaption ||
            feature.properties.name

        fillColor = feature.properties["marker-color"] ||
            feature.properties.fillColor ||
            feature.properties.color || defaults["FillColor"]

        size = feature.properties.radius ||
            defaults["Size"]

        icon_name = feature.properties.iconName ||
            defaults["IconName"] || "circle-fill"
    }

    /* Создание новой иконки для маркера. */
    let svgIcon = divIcon({
        html: strFormatArgs(mapIcons[icon_name], size, fillColor, defaults["BorderColor"]),
        className: "svg-icon",
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });

    let options = {
        "opacity": 1,
        "icon": svgIcon
    }

    /* Создание маркера по координатам широты с указанными параметрами. */
    let m = marker(latlng, options);

    /* Создание всплывающего окна для маркера. */
    if (popup_text) {
        m.bindPopup(wrapLinks(textToHtml(popup_text)), popupDefaultOptions)
    }
    /* Создание всплывающей подсказки для маркера. */
    if (tooltip_text) {
        m.bindTooltip(wrapLinks(tooltip_text))
    }
    return m
}


const mapIcons: any = {
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
}
