/**
 * Gallery/Slideshow Component
 * Handles automatic slideshow with manual navigation and touch support
 */

let slideIndex = 0;
let slideTimeout = null;
let touchStartX = 0;
let touchEndX = 0;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initGallery);

function initGallery() {
  const slides = document.getElementsByClassName('gallery__slide');
  if (slides.length === 0) return;
  
  // Start automatic slideshow
  showSlidesAuto();
  
  // Add touch event listeners
  setupTouchEvents();
}

function plusSlides(n) {
  clearTimeout(slideTimeout);
  showSlides(slideIndex += n);
}

function currentSlide(n) {
  clearTimeout(slideTimeout);
  showSlides(slideIndex = n);
}

function showSlides(n) {
  const slides = document.getElementsByClassName('gallery__slide');
  const dots = document.getElementsByClassName('gallery__dot');
  
  if (slides.length === 0) return;
  
  // Wrap around
  if (n > slides.length) slideIndex = 1;
  if (n < 1) slideIndex = slides.length;
  
  // Hide all slides and remove active class
  for (let i = 0; i < slides.length; i++) {
    slides[i].classList.remove('is-active');
  }
  
  // Remove active from all dots
  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove('is-active');
  }
  
  // Show current slide and activate dot
  slides[slideIndex - 1].classList.add('is-active');
  if (dots.length > 0) {
    dots[slideIndex - 1].classList.add('is-active');
  }
  
  // Restart auto-advance timer
  startSlideTimeout();
}

function startSlideTimeout() {
  clearTimeout(slideTimeout);
  slideTimeout = setTimeout(function() {
    plusSlides(1);
  }, 5000); // 5 seconds between slides
}

function showSlidesAuto() {
  const slides = document.getElementsByClassName('gallery__slide');
  const dots = document.getElementsByClassName('gallery__dot');
  
  if (slides.length === 0) return;
  
  // Hide all slides
  for (let i = 0; i < slides.length; i++) {
    slides[i].classList.remove('is-active');
  }
  
  slideIndex++;
  if (slideIndex > slides.length) slideIndex = 1;
  
  // Remove active from all dots
  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove('is-active');
  }
  
  // Show current slide and activate dot
  slides[slideIndex - 1].classList.add('is-active');
  if (dots.length > 0) {
    dots[slideIndex - 1].classList.add('is-active');
  }
  
  // Start auto-advance timer
  startSlideTimeout();
}

function setupTouchEvents() {
  const images = document.querySelectorAll('.gallery__slide img');
  
  images.forEach(image => {
    image.addEventListener('touchstart', function(event) {
      touchStartX = event.touches[0].clientX;
    }, { passive: true });
    
    image.addEventListener('touchend', function(event) {
      touchEndX = event.changedTouches[0].clientX;
      handleSwipe();
    }, { passive: true });
  });
}

function handleSwipe() {
  const swipeThreshold = 50;
  const diff = touchStartX - touchEndX;
  
  if (Math.abs(diff) > swipeThreshold) {
    if (diff > 0) {
      plusSlides(1); // Swipe left - next slide
    } else {
      plusSlides(-1); // Swipe right - previous slide
    }
  }
}
