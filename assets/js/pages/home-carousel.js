(() => {
  const carousel = document.querySelector('.pnec-carousel');
  if (!carousel) return;
  const slides = [...carousel.querySelectorAll('.pnec-slide')];
  const dots = [...carousel.querySelectorAll('[data-slide]')];
  const pause = carousel.querySelector('[data-carousel="pause"]');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let index = 0, paused = reduced.matches || document.documentElement.dataset.appearanceMotion === 'true', timer;
  function stop() { clearInterval(timer); }
  function start() {
    stop();
    const motionOff = reduced.matches || document.documentElement.dataset.appearanceMotion === 'true';
    pause.disabled = motionOff;
    pause.textContent = motionOff ? 'Rotation off (reduced motion)' : paused ? 'Resume rotation' : 'Pause rotation';
    if (!paused && !reduced.matches && document.documentElement.dataset.appearanceMotion !== 'true' && !document.hidden && !carousel.matches(':hover, :focus-within')) {
      timer = setInterval(() => show(index + 1), 8000);
    }
  }
  function show(next, announce = false) {
    index = (next + slides.length) % slides.length;
    slides.forEach((slide, i) => {slide.hidden = i !== index;});
    dots.forEach((dot, i) => {if (i === index) dot.setAttribute('aria-current','true'); else dot.removeAttribute('aria-current');});
    if (announce) carousel.querySelector('[data-carousel-status]').textContent = slides[index].getAttribute('aria-label');
  }
  function manual(next) { paused = true; show(next, true); start(); }
  carousel.querySelector('.pnec-carousel-controls').hidden = false;
  carousel.querySelector('[data-carousel="previous"]').addEventListener('click', () => manual(index - 1));
  carousel.querySelector('[data-carousel="next"]').addEventListener('click', () => manual(index + 1));
  dots.forEach((dot, i) => dot.addEventListener('click', () => manual(i)));
  pause.addEventListener('click', () => {paused = !paused; start();});
  carousel.addEventListener('keydown', event => {
    if (!['ArrowLeft','ArrowRight'].includes(event.key)) return;
    event.preventDefault(); manual(index + (event.key === 'ArrowRight' ? 1 : -1));
  });
  carousel.addEventListener('mouseenter', stop);
  carousel.addEventListener('mouseleave', start);
  carousel.addEventListener('focusin', stop);
  carousel.addEventListener('focusout', () => requestAnimationFrame(start));
  document.addEventListener('visibilitychange', start);
  function motionChanged() {if (reduced.matches || document.documentElement.dataset.appearanceMotion === 'true') paused = true; start();}
  reduced.addEventListener('change', motionChanged);
  window.addEventListener('pnec:appearance-changed', motionChanged);
  start();
  // Reuse the published weekly-tip endpoint and content workflow, never a synthetic tip.
  const content = document.getElementById('weekly-tip-content');
  const source = document.getElementById('weekly-tip-source');
  const base = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8425' : window.PNEC_API_BASE;
  fetch(base + '/api/preparedness/weekly', {credentials:'omit', signal:AbortSignal.timeout(10000)})
    .then(response => {if (!response.ok) throw new Error(); return response.json();})
    .then(data => {
      const tips = (Array.isArray(data.tips) ? data.tips : []).filter(tip => typeof tip.title === 'string' && typeof tip.body === 'string');
      if (!tips.length) throw new Error();
      document.getElementById('weekly-tip-title').textContent = tips[0].title;
      content.replaceChildren();
      tips.forEach((tip, i) => {
        if (i) {const title = document.createElement('h3'); title.textContent = tip.title; content.append(title);}
        const body = document.createElement('p'); body.textContent = tip.body; content.append(body);
      });
      source.textContent = 'PNEC preparedness tips' + (data.week_start ? ' · Week of ' + data.week_start : '') + '. Educational guidance; not an emergency alert.';
    })
    .catch(() => {content.textContent = 'The current weekly tip is unavailable. You can still use the emergency kit guide.'; source.textContent = 'No live risk information is shown.';});
})();
