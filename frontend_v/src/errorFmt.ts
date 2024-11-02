import {AxiosError} from "axios";

function getVerboseAxiosError(error: AxiosError<any>): string {
    if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        const request_id = error.response.headers["x-api-request-id"]

        if (typeof detail[0] === "string") return detail + "\nRequest ID: " + request_id;
        if (typeof detail[0] === "object") {
            let validationErrors = ""
            for (const detailElement of detail) {
                validationErrors += detailElement.loc[1].toString() + ": " + detailElement.msg.toString() + "<br>"
            }
            return validationErrors + "\nRequest ID: " + request_id
        }

    }
    return error.message
}


export default getVerboseAxiosError
