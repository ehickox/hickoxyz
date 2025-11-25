/**
 * Timeline Scroll Widget
 * Tracks scroll progress through career sections and updates the timeline accordingly
 */

(function() {
  'use strict';

  const timeline = document.querySelector('.timeline-scroll');
  if (!timeline) return;

  const progress = timeline.querySelector('.timeline-scroll__progress');
  const markers = timeline.querySelectorAll('.timeline-scroll__marker');
  const timelineParagraphs = document.querySelectorAll('[data-timeline-year]');
  
  if (timelineParagraphs.length === 0) return;

  // Map years to their marker elements
  const yearToMarker = {};
  markers.forEach(marker => {
    const year = marker.dataset.year;
    yearToMarker[year] = marker;
  });

  // Calculate positions for progress tracking
  function getTimelineRange() {
    const first = timelineParagraphs[0];
    const last = timelineParagraphs[timelineParagraphs.length - 1];
    
    const startY = first.getBoundingClientRect().top + window.scrollY - window.innerHeight * 0.3;
    const endY = last.getBoundingClientRect().bottom + window.scrollY - window.innerHeight * 0.5;
    
    return { startY, endY };
  }

  // Find which paragraph is currently in view
  function getCurrentYear() {
    const viewportCenter = window.scrollY + window.innerHeight * 0.4;
    let currentYear = null;
    let passedYears = [];

    timelineParagraphs.forEach(p => {
      const rect = p.getBoundingClientRect();
      const pTop = rect.top + window.scrollY;
      const pBottom = rect.bottom + window.scrollY;
      const year = p.dataset.timelineYear;

      if (viewportCenter >= pTop && viewportCenter <= pBottom) {
        currentYear = year;
      }
      
      if (viewportCenter > pTop) {
        if (!passedYears.includes(year)) {
          passedYears.push(year);
        }
      }
    });

    // If between paragraphs, use the last passed year
    if (!currentYear && passedYears.length > 0) {
      currentYear = passedYears[passedYears.length - 1];
    }

    return { currentYear, passedYears };
  }

  // Update timeline visibility based on scroll position
  function updateVisibility() {
    const firstParagraph = timelineParagraphs[0];
    const lastParagraph = timelineParagraphs[timelineParagraphs.length - 1];
    
    const firstRect = firstParagraph.getBoundingClientRect();
    const lastRect = lastParagraph.getBoundingClientRect();
    
    // Show timeline when first paragraph enters viewport
    const shouldShow = firstRect.top < window.innerHeight * 0.7 && lastRect.bottom > window.innerHeight * 0.3;
    
    timeline.classList.toggle('is-visible', shouldShow);
  }

  // Update progress bar and active markers
  function updateProgress() {
    const { startY, endY } = getTimelineRange();
    const scrollY = window.scrollY;
    
    // Calculate progress percentage for full-height line
    let progressPercent = 0;
    if (scrollY >= startY) {
      progressPercent = Math.min(100, ((scrollY - startY) / (endY - startY)) * 100);
    }
    
    progress.style.height = `${progressPercent}%`;

    // Update markers
    const { currentYear, passedYears } = getCurrentYear();
    
    markers.forEach(marker => {
      const year = marker.dataset.year;
      const isActive = year === currentYear;
      const isPassed = passedYears.includes(year) && !isActive;
      
      marker.classList.toggle('is-active', isActive);
      marker.classList.toggle('is-passed', isPassed);
    });
  }

  // Handle click on timeline markers
  function handleMarkerClick(e) {
    const marker = e.currentTarget;
    const year = marker.dataset.year;
    
    // Find the first paragraph with this year
    const targetParagraph = document.querySelector(`[data-timeline-year="${year}"]`);
    if (targetParagraph) {
      const targetY = targetParagraph.getBoundingClientRect().top + window.scrollY - window.innerHeight * 0.3;
      window.scrollTo({
        top: targetY,
        behavior: 'smooth'
      });
    }
  }

  // Add click handlers to markers
  markers.forEach(marker => {
    marker.addEventListener('click', handleMarkerClick);
  });

  // Throttle scroll handler for performance
  let ticking = false;
  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(() => {
        updateVisibility();
        updateProgress();
        ticking = false;
      });
      ticking = true;
    }
  }

  // Initialize
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  
  // Initial update
  updateVisibility();
  updateProgress();
})();
