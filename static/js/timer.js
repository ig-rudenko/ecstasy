var time = document.getElementById('time_passed');

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
function count() {
    time.textContent = time_passed(Math.round(Date.now() / 1000 - last_time)) + 'назад';
    timer();
}
function timer() {
    setTimeout(count, 1000);
}
timer();