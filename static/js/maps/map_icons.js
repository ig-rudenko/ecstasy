/* Словарь иконок SVG. */
const MAP_ICONS = {
    "circle-fill": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" class="bi bi-circle-fill" viewBox="0 0 16 16">
          <circle cx="8" cy="8" r="7" stroke="{2}" />
        </svg>`,
    "triangle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" class="bi bi-triangle-fill" viewBox="0 0 16 17">
          <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{2}" />
        </svg>`,
    "record-circle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" class="bi bi-record-circle" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
          <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" stroke="{2}" />
        </svg>`,
    "wrench-circle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" class="bi bi-wrench-adjustable-circle" viewBox="0 0 16 16">
          <path d="M12.496 8a4.491 4.491 0 0 1-1.703 3.526L9.497 8.5l2.959-1.11c.027.2.04.403.04.61Z"/>
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1 0a7 7 0 1 0-13.202 3.249l1.988-1.657a4.5 4.5 0 0 1 7.537-4.623L7.497 6.5l1 2.5 1.333 3.11c-.56.251-1.18.39-1.833.39a4.49 4.49 0 0 1-1.592-.29L4.747 14.2A7 7 0 0 0 15 8Zm-8.295.139a.25.25 0 0 0-.288-.376l-1.5.5.159.474.808-.27-.595.894a.25.25 0 0 0 .287.376l.808-.27-.595.894a.25.25 0 0 0 .287.376l1.5-.5-.159-.474-.808.27.596-.894a.25.25 0 0 0-.288-.376l-.808.27.596-.894Z"/>
        </svg>`,
    "diamond": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" class="bi bi-diamond-fill" viewBox="-1 -1 18 18">
          <path fill-rule="evenodd" d="M6.95.435c.58-.58 1.52-.58 2.1 0l6.515 6.516c.58.58.58 1.519 0 2.098L9.05 15.565c-.58.58-1.519.58-2.098 0L.435 9.05a1.482 1.482 0 0 1 0-2.098L6.95.435z" stroke="{2}" />
        </svg>`,
    "circle-in-triangle": `<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{0}" fill="{1}" class="bi bi-diamond-fill" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
          <circle cx="8" cy="10" r="4" stroke="{2}" />
        </svg>`,
}