// https://codepen.io/marcelo-ribeiro/pen/GRgmzNZ
let $navMenuButton = document.getElementById("navMenuButton");
let $navMenu = document.getElementById("navMenu");
const toggle = event => {
  event.stopPropagation();
  if (!event.target.closest("#navMenu")) {
    $navMenu.classList.toggle("nav__menu--visible");
    $navMenu.classList.contains("nav__menu--visible")
      ? document.addEventListener("click", toggle)
      : document.removeEventListener("click", toggle);
  }
}
if ($navMenuButton)
  $navMenuButton.addEventListener("click", toggle);
