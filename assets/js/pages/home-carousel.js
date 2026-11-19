(() => {
  const hero = document.querySelector('.pnec-hero');
  if (!hero) return;
  const photos = [...hero.querySelectorAll('.pnec-hero-backgrounds img')];
  const pause = hero.querySelector('.pnec-hero-pause');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let index = 0, paused = false, timer;
  function start() {
    clearInterval(timer);
    const motionOff = reduced.matches || document.documentElement.dataset.appearanceMotion === 'true';
    pause.hidden = motionOff;
    pause.textContent = paused ? 'Resume background photos' : 'Pause background photos';
    if (!paused && !motionOff && !document.hidden) {
      timer = setInterval(() => {
        if (reduced.matches || document.documentElement.dataset.appearanceMotion === 'true' || document.hidden) {
          start();
          return;
        }
        // Sequential cycling guarantees three distinct photos with no adjacent repeat.
        photos[index].classList.remove('is-current');
        index = (index + 1) % photos.length;
        photos[index].classList.add('is-current');
      }, 8000);
    }
  }
  pause.addEventListener('click', () => { paused = !paused; start(); });
  document.addEventListener('visibilitychange', start);
  reduced.addEventListener('change', start);
  window.addEventListener('pnec:appearance-changed', start);
  start();
  // Reuse the published weekly-tip endpoint and content workflow, never a synthetic tip.
  const content = document.getElementById('weekly-tip-content');
  const source = document.getElementById('weekly-tip-source');
  const base = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? (window.PNEC_API_BASE || `http://${location.hostname}:8425`) : window.PNEC_API_BASE;
  fetch(base + '/api/preparedness/weekly', {credentials:'omit', signal:AbortSignal.timeout(10000)})
    .then(response => {if (!response.ok) throw new Error(); return response.json();})
    .then(data => {
      const tips = (Array.isArray(data.tips) ? data.tips : []).filter(tip => typeof tip.title === 'string' && typeof tip.body === 'string');
      if (!tips.length) throw new Error();
      content.replaceChildren();
      tips.forEach((tip) => {
        const title = document.createElement('h3'); title.textContent = tip.title; content.append(title);
        const body = document.createElement('p'); body.textContent = tip.body; content.append(body);
      });
      source.textContent = 'PNEC preparedness tips' + (data.week_start ? ' · Week of ' + data.week_start : '') + '. Educational guidance; not an emergency alert.';
    })
    .catch(() => {content.textContent = 'The current weekly tip is unavailable. You can still use the emergency kit guide.'; source.textContent = 'No live risk information is shown.';});
})();
