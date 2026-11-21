import { DomEvent, type Layer, type LeafletMouseEvent, type PopupEvent, type PopupOptions } from "leaflet";

const descriptionTags = new Set(
    "a b blockquote br caption code dd div dl dt em h1 h2 h3 h4 h5 h6 hr i img input label li ol p pre s small span strong sub sup table tbody td th thead tfoot tr u ul".split(" ")
);
const descriptionStyleProperties = [
    "background-color",
    "border",
    "border-collapse",
    "border-radius",
    "color",
    "font-size",
    "font-weight",
    "letter-spacing",
    "line-height",
    "margin",
    "padding",
    "text-align",
];

export function bindLazyPopup(layer: Layer, content: string | (() => HTMLElement), options: PopupOptions) {
    layer.once("click", (event: LeafletMouseEvent) => {
        if (!layer.getPopup()) {
            layer.bindPopup(typeof content === "string" ? content : content(), options);
            DomEvent.stopPropagation(event);
            layer.openPopup(event.latlng);
        }
    });
}

export function bindGeoJsonPopup(layer: Layer, description: unknown, showExpanded: (html: string) => void) {
    if (typeof description !== "string" || !description.trim()) {
        return;
    }

    bindLazyPopup(layer, () => renderDescription(description), {
        className: "geojson-popup",
        maxWidth: Infinity,
    });

    layer.on("popupopen", ({ popup }: PopupEvent) => {
        const content = popup.getElement()!.querySelector<HTMLElement>(".leaflet-popup-content")!;
        const expandIfNeeded = () => {
            if (content.scrollWidth > content.clientWidth || content.scrollHeight > content.clientHeight) {
                for (const checkbox of content.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')) {
                    checkbox.defaultChecked = checkbox.checked;
                }
                showExpanded(content.innerHTML);
                layer.closePopup();
            }
        };

        const observer = new ResizeObserver(expandIfNeeded);
        observer.observe(content);
        observer.observe(content.firstElementChild!);
        const updatePopupLayout = () => {
            const focused = document.activeElement;
            popup.update();
            expandIfNeeded();
            if (popup.isOpen() && focused instanceof HTMLElement && content.contains(focused)) {
                focused.focus({ preventScroll: true });
            }
        };
        content.addEventListener("load", updatePopupLayout, true);
        content.addEventListener("change", updatePopupLayout);
        layer.once("popupclose", () => {
            observer.disconnect();
            content.removeEventListener("load", updatePopupLayout, true);
            content.removeEventListener("change", updatePopupLayout);
        });
        expandIfNeeded();
    });
}

function renderDescription(description: string) {
    const source = document.createElement("template");
    const content = document.createElement("div");
    content.className = "geojson-description";
    source.innerHTML = description;
    appendDescription(content, source.content);
    return content;
}

// Build fresh elements so attributes and executable markup from the file never enter the map DOM.
function appendDescription(target: HTMLElement, source: ParentNode, linkify = true) {
    for (const node of source.childNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent ?? "";
            let end = 0;
            if (linkify) {
                for (const { 0: url, index } of text.matchAll(/https?:\/\/[^\s<>"]+/g)) {
                    target.append(text.slice(end, index));
                    const link = document.createElement("a");
                    setDescriptionUrl(link, "href", url);
                    link.textContent = url;
                    target.append(link);
                    end = index + url.length;
                }
            }
            target.append(text.slice(end));
        } else if (node instanceof HTMLElement && descriptionTags.has(node.localName)) {
            if (node instanceof HTMLInputElement && node.type !== "checkbox") {
                continue;
            }

            const element = document.createElement(node.localName);
            if (element instanceof HTMLAnchorElement) {
                setDescriptionUrl(element, "href", node.getAttribute("href"));
            } else if (element instanceof HTMLImageElement) {
                element.alt = node.getAttribute("alt") ?? "";
                element.referrerPolicy = "no-referrer";
                setDescriptionUrl(element, "src", node.getAttribute("src"));
            } else if (element instanceof HTMLInputElement) {
                element.type = "checkbox";
                element.defaultChecked = node.hasAttribute("checked");
            } else if (node.localName === "div" && node.hasAttribute("data-geojson-extra")) {
                element.setAttribute("data-geojson-extra", "");
            }

            for (const name of ["width", "height", "colspan", "rowspan"]) {
                const value = node.getAttribute(name);
                if (value && /^\d+$/.test(value)) {
                    element.setAttribute(name, value);
                }
            }
            if (node.hasAttribute("style")) {
                for (const property of descriptionStyleProperties) {
                    element.style.setProperty(property, node.style.getPropertyValue(property));
                }
            }
            appendDescription(element, node, linkify && !(element instanceof HTMLAnchorElement));
            target.append(element);
        }
    }
}

function setDescriptionUrl(element: HTMLElement, name: "href" | "src", value: string | null) {
    const url = value && URL.parse(value, document.baseURI);
    if (
        url &&
        (url.protocol === "https:" || url.protocol === "http:" ||
            (name === "href" && (url.protocol === "mailto:" || url.protocol === "tel:")))
    ) {
        element.setAttribute(name, value);
    }
}
