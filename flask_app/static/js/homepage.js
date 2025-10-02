console.log("Homepage JS loaded");

document.addEventListener('DOMContentLoaded', function () {
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
});