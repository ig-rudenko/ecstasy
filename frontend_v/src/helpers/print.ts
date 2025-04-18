/**
 * Вызывает окно печати для переданного идентификатора элемента
 * @param {String} elementID
 */
export default function printElementById(elementID: string) {
    const container = document.getElementById(elementID);
    if (!container) return;

    let prtHtml = container.innerHTML

    // Get all stylesheets HTML
    let stylesHtml = '';
    for (const node of [...document.querySelectorAll('link[rel="stylesheet"], style')]) {
        stylesHtml += node.outerHTML;
    }
    // Open the print window
    const WinPrint = window.open('', '', 'width=1200,height=900,toolbar=0,scrollbars=0,status=0');
    if (!WinPrint) return;

    WinPrint.document.write(`<!DOCTYPE html>
        <html lang="ru">
        <head>
          ${stylesHtml}
          <title></title>
        </head>
        <body>
          ${prtHtml}
        </body>
        </html>`
    );
    WinPrint.document.close();
    WinPrint.focus();
    WinPrint.print();
}