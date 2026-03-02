/**
 * Fullscreen API helper for Livelist.
 *
 * Usage: call initFullscreenToggle(buttonId) after DOM is ready.
 * The button must be a <button> element; it will get an icon swap
 * between bi-arrows-fullscreen (normal) and bi-fullscreen-exit (fullscreen).
 */
function initFullscreenToggle(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    function isFullscreen() {
        return !!(document.fullscreenElement || document.webkitFullscreenElement);
    }

    function updateIcon() {
        // Swap Bootstrap Icons class
        btn.classList.toggle('bi-arrows-fullscreen', !isFullscreen());
        btn.classList.toggle('bi-fullscreen-exit', isFullscreen());
    }

    btn.addEventListener('click', function() {
        if (!isFullscreen()) {
            const el = document.documentElement;
            (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
        } else {
            (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        }
    });

    document.addEventListener('fullscreenchange', updateIcon);
    document.addEventListener('webkitfullscreenchange', updateIcon);

    // Set initial icon state
    updateIcon();
}
