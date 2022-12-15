var time = document.getElementById('time_passed');

/**
 * Замеряет количество секунд и возвращает строку с количеством минут и секунд на русском языке
 * @param value - Количество секунд, которое необходимо преобразовать в строку.
 */
function time_passed(value) {
    let min_ = Math.floor(value / 60);
    let sec = (value - (min_ * 60)).toString()
    let min = min_.toString()

    let sec_str = ''
    let min_str = ''

    if (min_ !== 0) {  // Если есть минуты
        if (/1$/.test(min)) { min_str = ' минуту ' }
        if (/[2-4]$/.test(min)) { min_str = ' минуты '}
        if (/[05-9]$/.test(min)) { min_str = ' минут ' }
    } else { min = '' }

    if (/1$/.test(sec)) { sec_str = ' секунду ' }
    if (/[2-4]$/.test(sec)) { sec_str = ' секунды '}
    if (/[05-9]$/.test(sec)) { sec_str = ' секунд ' }

    return min+min_str+sec+sec_str
}
/**
 * Он берет текущее время, вычитает время последнего сообщения, а затем преобразует его в удобочитаемый формат.
 */
function count() {
    time.textContent = time_passed(Math.round(Date.now() / 1000 - last_time)) + 'назад';
    timer();
}
/**
 * Установите таймер для вызова функции подсчета через 1000 миллисекунд.
 */
function timer() {
    setTimeout(count, 1000);
}
timer();