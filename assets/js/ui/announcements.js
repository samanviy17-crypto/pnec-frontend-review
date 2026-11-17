(() => {
  const banner = document.getElementById('pnec-alert-banner');
  if (!banner) return;
  const key = 'pnec_dismissed_notice_versions';
  let dismissed = [];
  try {const saved = JSON.parse(localStorage.getItem(key)); if (Array.isArray(saved)) dismissed = saved.filter(v => typeof v === 'string').slice(-100);} catch { /* In-memory dismissal remains available. */ }
  const base = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8425' : window.PNEC_API_BASE;
  const utcTime = value => {
    if (typeof value !== 'string') return NaN;
    return Date.parse(value + (/Z$|[+-]\d\d:\d\d$/.test(value) ? '' : 'Z'));
  };
  function render(notices, official = false) {
      notices.forEach(notice => {
        if (!notice || typeof notice.message !== 'string' || !notice.message.trim() || notice.id == null || notice.is_active === false) return;
        if (notice.expires_at && (!Number.isFinite(utcTime(notice.expires_at)) || utcTime(notice.expires_at) <= Date.now())) return;
        let source;
        if (official) {
          try {source = new URL(notice.source_url);} catch {return;}
          if (notice.verified !== true || source.protocol !== 'https:' ||
              !['poway.org','www.poway.org','readysandiego.org','www.readysandiego.org','alertsandiego.org','www.alertsandiego.org','weather.gov','www.weather.gov','fire.ca.gov','www.fire.ca.gov'].includes(source.hostname) ||
              !Number.isFinite(utcTime(notice.updated_at)) || utcTime(notice.updated_at) > Date.now() ||
              !notice.expires_at || utcTime(notice.expires_at) <= utcTime(notice.updated_at)) return;
        }
        const version = JSON.stringify([notice.id,notice.updated_at || '',notice.message,notice.level]);
        // Priority notices remain visible. The current API cannot certify an official alert.
        const urgent = official || notice.level === 'danger';
        if (!urgent && dismissed.includes(version)) return;
        const article = document.createElement('article');
        const level = official ? 'danger' : ['info','warning','danger'].includes(notice.level) ? notice.level : 'info';
        article.className = 'pnec-alert pnec-alert-' + level;
        const copy = document.createElement('div'); copy.className = 'pnec-alert-copy';
        const heading = document.createElement('strong'); heading.textContent = official ? 'Verified official emergency notice' : urgent ? 'Important community notice' : level === 'warning' ? 'Community reminder' : 'Community announcement';
        const message = document.createElement('p'); message.textContent = notice.message;
        const meta = document.createElement('span'); meta.className = 'pnec-alert-meta';
        meta.textContent = 'Source: PNEC community announcements. Not an official emergency alert.' + (notice.updated_at ? ' Updated: ' + notice.updated_at + ' UTC.' : '');
        if (official) {
          meta.textContent = 'Verified source: ';
          const link = document.createElement('a'); link.href = source.href; link.textContent = source.hostname;
          meta.append(link, ' · Issued: ' + notice.updated_at + ' · Expires: ' + notice.expires_at);
        }
        copy.append(heading,message,meta); article.append(copy);
        if (!urgent) {
          const close = document.createElement('button'); close.type = 'button'; close.className = 'pnec-alert-dismiss'; close.textContent = '×'; close.setAttribute('aria-label','Dismiss community announcement');
          close.addEventListener('click', () => {
            const focused = article.contains(document.activeElement);
            article.remove(); dismissed.push(version); dismissed = dismissed.slice(-100);
            try {localStorage.setItem(key,JSON.stringify(dismissed));} catch { /* Session-only dismissal. */ }
            banner.hidden = !banner.children.length;
            if (focused) {const next = banner.querySelector('button') || document.getElementById('jupiterx-main'); next?.focus();}
          });
          article.append(close);
        }
        banner.append(article);
      });
      banner.hidden = !banner.children.length;
      banner.dataset.state = banner.hidden ? 'empty' : 'available';
  }
  try {const configured = JSON.parse(banner.dataset.configuredNotices || '[]'); if (Array.isArray(configured)) render(configured, true);} catch { /* Invalid source config is ignored. */ }
  fetch(base + '/api/announcements', {credentials:'omit', signal:AbortSignal.timeout(10000)})
    .then(response => {if (!response.ok) throw new Error(); return response.json();})
    .then(data => render(Array.isArray(data.announcements) ? data.announcements : []))
    .catch(() => {if (!banner.children.length) {banner.dataset.state = 'unavailable'; banner.hidden = true;}});
})();
