import {getProtectedImage} from "@/helpers/images.ts";

class MediaFile {
    public file: File
    public description: string
    public imageSrc: string | null
    public errors: Array<string>

    constructor(
        file: File,
    ) {
        this.file = file
        this.description = ""
        this.imageSrc = null
        if (this.isImage) {
          // Создать URL-адрес объекта для предварительного просмотра изображения
          this.imageSrc = URL.createObjectURL(file);
        }
        this.errors = []
    }

    public get isImage(): boolean {
        return this.file.type.startsWith("image/");
    }
}


class MediaFileInfo {
    constructor(
        public description: string,
        public fileType: string,
        public id: number,
        public isImage: boolean,
        public modTime: string,
        public name: string,
        public url: string,
    ) {}
}


function newMediaFileInfo(data: any): MediaFileInfo {
    return new MediaFileInfo(
        data.description,
        data.file_type,
        data.id,
        data.is_image,
        data.mod_time,
        data.name,
        data.url,
    )
}


async function newMediaFileInfoList(data: Array<any>): Promise<MediaFileInfo[]> {
    let res: Array<MediaFileInfo> = []
    for (const datum of data) {
        if (datum.is_image) datum.url = await getProtectedImage(datum.url)
        res.push(new MediaFileInfo(
            datum.description,
            datum.file_type,
            datum.id,
            datum.is_image,
            datum.mod_time,
            datum.name,
            datum.url,
        ))
    }
    return res
}

export {MediaFile, MediaFileInfo, newMediaFileInfoList, newMediaFileInfo}
