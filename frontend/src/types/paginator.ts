export default class Paginator {
    constructor(
        public count: number = 0,
        public page: number = 0,
        public rowsPerPage: number = 50
    ) {}

    public get pagesCount() {
        return Math.floor(this.count / this.rowsPerPage) + 1
    }
}