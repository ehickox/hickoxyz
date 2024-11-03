let slideIndex = 0;
let slideTimeout; // Variable to store the timeout
let touchStartX = 0;
let touchEndX = 0;

showSlidesAuto();

function plusSlides(n) {
  clearTimeout(slideTimeout); // Clear existing timeout
  showSlides(slideIndex += n);
}

function currentSlide(n) {
  clearTimeout(slideTimeout); // Clear existing timeout
  showSlides(slideIndex = n);
}

function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  if (n > slides.length) {slideIndex = 1}    
  if (n < 1) {slideIndex = slides.length}
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
  startSlideTimeout(); // Start the timeout again after slide change
}

function startSlideTimeout() {
  clearTimeout(slideTimeout); // Clear existing timeout
  slideTimeout = setTimeout(function() {
    plusSlides(1); // Move to the next slide after the timeout
  }, 4000); // Change image every 4 seconds
}

function showSlidesAuto() {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  if (slides.length == 0) {
    return;
  }
  let dots = document.getElementsByClassName("dot");
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  slideIndex++;
  if (slideIndex > slides.length) {slideIndex = 1}
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
  startSlideTimeout(); // Start the initial timeout
}

// Touch event handlers for swiping on images
let images = document.querySelectorAll(".mySlides img");

images.forEach(image => {
  image.addEventListener('touchstart', function(event) {
    touchStartX = event.touches[0].clientX;
  }, false);

  image.addEventListener('touchend', function(event) {
    touchEndX = event.changedTouches[0].clientX;
    handleSwipe();
  }, false);
});

function handleSwipe() {
  if (touchStartX - touchEndX > 50) {
    plusSlides(1); // Swipe left, move to the next slide
  } else if (touchEndX - touchStartX > 50) {
    plusSlides(-1); // Swipe right, move to the previous slide
  }
}

