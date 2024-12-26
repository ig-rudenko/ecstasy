/**
 * Функция getFileEarmarkClass принимает имя файла в качестве входных данных и возвращает соответствующий класс значков
 * Bootstrap на основе расширения файла.
 * @param {string} file_name - Параметр `file_name` представляет собой строку, представляющую имя файла, включая его расширение.
 * @returns {string} Функция getFileEarmarkClass возвращает строку, представляющую имя класса CSS для данного имени файла.
 */
function getFileEarmarkClass(file_name: string): string {
  const parts = file_name.split(".")
  if (parts.length === 1){
    // Не указано расширение
    return "bi-file-earmark"
  }

  const extension = parts[parts.length - 1]

  // создаем объект с ключами - расширениями файлов и значениями - типами файлов
  let fileTypes: any = {
    zip: "bi-file-earmark-zip",
    rar: "bi-file-earmark-zip",
    "7z": "bi-file-earmark-zip",
    gz: "bi-file-earmark-zip",
    pdf: "bi-file-earmark-pdf",
    mp3: "bi-file-earmark-music",
    wav: "bi-file-earmark-music",
    ogg: "bi-file-earmark-music",
    mp4: "bi-file-earmark-play",
    avi: "bi-file-earmark-play",
    mkv: "bi-file-earmark-play",
  };

  const bootstrap_default_formats = [
      "aac", "ai", "cs", "css", "csv", "doc", "docx", "exe", "heic", "html", "java", "js", "json",
      "jsx", "key", "md", "mdx", "otf", "ppt", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh",
      "sql", "tiff", "tsx", "ttf", "txt", "woff", "xls", "xlsx", "xml", "yaml", "yml"
  ]

  if (bootstrap_default_formats.indexOf(extension) > -1){
    return "bi-filetype-"+extension
  }

  // возвращаем тип файла из объекта по ключу-расширению или "bi-file-earmark", если такого ключа нет.
  return fileTypes[extension] || "bi-file-earmark";

}

export default getFileEarmarkClass