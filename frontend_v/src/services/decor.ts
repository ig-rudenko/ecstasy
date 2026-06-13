import { Ref, ref } from "vue";

export class DecorConfig {
    public _winterDecor: Ref<boolean> = ref(true);
    public _compactMenu: Ref<boolean> = ref(false);
    public _autoExpandLargeInterfaceInfo: Ref<boolean> = ref(false);

    constructor() {
        this.load();
    }

    private load() {
        const loadData = localStorage.getItem("decorConfig");
        if (loadData) {
            const parsedData = JSON.parse(loadData);
            this._winterDecor.value = Boolean(parsedData.winterDecor);
            this._compactMenu.value = Boolean(parsedData.compactMenu);
            this._autoExpandLargeInterfaceInfo.value = Boolean(parsedData.autoExpandLargeInterfaceInfo);
        }
    }

    private save() {
        const data = {
            winterDecor: this._winterDecor.value,
            compactMenu: this._compactMenu.value,
            autoExpandLargeInterfaceInfo: this._autoExpandLargeInterfaceInfo.value,
        };
        localStorage.setItem("decorConfig", JSON.stringify(data));
    }

    get winterDecor(): boolean {
        return this._winterDecor.value;
    }

    set winterDecor(val: boolean) {
        this._winterDecor.value = val;
        this.save();
    }

    get compactMenu(): boolean {
        return this._compactMenu.value;
    }

    set compactMenu(val: boolean) {
        this._compactMenu.value = val;
        this.save();
    }

    get autoExpandLargeInterfaceInfo(): boolean {
        return this._autoExpandLargeInterfaceInfo.value;
    }

    set autoExpandLargeInterfaceInfo(val: boolean) {
        this._autoExpandLargeInterfaceInfo.value = val;
        this.save();
    }
}

const decorConfig = new DecorConfig();
export default decorConfig;
