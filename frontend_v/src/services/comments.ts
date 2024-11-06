import {ref, Ref} from "vue";

import api from "@/services/api";
import {InterfaceComment} from "@/services/interfaces";
import {errorToast, successToast} from "@/services/my.toast.ts";
import errorFmt from "@/errorFmt.ts";


export type CommentAction = "add" | "update" | "delete";


export interface CommentControl {
    id: number;
    deviceName: string;
    text: string;
    user: string;
    action: "" | CommentAction;
    interface: string;
}


class CommentService {
    public dialogVisible: Ref<boolean> = ref(false);
    private registered = false;
    commentObject: Ref<CommentControl> = ref({
        id: 0,
        text: "",
        deviceName: "",
        user: "",
        action: "",
        interface: "",
    })

    /**
     * Регистрируем новое действие над комментариями.
     * Обновляем объект `commentObject`
     *
     * @param action Действие: ('add', 'update' или 'delete')
     * @param comment Объект комментария из БД ('id', 'text', 'username')
     * @param interfaceName Название интерфейса
     * @param deviceName Название устройства
     */
    registerCommentAction(action: CommentAction, comment: InterfaceComment|null, interfaceName: string, deviceName: string) {
        if (action === "add") {
            this.commentObject.value = {
                id: 0,
                text: '',
                user: '',
                deviceName: deviceName,
                action: action,
                interface: interfaceName,
            }
            this.dialogVisible.value = true;
            this.registered = true;

        } else if (comment && comment.id && (action === "update" || action === "delete")) {
            this.commentObject.value = {
                id: comment.id,
                text: comment.text,
                user: comment.user,
                deviceName: deviceName,
                action: action,
                interface: interfaceName,
            }
            this.dialogVisible.value = true;
            this.registered = true;

        } else {
            this.registered = false;
        }
    }

    /**
     * Подтверждаем действие над выбранным комментарием
     */
    async submitCommentAction() {
        if (!this.registered) return;

        let new_comment = this.commentObject.value.text
        let method: "post" | "patch" | "delete"
        let data: any
        let url: string = "/device/api/comments"

        // Добавляем новый комментарий
        if (this.commentObject.value.action === "add" && new_comment.length) {
            method = "post"
            data = {
                device: this.commentObject.value.deviceName,
                comment: new_comment,
                interface: this.commentObject.value.interface
            }
        } else if (this.commentObject.value.action === "update" && new_comment.length) {
            // Обновление комментария на порту
            url = "/device/api/comments/" + this.commentObject.value.id
            method = "patch"
            data = {comment: new_comment}
        } else {
            // Удаление комментария на порту
            url = "/device/api/comments/" + this.commentObject.value.id
            method = "delete"
            data = {}
        }

        try {
            await api[method](url, data);
            let message: string = method === "patch" ? "обновлен" : method === "post" ? "создан" : "удален"
            successToast("ОК", "Комментарий был " + message, 5000)
        } catch (error: any) {
            errorToast("Ошибка", errorFmt(error))
        }
        this.dialogVisible.value = false;
        this.registered = false;
    }

}

const commentService = new CommentService();
export default commentService;
