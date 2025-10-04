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

	const hamburger = document.querySelector('.hamburger');
	const mobileMenu = document.getElementById('mobile-menu');

	if (!hamburger || !mobileMenu) return;

	// Ensure initial state is closed (helps if cache or prior state made it visible)
	try {
		mobileMenu.hidden = true;
		hamburger.setAttribute('aria-expanded', 'false');
	} catch (e) {
		console.warn('Failed to set initial menu state', e);
	}

	function openMenu() {
		mobileMenu.hidden = false;
		mobileMenu.classList.add('open');
		hamburger.setAttribute('aria-expanded', 'true');
		document.documentElement.style.overflow = 'hidden';
		lastFocused = document.activeElement;
		// focus first focusable element in the menu
		focusable[0] && focusable[0].focus();
		console.log('mobile menu opened');
	}

	function closeMenu() {
		mobileMenu.classList.remove('open');
		// after transition, set hidden to true to remove from accessibility tree
		const transitionDuration = 300; // must match CSS
		setTimeout(() => {
			mobileMenu.hidden = true;
		}, transitionDuration);
		hamburger.setAttribute('aria-expanded', 'false');
		document.documentElement.style.overflow = '';
		// restore focus
		if (lastFocused) lastFocused.focus();
		console.log('mobile menu closed');
	}

	hamburger.addEventListener('click', function (e) {
		const expanded = hamburger.getAttribute('aria-expanded') === 'true';
		if (expanded) closeMenu(); else openMenu();
		console.log('hamburger clicked — expanded? ', !expanded);
	});

	// Close when clicking outside the mobile menu
	document.addEventListener('click', function (e) {
		if (mobileMenu.hidden) return;
		if (hamburger.contains(e.target)) return;
		if (mobileMenu.contains(e.target)) return;
		closeMenu();
	});

	// Close on Escape
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape' && !mobileMenu.hidden) {
			closeMenu();
			hamburger.focus();
		}

		// Focus trap: keep focus within mobile menu when open
		if (e.key === 'Tab' && mobileMenu.classList.contains('open')) {
			if (focusable.length === 0) {
				e.preventDefault();
				return;
			}
			const currentIndex = focusable.indexOf(document.activeElement);
			if (e.shiftKey) {
				// shift + tab
				if (currentIndex === 0 || document.activeElement === mobileMenu) {
					focusable[focusable.length - 1].focus();
					e.preventDefault();
				}
			} else {
				if (currentIndex === focusable.length - 1) {
					focusable[0].focus();
					e.preventDefault();
				}
			}
		}
	});

	// Ensure links inside menu close it when clicked
	mobileMenu.addEventListener('click', function (e) {
		const target = e.target.closest('a, button');
		if (!target) return;
		closeMenu();
	});

	// Close menu if window is resized above mobile breakpoint
	const MOBILE_BREAKPOINT = 800;
	window.addEventListener('resize', function () {
		if (window.innerWidth > MOBILE_BREAKPOINT && !mobileMenu.hidden) {
			closeMenu();
		}
	});

	// Focusable elements inside the mobile menu for trapping
	let focusable = Array.from(mobileMenu.querySelectorAll('a, button, [tabindex]:not([tabindex="-1"])'));
	let lastFocused = null;

	// Recompute focusable elements if menu content changes
	const observer = new MutationObserver(() => {
		focusable = Array.from(mobileMenu.querySelectorAll('a, button, [tabindex]:not([tabindex="-1"])'));
	});
	observer.observe(mobileMenu, { childList: true, subtree: true });
	// End of mobile menu code
	try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
});