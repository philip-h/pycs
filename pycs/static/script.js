// https://codepen.io/marcelo-ribeiro/pen/GRgmzNZ
const $navMenuButton = document.getElementById("navMenuButton");
const $navMenu = document.getElementById("navMenu");
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

// Search for teacher page
const $filterInput = document.querySelector('[data-script="filterStudents"]')

const filterStudents = () => {
  const filterValue = $filterInput.value.toLowerCase();
  console.log(filterValue);
  const $studentDivs = document.querySelectorAll('.ass-list__ass');

  $studentDivs.forEach(studentDiv => {
    const studentName = studentDiv.getAttribute('data-student-name').toLowerCase();

    if (studentName.includes(filterValue)) {
      studentDiv.classList.remove('hidden');
    } else {
      studentDiv.classList.add('hidden');
    }
  });
}

if ($filterInput)
  $filterInput.addEventListener('keyup', filterStudents);
