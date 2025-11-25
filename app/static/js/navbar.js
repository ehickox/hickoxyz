/**
 * Navigation Component
 * Handles mobile menu toggle and scroll behavior
 */

document.addEventListener('DOMContentLoaded', initNavbar);

function initNavbar() {
  const toggle = document.getElementById('navToggle');
  const menu = document.getElementById('navMenu');
  
  if (!toggle || !menu) return;
  
  // Toggle mobile menu
  toggle.addEventListener('click', function() {
    toggle.classList.toggle('is-active');
    menu.classList.toggle('is-open');
    
    // Prevent body scroll when menu is open
    if (menu.classList.contains('is-open')) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  });
  
  // Close menu when clicking a link
  const navLinks = menu.querySelectorAll('.nav__link');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      toggle.classList.remove('is-active');
      menu.classList.remove('is-open');
      document.body.style.overflow = '';
    });
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', function(event) {
    if (menu.classList.contains('is-open') && 
        !menu.contains(event.target) && 
        !toggle.contains(event.target)) {
      toggle.classList.remove('is-active');
      menu.classList.remove('is-open');
      document.body.style.overflow = '';
    }
  });
  
  // Handle escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && menu.classList.contains('is-open')) {
      toggle.classList.remove('is-active');
      menu.classList.remove('is-open');
      document.body.style.overflow = '';
    }
  });
}
