// Custom JavaScript for the MIKROBOT website

// This script handles the mobile navigation toggle.
document.addEventListener('DOMContentLoaded', function() {
  const toggler = document.querySelector('.navbar-toggler');
  const nav = document.getElementById('navbarNav');
  if (toggler && nav) {
    toggler.addEventListener('click', function() {
      nav.classList.toggle('show');
    });
  }

  // Prosty pokaz slajdów dla kart osiągnięć i publikacji. Każdy element
  // posiada klasę .slideshow-img oraz atrybut data-images zawierający
  // nazwy plików oddzielone przecinkami. Skrypt zmienia atrybut src co 5
  // sekund, jeśli w danej karcie znajduje się więcej niż jeden obraz.
  const slides = document.querySelectorAll('.slideshow-img');
  slides.forEach(function(img) {
    const data = img.getAttribute('data-images');
    if (!data) return;
    const files = data.split(',').map(function(s) { return s.trim(); });
    if (files.length > 1) {
      let index = 0;
      setInterval(function() {
        // Dodaj klasę fade-out, aby rozpocząć zanikanie
        img.classList.add('fade-out');
        // Po krótkim czasie (0.5 s) zmień obraz na następny i usuń efekt zanikania
        setTimeout(function() {
          index = (index + 1) % files.length;
          img.src = '/static/' + files[index];
          img.classList.remove('fade-out');
        }, 500);
      }, 5000);
    }
  });
});