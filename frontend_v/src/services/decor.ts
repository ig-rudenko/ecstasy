import {Ref, ref} from "vue";

export class DecorConfig {
    public _winterDecor: Ref<boolean> = ref(true);

    constructor() {
        this.load()
    }

    private load() {
        const loadData = localStorage.getItem("decorConfig")
        if (loadData) {
            const parsedData = JSON.parse(loadData)
            this._winterDecor.value = Boolean(parsedData.winterDecor);
        }
    }

    private save() {
        const data = {
            winterDecor: this._winterDecor.value,
        }
        localStorage.setItem("decorConfig", JSON.stringify(data))
    }

    get winterDecor(): boolean {
        return this._winterDecor.value;
    }

    set winterDecor(val: boolean) {
        this._winterDecor.value = val;
        this.save();
    }

}

const decorConfig = new DecorConfig();
export default decorConfig;
