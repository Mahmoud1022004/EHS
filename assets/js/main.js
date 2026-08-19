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
      }, 2350);   /* the shine lands at ~2.1s — hold briefly, then lift */
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


  /* Homepage certifications toggle. Opens the certificates in place rather than
     sending the visitor to the About page and losing their position — pressing
     it again closes them.

     [hidden] is display:none, which no transition can animate away from, so the
     attribute is cleared one frame before the open class lands and only restored
     once the closing transition has finished. The cards inside carry .reveal and
     were never scrolled past while hidden, so their observer never fired; mark
     them visible on first open or they would expand into empty space. */
  var certsToggle = document.querySelector('[data-certs-toggle]');
  var certsPanel = document.querySelector('[data-certs-panel]');
  if (certsToggle && certsPanel) {
    var certsLabel = certsToggle.querySelector('[data-certs-label]');
    var labelClosed = certsLabel ? certsLabel.textContent : '';
    var labelOpen = certsLabel ? (certsLabel.getAttribute('data-label-open') || labelClosed) : '';
    var certsBusy = false;

    certsToggle.addEventListener('click', function () {
      if (certsBusy) { return; }
      var opening = certsToggle.getAttribute('aria-expanded') !== 'true';
      certsToggle.setAttribute('aria-expanded', opening ? 'true' : 'false');
      if (certsLabel) { certsLabel.textContent = opening ? labelOpen : labelClosed; }

      if (opening) {
        certsPanel.hidden = false;
        certsPanel.querySelectorAll('.reveal').forEach(function (el) {
          el.classList.add('is-visible');
        });
        /* two frames: one for [hidden] to clear, one for the start height to stick */
        requestAnimationFrame(function () {
          requestAnimationFrame(function () { certsPanel.classList.add('is-open'); });
        });
      } else {
        certsBusy = true;
        certsPanel.classList.remove('is-open');
        var done = function () {
          certsPanel.hidden = true;
          certsBusy = false;
          certsPanel.removeEventListener('transitionend', done);
        };
        certsPanel.addEventListener('transitionend', done);
        /* transitionend never fires under reduced motion, so close regardless */
        window.setTimeout(function () { if (certsBusy) { done(); } }, 700);
      }
    });
  }

  /* Hero video: play it wherever the browser will allow it, pause off-screen.

     This used to pause outright under prefers-reduced-motion, and because that
     was an else-if the observer was never attached either — so on a phone with
     Reduce Motion enabled the video could not start, then or later. The clip is
     muted, slow and ambient rather than the flashing or parallax that setting
     exists to suppress, so it now plays and only the page transitions honour it.

     Autoplay is refused outright in iOS Low Power Mode and Android battery
     saver; no script can override that. A user gesture does lift the block, so
     retry once on the first tap. Until then the panel shows the poster. */
  var heroVideo = document.querySelector('.hero__video');
  if (heroVideo) {
    var playHero = function () {
      var p = heroVideo.play();
      if (p && p.catch) p.catch(function () {});
    };
    if ('IntersectionObserver' in window) {
      var vio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) { playHero(); } else { heroVideo.pause(); }
        });
      }, { threshold: 0.1 });
      vio.observe(heroVideo);
    } else {
      playHero();
    }
    var gestures = ['touchstart', 'pointerdown', 'keydown'];
    var resumeHero = function () {
      if (heroVideo.paused) { playHero(); }
      gestures.forEach(function (ev) { window.removeEventListener(ev, resumeHero); });
    };
    gestures.forEach(function (ev) {
      window.addEventListener(ev, resumeHero, { passive: true });
    });
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

    /* WhatsApp and email carry the same answers; only the transport differs,
       so the message is built once here and handed to whichever the visitor
       picked. */
    function compose() {
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
      /* both wa.me and mailto: carry the message in the URL, so keep it short */
      if (text.length > 1600) { text = text.slice(0, 1600) + '…'; }
      return text;
    }

    /* Show the confirmation for the channel used, and point its fallback link
       at the same URL in case the hand-off was blocked. */
    function confirm(channel, url) {
      var success = form.querySelector('.form-success');
      if (!success) return;
      success.querySelectorAll('[data-success]').forEach(function (variant) {
        variant.hidden = variant.getAttribute('data-success') !== channel;
      });
      var manual = success.querySelector('[data-' + channel + '-manual]');
      if (manual) { manual.setAttribute('href', url); }
      success.classList.add('is-visible');
      success.setAttribute('role', 'status');
      success.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var url = 'https://wa.me/' + number + '?text=' + encodeURIComponent(compose());
      window.open(url, '_blank', 'noopener');
      confirm('wa', url);
    });

    var mailBtn = form.querySelector('[data-mail-send]');
    var mailTo = form.getAttribute('data-mail-to');
    if (mailBtn && mailTo) {
      mailBtn.addEventListener('click', function () {
        /* type="button" skips the browser's own required-field check, so ask
           for it here rather than composing a half-empty enquiry */
        if (typeof form.reportValidity === 'function' && !form.reportValidity()) return;
        var url = 'mailto:' + mailTo
                + '?subject=' + encodeURIComponent(form.getAttribute('data-mail-subject') || '')
                + '&body=' + encodeURIComponent(compose());
        confirm('mail', url);
        window.location.href = url;
      });
    }
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

  /* Picture carousels.
     Any .gallery marked data-carousel is upgraded from a plain grid into a
     carousel: the incoming photo wipes across the outgoing one, the same
     motion as the page-transition curtain. Photos are shown whole rather
     than cropped. If this script never runs the gallery stays a grid, so
     every picture is still reachable. */
  var CAROUSEL_ARROW =
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
    '<path d="M5 12h14m-6-7 7 7-7 7" stroke="currentColor" stroke-width="2.2" ' +
    'stroke-linecap="round" stroke-linejoin="round"/></svg>';

  document.querySelectorAll('.gallery[data-carousel]').forEach(function (gallery) {
    var figures = [].slice.call(gallery.children).filter(function (el) {
      return el.tagName === 'FIGURE';
    });
    if (figures.length < 2) return;

    var labels = {
      prev: gallery.getAttribute('data-prev') || 'Previous picture',
      next: gallery.getAttribute('data-next') || 'Next picture',
      of: gallery.getAttribute('data-of') || 'Picture'
    };

    gallery.classList.add('is-carousel');
    gallery.removeAttribute('style');           /* drop the grid-columns override */

    var carousel = document.createElement('div');
    carousel.className = 'carousel';
    var stage = document.createElement('div');
    stage.className = 'carousel__stage';
    figures.forEach(function (fig, i) {
      if (i === 0) fig.classList.add('is-on');
      stage.appendChild(fig);
    });
    carousel.appendChild(stage);

    var prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = 'carousel__nav carousel__nav--prev';
    prevBtn.setAttribute('aria-label', labels.prev);
    prevBtn.innerHTML = CAROUSEL_ARROW;

    var nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = 'carousel__nav carousel__nav--next';
    nextBtn.setAttribute('aria-label', labels.next);
    nextBtn.innerHTML = CAROUSEL_ARROW;

    var count = document.createElement('span');
    count.className = 'carousel__count';
    count.textContent = '1 / ' + figures.length;

    var dots = document.createElement('div');
    dots.className = 'carousel__dots';
    figures.forEach(function (fig, i) {
      var dot = document.createElement('button');
      dot.type = 'button';
      dot.className = 'carousel__dot' + (i ? '' : ' is-on');
      dot.setAttribute('aria-label', labels.of + ' ' + (i + 1));
      dot.addEventListener('click', function () { go(i, i > current ? 'next' : 'prev'); });
      dots.appendChild(dot);
    });

    carousel.appendChild(count);
    carousel.appendChild(prevBtn);
    carousel.appendChild(nextBtn);
    carousel.appendChild(dots);
    gallery.appendChild(carousel);

    var current = 0;
    var moving = false;

    function go(target, dir) {
      if (moving) return;
      target = (target + figures.length) % figures.length;
      if (target === current) return;
      moving = true;

      var outgoing = figures[current];
      var incoming = figures[target];

      /* set the wipe direction, then force the browser to apply the new
         start position before the transition to it begins */
      carousel.setAttribute('data-dir', dir);
      outgoing.classList.remove('is-on');
      incoming.classList.remove('is-on', 'is-back');
      void incoming.offsetWidth;

      outgoing.classList.add('is-back');
      incoming.classList.add('is-on');
      window.setTimeout(function () { outgoing.classList.remove('is-back'); }, 700);

      dots.children[current].classList.remove('is-on');
      dots.children[target].classList.add('is-on');
      current = target;
      count.textContent = (current + 1) + ' / ' + figures.length;
      window.setTimeout(function () { moving = false; }, 280);
    }

    nextBtn.addEventListener('click', function () { go(current + 1, 'next'); });
    prevBtn.addEventListener('click', function () { go(current - 1, 'prev'); });

    var touchX = null;
    carousel.addEventListener('touchstart', function (e) {
      touchX = e.touches[0].clientX;
    }, { passive: true });
    carousel.addEventListener('touchend', function (e) {
      if (touchX === null) return;
      var dx = e.changedTouches[0].clientX - touchX;
      if (Math.abs(dx) > 40) { go(current + (dx < 0 ? 1 : -1), dx < 0 ? 'next' : 'prev'); }
      touchX = null;
    }, { passive: true });
  });

  /* Floating contact button — one button that opens the channel list.
     Only present once social profiles are configured; otherwise the button
     is a plain WhatsApp link and needs no script. */
  var fab = document.getElementById('ehs-fab');
  if (fab) {
    var fabToggle = fab.querySelector('.fab__toggle');
    var setFab = function (open) {
      fab.classList.toggle('is-open', open);
      fabToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    fabToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      setFab(!fab.classList.contains('is-open'));
    });
    document.addEventListener('click', function (e) {
      if (!fab.contains(e.target)) setFab(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setFab(false);
    });
    /* choosing a channel closes it behind you */
    fab.querySelectorAll('.fab__item').forEach(function (a) {
      a.addEventListener('click', function () { setFab(false); });
    });
  }

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

    /* Back/forward cache. The browser freezes this page exactly as it looks
       the moment we navigate away — which is mid-transition, blinds fully
       closed. Restoring it hands the visitor a green screen, and because a
       bfcache restore re-runs no script, nothing clears it: Back appears to
       need two presses. pageshow is the only event that fires on a restore. */
    window.addEventListener('pageshow', function (e) {
      if (!e.persisted) return;
      curtain.classList.remove('is-closing');
      curtain.classList.remove('is-opening');
      root.classList.remove('curtain-in');
      /* a cancelled or restored navigation must not leave the flag behind,
         or the next ordinary load opens with a curtain it never closed */
      try { sessionStorage.removeItem('ehsCurtain'); } catch (err) {}
    });

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

  /* Office / factory tabs. Progressive enhancement: without JS both panes are
     just stacked content, so the addresses are never hidden behind a script. */
  Array.prototype.forEach.call(document.querySelectorAll('[data-loctabs]'), function (box) {
    var tabs = [].slice.call(box.querySelectorAll('.loctabs__tab'));
    var panes = [].slice.call(box.querySelectorAll('.loctabs__pane'));
    if (tabs.length !== panes.length) return;

    function select(i) {
      tabs.forEach(function (t, n) {
        t.setAttribute('aria-selected', String(n === i));
        t.tabIndex = n === i ? 0 : -1;
      });
      panes.forEach(function (p, n) { p.classList.toggle('is-on', n === i); });
    }

    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(i); });
      t.addEventListener('keydown', function (e) {
        var step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (!step) return;
        e.preventDefault();
        var next = (i + step + tabs.length) % tabs.length;
        select(next);
        tabs[next].focus();
      });
    });

    select(0);
  });

})();
