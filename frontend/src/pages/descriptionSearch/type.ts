import {newInterfaceCommentsList, InterfaceComment} from "../../types/comments";

class SearchMatch {
    constructor(
        public description: string,
        public device: string,
        public interfaceName: string,
        public savedTime: string,
        public comments: Array<InterfaceComment>
    ) {}
}

function newSearchMatchList(data: Array<any>): Array<SearchMatch> {
    let res: Array<SearchMatch> = []
    for (const line of data) {
        res.push(
            new SearchMatch(
                line.Description, line.Device, line.Interface, line.SavedTime,
                newInterfaceCommentsList(line.Comments)
            )
        )
    }
    return res
}

export {SearchMatch, newSearchMatchList}
