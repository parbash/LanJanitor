/**
 * LanJanitor utils.js
 * -------------------
 * Utility functions for frontend helpers.
 */

/**
 * Get CSRF token from meta tag.
 * @returns {string} CSRF token
 */
function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}
