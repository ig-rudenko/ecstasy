let mybutton = document.getElementById("btn-back-to-top");

/**
 * Если пользователь прокручивает документ на 100 пикселей вниз, показывает кнопку.
 * В противном случае скрывает
 */
window.onscroll = function () {
  if (
    document.body.scrollTop > 100 ||
    document.documentElement.scrollTop > 100
  ) {
    mybutton.style.display = "block";
  } else {
    mybutton.style.display = "none";
  }
};

/* При нажатии кнопки вызывается функция страница прокручивается вверх. */
mybutton.addEventListener("click", function () {
  document.body.scrollTop = 0;
  document.documentElement.scrollTop = 0;
});