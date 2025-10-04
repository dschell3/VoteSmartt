// Animated background blobs using GSAP (replacement for React+framer-motion)
// This script injects blobs into #animated-bg and animates them with looping motion.

(function () {
  const blobs = [
    { color: 'rgba(59,130,246,0.2)', size: 384, x: null, y: 80, right: 40, duration: 8, delay: 0 },
    { color: 'rgba(20,184,166,0.25)', size: 320, x: 64, y: null, bottom: 128, duration: 10, delay: 1 },
    { color: 'rgba(16,185,129,0.2)', size: 288, xPercent: 25, yPercent: 33, duration: 12, delay: 2 },
    { color: 'rgba(6,182,212,0.15)', size: 256, xPercentRight: 25, yPercentBottom: 20, duration: 9, delay: 1.5 },
    { color: 'rgba(37,99,235,0.18)', size: 224, xPercentRight: 12, yPercent: 50, duration: 11, delay: 0.5 },
    { color: 'rgba(20,184,166,0.22)', size: 352, xPercent: 33, y: 160, duration: 13, delay: 2.5 },
    { color: 'rgba(34,197,94,0.15)', size: 256, xPercent: 50, yPercentBottom: 25, duration: 10, delay: 1.8 },
    { color: 'rgba(6,182,212,0.2)', size: 288, xPercentRight: 33, yPercent: 25, duration: 14, delay: 0.8 },
  ];

  function createBlob(opts) {
    const el = document.createElement('div');
    el.className = 'animated-blob';
    el.style.width = opts.size + 'px';
    el.style.height = opts.size + 'px';
    el.style.background = opts.color;
    // initial positioning
    if (opts.x !== undefined && opts.x !== null) el.style.left = opts.x + 'px';
    if (opts.y !== undefined && opts.y !== null) el.style.top = opts.y + 'px';
    if (opts.right !== undefined && opts.right !== null) el.style.right = opts.right + 'px';
    if (opts.bottom !== undefined && opts.bottom !== null) el.style.bottom = opts.bottom + 'px';
    if (opts.xPercent !== undefined) el.style.left = opts.xPercent + '%';
    if (opts.yPercent !== undefined) el.style.top = opts.yPercent + '%';
    if (opts.xPercentRight !== undefined) el.style.right = opts.xPercentRight + '%';
    if (opts.yPercentBottom !== undefined) el.style.bottom = opts.yPercentBottom + '%';

    return el;
  }

  function init() {
    const container = document.getElementById('animated-bg');
    if (!container) return;

    // create blobs
    blobs.forEach((b, i) => {
      const el = createBlob(b);
      container.appendChild(el);

      // animate with GSAP
      const tl = gsap.timeline({ repeat: -1, yoyo: true, delay: b.delay });
      tl.to(el, { y: -30, x: 20, rotation: 10, scale: 1.05, duration: b.duration / 2, ease: 'sine.inOut' });
      tl.to(el, { y: 0, x: 0, rotation: -6, scale: 0.95, duration: b.duration / 2, ease: 'sine.inOut' });
    });

    // ensure the blobs sit under the nav: nav has z-index 50, hero inner has z-10
    container.style.zIndex = '0';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
