class InterfaceComment {
        constructor(
        public id: number,
        public user: string,
        public text: string,
        public createdTime: string,
    ) {}
}


function newInterfaceCommentsList(commentsData: Array<any>): Array<InterfaceComment> {
    let res: Array<InterfaceComment> = []
    for (const comment of commentsData) {
        res.push(
            new InterfaceComment(comment.id, comment.user, comment.text, comment.createdTime)
        )
    }
    return res
}


export default InterfaceComment
export {newInterfaceCommentsList, InterfaceComment}
