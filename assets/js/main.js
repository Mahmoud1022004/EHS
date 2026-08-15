/* EHS — Egyptian Hospital Supplies · shared site scripts */
(function () {
  'use strict';

  var header = document.querySelector('.header');
  var navToggle = document.querySelector('.nav-toggle');
  var body = document.body;
  var root = document.documentElement;

  /* Loading screen — "The Care Line".
     Plays once per browsing session (first page seen); repeat navigations and
     reduced-motion users skip it via the inline check in <head>. */
  var loader = document.getElementById('ehs-loader');
  if (loader) {
    if (root.classList.contains('loader-skip')) {
      loader.remove();
      root.classList.remove('loader-active');
    } else {
      try { sessionStorage.setItem('ehsSeenLoader', '1'); } catch (e) {}
      window.setTimeout(function () {
        loader.classList.add('is-done');
        root.classList.remove('loader-active');
        window.setTimeout(function () { loader.remove(); }, 600);
      }, 3050);
    }
  }

  /* Sticky header shadow */
  function onScroll() {
    if (!header) return;
    header.classList.toggle('is-scrolled', window.scrollY > 8);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Mobile navigation */
  var drawerMq = window.matchMedia('(max-width: 1120px)');
  if (navToggle) {
    navToggle.addEventListener('click', function () {
      var open = body.classList.toggle('nav-open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.querySelectorAll('.nav a').forEach(function (link) {
      link.addEventListener('click', function () {
        /* In the drawer, a parent item with a submenu expands instead of
           closing the menu; its toggle handler below handles the tap. */
        if (drawerMq.matches && link.parentElement.classList.contains('nav__item')) return;
        body.classList.remove('nav-open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    });
    document.querySelectorAll('.nav__item > a').forEach(function (parent) {
      parent.setAttribute('aria-expanded', 'false');
      parent.addEventListener('click', function (e) {
        if (!drawerMq.matches) return;
        e.preventDefault();
        var item = parent.parentElement;
        var open = item.classList.toggle('is-open');
        parent.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && body.classList.contains('nav-open')) {
        body.classList.remove('nav-open');
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.focus();
      }
    });
  }

  /* Reveal on scroll */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* Hero video: respect reduced motion, pause when off-screen */
  var heroVideo = document.querySelector('.hero__video');
  if (heroVideo) {
    var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (prefersReduced.matches) {
      heroVideo.removeAttribute('autoplay');
      heroVideo.pause();
    } else if ('IntersectionObserver' in window) {
      var vio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var p = heroVideo.play();
            if (p && p.catch) p.catch(function () {});
          } else {
            heroVideo.pause();
          }
        });
      }, { threshold: 0.1 });
      vio.observe(heroVideo);
    }
  }

  /* Bulk-order deep links: /professionals.html?product=X&interest=bulk#enquiry
     preselects the bulk option and prefills the product in the message. */
  var enquiryForm = document.querySelector('#enquiry form');
  if (enquiryForm) {
    var params = new URLSearchParams(window.location.search);
    var product = params.get('product');
    var interest = params.get('interest');
    if (interest === 'bulk') {
      var sel = enquiryForm.querySelector('select[name="interest"]');
      if (sel) { sel.value = 'bulk'; }
    }
    if (product) {
      var msg = enquiryForm.querySelector('textarea[name="message"]');
      var line = (enquiryForm.getAttribute('data-bulk-line') || 'Bulk order enquiry — product: ') + product;
      if (msg && !msg.value) { msg.value = line + '\n'; }
      var anchor = document.getElementById('enquiry');
      if (anchor) {
        window.setTimeout(function () {
          anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 350);
      }
    }
  }

  /* Enquiry / contact forms.
     The form is composed into a single structured WhatsApp message and handed
     to the visitor's own WhatsApp, where they press send — so enquiries arrive
     as readable chats with no form backend in between. Field names come from
     each input's own <label>, which keeps the message in the page's language.
     Native validation runs first: the submit event only fires once required
     fields are filled. */
  document.querySelectorAll('form[data-wa-form]').forEach(function (form) {
    var number = form.getAttribute('data-wa-form');
    if (!number) return;

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var lines = [];
      var heading = form.getAttribute('data-wa-heading');
      if (heading) { lines.push(heading, ''); }

      form.querySelectorAll('input[name], select[name], textarea[name]').forEach(function (field) {
        if (field.type === 'hidden' || field.disabled) return;
        var value;
        if (field.tagName === 'SELECT') {
          var opt = field.options[field.selectedIndex];
          value = opt ? opt.text : '';           /* the label, never the value code */
        } else if (field.type === 'checkbox' || field.type === 'radio') {
          if (!field.checked) return;
          value = field.value;
        } else {
          value = field.value;
        }
        value = (value || '').replace(/\s+$/, '').replace(/^\s+/, '');
        if (!value) return;
        var label = field.id ? form.querySelector('label[for="' + field.id + '"]') : null;
        var name = label ? label.textContent.trim() : field.name;
        lines.push(name + ': ' + value);
      });

      var source = form.getAttribute('data-wa-source');
      if (source) { lines.push('', source); }

      var text = lines.join('\n');
      /* wa.me carries the message in the URL, so keep it comfortably short */
      if (text.length > 1600) { text = text.slice(0, 1600) + '…'; }
      var url = 'https://wa.me/' + number + '?text=' + encodeURIComponent(text);

      window.open(url, '_blank', 'noopener');

      var success = form.querySelector('.form-success');
      if (success) {
        /* also offer the link directly, in case the pop-up was blocked */
        var manual = success.querySelector('[data-wa-manual]');
        if (manual) { manual.setAttribute('href', url); }
        success.classList.add('is-visible');
        success.setAttribute('role', 'status');
        success.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  });

  /* Count-up stats. Elements carry their final value as text (the no-JS
     fallback); data-count / data-count-years defines the animated target. */
  var countEls = document.querySelectorAll('[data-count], [data-count-years]');
  if (countEls.length) {
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var fmt = function (n) { return n.toLocaleString('en-US'); };
    var targetOf = function (el) {
      if (el.hasAttribute('data-count-years')) {
        return new Date().getFullYear() - parseInt(el.getAttribute('data-count-years'), 10);
      }
      return parseInt(el.getAttribute('data-count'), 10);
    };
    var runCount = function (el) {
      var target = targetOf(el);
      var suffix = el.getAttribute('data-suffix') || '';
      if (reducedMotion || !isFinite(target)) {
        el.textContent = fmt(target) + suffix;
        return;
      }
      if (el._raf) cancelAnimationFrame(el._raf);
      var dur = 1700;
      var t0 = null;
      var step = function (ts) {
        if (t0 === null) t0 = ts;
        var p = Math.min(1, (ts - t0) / dur);
        var eased = 1 - Math.pow(2, -10 * p);
        el.textContent = fmt(Math.round(target * eased)) + suffix;
        if (p < 1) { el._raf = requestAnimationFrame(step); } else { el.textContent = fmt(target) + suffix; el._raf = null; }
      };
      el._raf = requestAnimationFrame(step);
    };
    /* Counts replay every time the stats scroll back into view: start when
       ~40% visible, re-arm (and reset to 0 while off-screen) once fully out. */
    if ('IntersectionObserver' in window && !reducedMotion) {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var el = entry.target;
          if (entry.intersectionRatio >= 0.4) {
            if (!el._played) { el._played = true; runCount(el); }
          } else if (!entry.isIntersecting && el._played) {
            el._played = false;
            if (el._raf) { cancelAnimationFrame(el._raf); el._raf = null; }
            el.textContent = '0' + (el.getAttribute('data-suffix') || '');
          }
        });
      }, { threshold: [0, 0.4] });
      countEls.forEach(function (el) { cio.observe(el); });
    } else {
      countEls.forEach(runCount);
    }
  }

  /* Journey year scrub — a giant year counts through the milestones,
     captions crossfade, segment bars fill; loops once it scrolls into view. */
  document.querySelectorAll('[data-yearscrub]').forEach(function (scrub) {
    var stops = [];
    try { stops = JSON.parse(scrub.getAttribute('data-milestones') || '[]'); } catch (e) {}
    var yEl = scrub.querySelector('.yearscrub__year');
    var cEl = scrub.querySelector('.yearscrub__cap');
    var segs = scrub.querySelectorAll('.yearscrub__segs i');
    if (!stops.length || !yEl || !cEl) return;
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) {
      var last = stops[stops.length - 1];
      yEl.textContent = last[0];
      cEl.textContent = last[1];
      segs.forEach(function (s) { s.style.width = '100%'; });
      return;
    }
    var TWEEN = 900, HOLD = 1150, timer = null, raf = null;
    function setSeg(i, pct) { if (segs[i]) segs[i].style.width = pct + '%'; }
    function play() {
      if (timer) clearTimeout(timer);
      if (raf) cancelAnimationFrame(raf);
      segs.forEach(function (s) { s.style.width = '0%'; });
      var idx = 0;
      yEl.textContent = stops[0][0];
      cEl.textContent = stops[0][1];
      cEl.style.opacity = 1;
      setSeg(0, 100);
      function next() {
        idx += 1;
        if (idx >= stops.length) { timer = setTimeout(play, 2400); return; }
        var from = parseInt(stops[idx - 1][0], 10);
        var to = parseInt(stops[idx][0], 10);
        var t0 = null;
        cEl.style.opacity = 0;
        function step(ts) {
          if (t0 === null) t0 = ts;
          var p = Math.min(1, (ts - t0) / TWEEN);
          var e = 1 - Math.pow(1 - p, 3);
          yEl.textContent = Math.round(from + (to - from) * e);
          setSeg(idx, Math.round(p * 100));
          if (p < 1) { raf = requestAnimationFrame(step); }
          else {
            cEl.textContent = stops[idx][1];
            cEl.style.opacity = 1;
            timer = setTimeout(next, HOLD);
          }
        }
        raf = requestAnimationFrame(step);
      }
      timer = setTimeout(next, HOLD);
    }
    if ('IntersectionObserver' in window) {
      var started = false;
      var sio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !started) { started = true; play(); sio.unobserve(scrub); }
        });
      }, { threshold: 0.35 });
      sio.observe(scrub);
    } else {
      play();
    }
  });

  /* Curtain / blinds page transition on menu navigation. */
  var curtain = document.getElementById('ehs-curtain');
  if (curtain && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    if (root.classList.contains('curtain-in')) {
      try { sessionStorage.removeItem('ehsCurtain'); } catch (e) {}
      curtain.classList.add('is-opening');
      window.setTimeout(function () {
        curtain.classList.remove('is-opening');
        root.classList.remove('curtain-in');
      }, 800);
    }

    document.querySelectorAll('.nav a, .lang-switch, .nav-cta').forEach(function (link) {
      link.addEventListener('click', function (e) {
        var href = link.getAttribute('href');
        if (!href || href.charAt(0) === '#' || link.target === '_blank') return;
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
        /* parent items in the mobile drawer only expand — handled elsewhere */
        if (drawerMq.matches && link.parentElement.classList.contains('nav__item')) return;
        /* an anchor on the page we are already on just scrolls — running the
           curtain would cover the screen with nothing to navigate to */
        var samePage = false;
        try {
          var target = new URL(href, window.location.href);
          samePage = !!target.hash && target.pathname === window.location.pathname;
        } catch (err) {}
        if (samePage) {
          body.classList.remove('nav-open');
          if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
          return;
        }
        e.preventDefault();
        try { sessionStorage.setItem('ehsCurtain', '1'); } catch (err) {}
        curtain.classList.add('is-closing');
        window.setTimeout(function () { window.location.href = href; }, 560);
      });
    });
  }

  /* Hero reveal — the landing-page hero is pinned while the page scrolls up
     over it; it eases back slightly as it gets covered. */
  var heroSection = document.querySelector('.hero');
  var pageFlow = document.querySelector('.page-flow');
  var heroPanel = heroSection && heroSection.querySelector('.hero__panel');
  if (heroSection && pageFlow && heroPanel &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    body.classList.add('has-hero-reveal');
    /* Height is cached so the scroll handler only writes styles — no rAF
       gate, which can stick permanently if the page loads in a background
       tab where animation frames never run. */
    var heroH = heroSection.offsetHeight || 1;
    var heroUpdate = function () {
      var p = Math.max(0, Math.min(1, window.scrollY / heroH));
      heroPanel.style.transform = 'scale(' + (1 - p * 0.06).toFixed(4) + ')';
      heroPanel.style.opacity = (1 - p * 0.55).toFixed(3);
    };
    var heroMeasure = function () {
      heroH = heroSection.offsetHeight || 1;
      heroUpdate();
    };
    window.addEventListener('scroll', heroUpdate, { passive: true });
    window.addEventListener('resize', heroMeasure);
    window.addEventListener('load', heroMeasure);
    heroUpdate();
  }

  /* Footer reveal — optional; the footer is fixed behind the page and is
     uncovered by scroll, fading from transparent to opaque as it appears. */
  var revealFooter = document.querySelector('.footer[data-footer-reveal]');
  var mainEl = document.getElementById('main');
  if (revealFooter && mainEl) {
    var footerH = 0;
    var enabled = false;

    var measure = function () {
      /* The fixed footer must fit the viewport, otherwise its lower part
         could never be reached. Taller footers (phones) keep the normal
         stacked layout. */
      body.classList.remove('has-footer-reveal');
      mainEl.style.marginBottom = '';
      footerH = revealFooter.offsetHeight;
      enabled = footerH > 0 && footerH <= window.innerHeight - 8;
      if (enabled) {
        body.classList.add('has-footer-reveal');
        mainEl.style.marginBottom = footerH + 'px';
      } else {
        revealFooter.style.opacity = '';
      }
      update();
    };

    var update = function () {
      if (!enabled) return;
      var docH = document.documentElement.scrollHeight;
      var seen = window.scrollY + window.innerHeight - (docH - footerH);
      var p = Math.max(0, Math.min(1, seen / footerH));
      /* ease out so the footer becomes readable early in the reveal */
      revealFooter.style.opacity = Math.pow(p, 0.6).toFixed(3);
    };

    window.addEventListener('scroll', update, { passive: true });

    var resizeTimer;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(measure, 150);
    });
    window.addEventListener('load', measure);
    measure();
  }

  /* Footer year */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
