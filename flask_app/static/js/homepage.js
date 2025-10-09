console.log("Homepage JS loaded");

document.addEventListener('DOMContentLoaded', function () {

	// Ensure page always reloads at the top instead of restoring previous scroll position.
	// Uses history.scrollRestoration when available, and falls back to scrollTo on pageshow.
	try {
		if ('scrollRestoration' in history) {
			history.scrollRestoration = 'manual';
		}
	} catch (e) {
	}

	// If the page is loaded from bfcache (pageshow.persisted), force scroll to top
	window.addEventListener('pageshow', function (ev) {
		if (ev.persisted) {
			window.scrollTo(0, 0);
		}
	});

	// Before the page unloads, try to set scroll to top so some browsers won't restore previous position
	window.addEventListener('beforeunload', function () {
		try { window.scrollTo(0, 0); } catch (e) { }
	});


	// animate the How It Works bridge heading if present
	try {
		const bridge = document.querySelector('.howitworks-bridge');
		if (bridge && window.gsap) {
			gsap.fromTo(bridge, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.9, ease: 'power2.out', delay: 0.25 });
		}
	} catch (e) {
		console.warn('Bridge animation failed', e);
	}

	// Slide-in on scroll for How It Works steps
	try {
		const steps = document.querySelectorAll('.how-step');
		if (steps && 'IntersectionObserver' in window) {
			// Use more aggressive options on small screens so animations trigger earlier
			const isSmall = window.matchMedia('(max-width: 640px)').matches;
			const obsOptions = isSmall ? { threshold: 0.15, rootMargin: '0px 0px -40% 0px' } : { threshold: 0.4, rootMargin: '0px 0px -10% 0px' };
			const obs = new IntersectionObserver((entries) => {
				entries.forEach(entry => {
					if (entry.isIntersecting) {
						entry.target.classList.add('in-view');
						obs.unobserve(entry.target);
					}
				});
			}, obsOptions);
			steps.forEach(s => obs.observe(s));
		}
	} catch (e) {
		console.warn('HowItWorks observer failed', e);
	}

	// Hide nav while scrolling down, show on scroll up
	(function () {
		const nav = document.querySelector('nav');
		if (!nav) return;
	let lastScroll = window.scrollY;
	let ticking = false;
	// Minimal threshold to avoid tiny micro-scroll jitter; effectively hides immediately
	const threshold = 1;

		function onTick() {
			const current = window.scrollY;
			if (Math.abs(current - lastScroll) < threshold) {
				ticking = false;
				return;
			}
			if (current > lastScroll) {
				// scrolling down: hide nav and remove visible background immediately
				nav.classList.add('nav-hidden');
				nav.classList.remove('nav-visible');
			} else {
				// scrolling up: show nav and add visible background
				nav.classList.remove('nav-hidden');
				// Only add background if we've scrolled away from the top
				if (current > 10) {
					nav.classList.add('nav-visible');
				} else {
					nav.classList.remove('nav-visible');
				}
			}
			lastScroll = current;
			ticking = false;
		}

		window.addEventListener('scroll', function () {
			if (!ticking) {
				window.requestAnimationFrame(onTick);
				ticking = true;
			}
		}, { passive: true });
	})();

	// Mobile menu is now handled by base.html template
	// Removed duplicate mobile menu JavaScript to prevent conflicts

	try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
});