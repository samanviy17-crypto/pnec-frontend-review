/* Extend existing pages with account-backed community features. */
(() => {
  const api = (...args) => window.pnecCommunityRequest(...args);
  const el = (tag, text, parent) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (parent) parent.append(node);
    return node;
  };
  const status = parent => {const node = el('p', '', parent); node.setAttribute('role', 'status'); return node;};
  const section = (parent, title) => {const node = el('section', undefined, parent); el('h2', title, node); return node;};
  const button = (parent, title, action) => {
    const node = el('button', title, parent); node.type = 'button';
    node.addEventListener('click', async () => {
      node.disabled = true;
      try {await action();} catch(error) {const message = status(parent); message.textContent = error.message; message.className = 'community-error';}
      finally {node.disabled = false;}
    }); return node;
  };
  let fieldId = 0;
  const field = (form, name, title, type = 'text', options = {}) => {
    const label = el('label', title, form);
    const input = el(type === 'textarea' ? 'textarea' : type === 'select' ? 'select' : 'input', undefined, form);
    input.id = 'community-field-' + (++fieldId);
    label.htmlFor = input.id;
    input.name = name;
    if (input.tagName === 'INPUT') input.type = type;
    input.required = options.required !== false;
    if (options.max) input.maxLength = options.max;
    if (type === 'number') { input.min = options.min || 1; input.max = options.limit || 1000000; input.step = 1; }
    if (type === 'select') {
      el('option', 'Choose…', input).value = '';
      (options.choices || []).forEach(([value, text]) => {el('option', text, input).value = value;});
    }
    if (options.value !== undefined) input.value = options.value;
    return input;
  };
  const form = (parent, title, submit) => {
    const node = el('form', undefined, parent); const message = status(parent);
    const send = el('button', title); send.type = 'submit';
    node.addEventListener('submit', async event => {
      event.preventDefault(); send.disabled = true; message.textContent = 'Saving…';
      try {await submit(Object.fromEntries(new FormData(node))); message.textContent = 'Saved.';}
      catch(error) {message.textContent = error.message; message.className = 'community-error';}
      finally {send.disabled = false;}
    });
    // Add fields before the submit button, then call finish().
    node.finish = () => node.append(send); return node;
  };
  const numberData = (data, keys) => {keys.forEach(k => {data[k] = data[k] === '' ? null : Number(data[k]);}); return data;};
  let user = null, neighborhoods = [];
  const managing = () => user && ['coordinator', 'staff', 'admin'].includes(user.role);
  const staff = () => user && ['staff', 'admin'].includes(user.role);
  const neighborhoodField = (node, optional = false) => field(node, 'neighborhood_id', 'Neighborhood', 'select', {
    required: !optional, value: user?.neighborhood_id || '', choices: neighborhoods.map(n => [n.id, n.name])
  });
  const neighborhoodName = id => neighborhoods.find(n => n.id === id)?.name || 'Citywide';
  const loginNote = parent => el('p', 'Sign in using the site account menu to save and manage your information.', parent);

  async function household(parent) {
    const node = section(parent, 'Your household plan');
    if (!user) return loginNote(node);
    const record = await api('/preparedness');
    const f = form(node, 'Save household plan', async data => {
      const saved = await api('/preparedness', 'PATCH', numberData(data, ['household_size']));
      window.dispatchEvent(new CustomEvent('pnec-household-saved', {detail:saved}));
    });
    field(f, 'household_size', 'People in your household', 'number', {limit:50, value:record.household_size});
    field(f, 'meeting_point', 'Meeting point', 'text', {max:300, required:false, value:record.meeting_point});
    field(f, 'evacuation_plan', 'Household evacuation plan and access needs', 'textarea', {max:2000, required:false, value:record.evacuation_plan});
    f.finish(); el('p', 'Your plan is private to your account. Review your neighborhood resources before making a plan.', node);
  }

  async function quiz(parent) {
    const node = section(parent, 'Preparedness assessment');
    const {questions} = await api('/preparedness/quiz');
    const result = status(node);
    if (!user) return loginNote(node);
    const record = await api('/preparedness');
    const show = data => {result.textContent = `Preparedness score: ${data.score}%\n${data.recommendations.join('\n') || 'Review and practice your plan regularly.'}`;};
    if (record.assessment) show(record.assessment);
    const f = form(node, 'Save assessment', async data => {
      const answers = Object.fromEntries(Object.entries(data).map(([k,v]) => [k, v === 'yes']));
      show(await api('/preparedness/quiz', 'POST', {answers}));
    });
    questions.forEach(q => field(f, q.id, q.question, 'select', {choices:[['yes','Yes'],['no','No']], value:record.quiz_answers[q.id] === undefined ? '' : record.quiz_answers[q.id] ? 'yes' : 'no'}));
    f.finish();
  }

  async function tasks(parent) {
    const node = section(parent, 'Volunteer shifts and tasks');
    const list = el('div', undefined, node);
    async function refresh() {
      const data = await api('/volunteer/tasks'); list.replaceChildren();
      if (!data.tasks.length) el('p', 'No shifts have been posted yet.', list);
      data.tasks.forEach(t => {
        const card = el('article', undefined, list); el('h3', t.title, card); el('p', t.description, card);
        el('p', `${new Date(t.starts_at).toLocaleString()} · ${neighborhoodName(t.neighborhood_id)} · ${t.claimed_count}/${t.capacity} slots claimed${t.closed ? ' · Closed' : ''}`, card);
        if (user && t.signed_up) button(card, 'Cancel my signup', async () => {await api(`/volunteer/tasks/${t.id}/signup`, 'DELETE'); await refresh();});
        else if (user && !t.closed && t.claimed_count < t.capacity && new Date(t.starts_at) > new Date()) button(card, 'Claim a slot', async () => {await api(`/volunteer/tasks/${t.id}/signup`, 'POST', {}); await refresh();});
        if (managing() && (user.role !== 'coordinator' || user.neighborhood_id === t.neighborhood_id)) {
          el('p', 'Volunteers: ' + (t.volunteers || []).map(v => `${v.name} (${v.email})`).join(', '), card);
          button(card, t.closed ? 'Reopen shift' : 'Close shift', async () => {await api(`/volunteer/tasks/${t.id}`, 'PATCH', {closed:!t.closed}); await refresh();});
        }
      });
    }
    await refresh();
    if (!user) loginNote(node);
    if (managing()) {
      const f = form(node, 'Post a shift', async data => {
        data.starts_at = new Date(data.starts_at).toISOString();
        await api('/volunteer/tasks', 'POST', numberData(data, ['neighborhood_id','capacity'])); f.reset(); await refresh();
      });
      field(f, 'title', 'Task or shift title', 'text', {max:200});
      field(f, 'description', 'Details and meeting location', 'textarea', {max:2000, required:false});
      neighborhoodField(f, user.role !== 'coordinator');
      field(f, 'starts_at', 'Start date and time (your local time)', 'datetime-local');
      field(f, 'capacity', 'Available slots', 'number', {limit:1000}); f.finish();
    }
  }

  async function checkins(parent) {
    const node = section(parent, 'Resident well-being check-in');
    el('p', 'For immediate danger, call 911. These check-ins go to PNEC coordinators and are not monitored emergency dispatch. Each status includes its last update time.', node);
    if (!user) return loginNote(node);
    const list = el('div', undefined, node);
    async function refresh() {
      const data = await api('/check-ins'); list.replaceChildren();
      if (!data.check_ins.length) el('p', 'No check-ins to display.', list);
      data.check_ins.forEach(c => {
        const card = el('article', undefined, list);
        el('h3', `${c.name}: ${c.status === 'safe' ? 'Safe' : 'Need help'}`, card);
        el('p', `${neighborhoodName(c.neighborhood_id)} · Updated ${new Date(c.updated_at).toLocaleString()}`, card); el('p', c.note, card);
      });
    }
    await refresh();
    const f = form(node, 'Update my status', async data => {await api('/check-ins', 'PUT', data); await refresh();});
    field(f, 'status', 'My status', 'select', {choices:[['safe','Safe'],['need_help','Need help']]});
    field(f, 'note', 'Details for your coordinator', 'textarea', {max:1000, required:false}); f.finish();
    button(node, 'Remove my check-in', async () => {await api('/check-ins', 'DELETE'); await refresh();});
  }

  async function hazards(parent) {
    const node = section(parent, 'Report a neighborhood hazard');
    node.id = 'hazard-reporting';
    if (location.hash === '#hazard-reporting') node.scrollIntoView({block: 'center'});
    el('p', 'Report non-emergency hazards for coordinator review. For immediate danger, call 911.', node);
    if (!user) return loginNote(node);
    const list = el('div', undefined, node);
    async function refresh() {
      const data = await api('/hazards'); list.replaceChildren();
      if (!data.hazards.length) el('p', 'No hazard reports to display.', list);
      data.hazards.forEach(h => {
        const card = el('article', undefined, list); el('h3', `${h.location} · ${h.status}`, card);
        el('p', `${neighborhoodName(h.neighborhood_id)} · ${h.category} · ${h.name} · ${new Date(h.created_at).toLocaleString()}`, card);
        el('p', h.description, card);
        if (managing()) ['open','reviewing','resolved'].filter(s => s !== h.status).forEach(s => button(card, `Mark ${s}`, async () => {await api(`/hazards/${h.id}`, 'PATCH', {status:s}); await refresh();}));
      });
    }
    await refresh();
    const f = form(node, 'Submit hazard report', async data => {await api('/hazards', 'POST', numberData(data, ['neighborhood_id'])); f.reset(); await refresh();});
    neighborhoodField(f);
    field(f, 'category', 'Hazard type', 'select', {choices:[['tree','Downed tree'],['route','Blocked route'],['hydrant','Damaged hydrant'],['other','Other']]});
    field(f, 'location', 'Location', 'text', {max:300}); field(f, 'description', 'Description', 'textarea', {max:2000}); f.finish();
  }

  async function drives(parent) {
    const node = section(parent, 'Community supply drives');
    el('p', 'Pledges are promises of supplies. The goal tracker counts only deliveries confirmed by staff. Use the existing donation options below for monetary gifts.', node);
    const list = el('div', undefined, node);
    async function refresh() {
      const data = await api('/supply-drives'); list.replaceChildren();
      if (!data.drives.length) el('p', 'No supply drives have been posted yet.', list);
      for (const d of data.drives) {
        const card = el('article', undefined, list); el('h3', d.title, card); el('p', d.description, card);
        el('p', `${d.received} / ${d.goal} ${d.unit} received (${d.progress}%). ${d.pledged} ${d.unit} pledged, awaiting delivery.${d.closed ? ' Drive closed.' : ''}`, card);
        const progress = el('progress', undefined, card); progress.max = d.goal; progress.value = d.received; progress.setAttribute('aria-label', d.title + ' received supplies');
        if (user && !d.closed) {
          const f = form(card, 'Pledge supplies', async data => {await api(`/supply-drives/${d.id}/pledges`, 'POST', numberData(data, ['quantity'])); await refresh();});
          field(f, 'quantity', `Quantity (${d.unit})`, 'number'); f.finish();
        }
        if (user) {
          const {pledges} = await api(`/supply-drives/${d.id}/pledges`);
          pledges.forEach(p => {
            const row = el('p', `${p.name}: ${p.quantity} ${d.unit} · ${p.fulfilled ? 'Received' : 'Awaiting delivery'}`, card);
            if (staff() && !p.fulfilled) button(row, 'Confirm delivery received', async () => {await api(`/supply-pledges/${p.id}/receive`, 'PATCH', {}); await refresh();});
          });
        }
        if (staff()) button(card, d.closed ? 'Reopen drive' : 'Close drive', async () => {await api(`/supply-drives/${d.id}`, 'PATCH', {closed:!d.closed}); await refresh();});
      }
    }
    await refresh(); if (!user) loginNote(node);
    if (staff()) {
      const f = form(node, 'Create supply drive', async data => {await api('/supply-drives', 'POST', numberData(data, ['goal'])); f.reset(); await refresh();});
      field(f, 'title', 'Drive title', 'text', {max:200}); field(f, 'description', 'Requested supplies and delivery instructions', 'textarea', {max:2000});
      field(f, 'unit', 'Unit (e.g. kits, bottles)', 'text', {max:30}); field(f, 'goal', 'Goal quantity', 'number'); f.finish();
    }
  }

  async function weekly(parent) {
    const node = section(parent, 'This week: preparedness and community learning');
    const data = await api('/preparedness/weekly');
    el('p', `Week of ${data.week_start} · ${data.risk_available ? `${data.threat} focus${data.risk_is_stale ? ' (cached risk data)' : ''}` : 'Live risk data unavailable; showing general preparedness tips.'}`, node);
    data.tips.forEach(t => {const card = el('article', undefined, node); el('h3', t.title, card); el('p', t.body, card);});
    if (!data.events.length) el('p', 'No community learning events scheduled for the next seven days.', node);
    data.events.forEach(e => {const card = el('article', undefined, node); el('h3', e.title, card); el('p', `${new Date(e.date).toLocaleString()} · ${e.location || ''}`, card); el('p', e.description || '', card);});
  }

  async function tipsAdmin(parent) {
    if (!staff()) return;
    const node = section(parent, 'Publish weekly preparedness tips');
    const f = form(node, 'Publish tip', async data => {await api('/preparedness/weekly', 'POST', data); f.reset();});
    field(f, 'title', 'Title', 'text', {max:200}); field(f, 'body', 'Tip', 'textarea', {max:3000});
    field(f, 'week_start', 'Week starting Monday', 'date');
    field(f, 'threat', 'Show when this threat is active', 'select', {choices:[['general','General'],['fire','Wildfire'],['flood','Flood'],['heat','Heat']]}); f.finish();
  }

  async function feedback(parent) {
    const node = section(parent, 'Community FAQ feedback');
    el('p', 'Search PNEC FAQs, rate an answer, or send a question to the existing staff queue.', node);
    const list = el('div', undefined, node);
    const f = form(node, 'Search FAQs', async data => {
      const results = await searchFaqItems(data.q); list.replaceChildren();
      if (!results.length) el('p', 'No matching answers. Submit your question below.', list);
      results.forEach(item => {
        const card = el('article', undefined, list); el('h3', item.question, card); el('p', item.answer, card);
        const voted = status(card);
        const vote = async helpful => {await submitFaqHelpfulVote(item.id, helpful); voted.textContent = 'Thank you for your feedback.';};
        button(card, 'Helpful', () => vote(true)); button(card, 'Not helpful', () => vote(false));
      });
    }); field(f, 'q', 'Search question', 'text', {max:255}); f.finish();
    const question = form(node, 'Send question to staff', async data => {await submitUserQuestion(data); question.reset();});
    field(question, 'display_name', 'Name', 'text', {max:100, value:user?.display_name || ''});
    field(question, 'email', 'Email for a reply', 'email', {max:254, value:user?.email || ''});
    field(question, 'question_text', 'Your unanswered question (at least 10 characters)', 'textarea', {max:4000}); question.finish();
  }

  async function language(parent) {
    const node = section(parent, 'Preparedness information / Información / Impormasyon');
    const copy = {
      en: {title:'Emergency preparedness', body:'Review your household kit and evacuation plan. Find your neighborhood for local resources. Risk Watch displays wildfire, flood and heat levels. Follow official local emergency alerts and evacuation instructions.', risk:'Risk Watch', fire:'Wildfire', flood:'Flood', heat:'Heat', unavailable:'Live risk data unavailable.', links:['Household checklist','Neighborhood and evacuation resources','Preparedness resources'], bot:'Helper Bot will respond in English.'},
      es: {title:'Preparación para emergencias', body:'Revise el kit y el plan de evacuación de su hogar. Busque su vecindario para consultar los recursos locales. Risk Watch muestra los niveles de riesgo de incendio, inundación y calor. Siga las alertas oficiales locales y las instrucciones de evacuación.', risk:'Riesgos actuales', fire:'Incendio', flood:'Inundación', heat:'Calor', unavailable:'Los datos de riesgo actuales no están disponibles.', links:['Lista de preparación del hogar','Recursos del vecindario y de evacuación','Recursos de preparación'], bot:'Helper Bot responderá en español.'},
      tl: {title:'Paghahanda sa emerhensiya', body:'Suriin ang emergency kit at plano sa paglikas ng inyong sambahayan. Hanapin ang inyong kapitbahayan para sa lokal na impormasyon. Ipinapakita ng Risk Watch ang panganib ng sunog, baha at init. Sundin ang opisyal na lokal na mga alerto at tagubilin sa paglikas.', risk:'Kasalukuyang panganib', fire:'Sunog', flood:'Baha', heat:'Init', unavailable:'Hindi available ang kasalukuyang datos ng panganib.', links:['Checklist ng sambahayan','Impormasyon ng kapitbahayan at paglikas','Mga sanggunian sa paghahanda'], bot:'Sasagot ang Helper Bot sa Tagalog.'}
    };
    const i18n = await import('../chatbot/i18n.js');
    const selector = field(node, 'language', 'Language / Idioma / Wika', 'select', {choices:[['en','English'],['es','Español'],['tl','Tagalog']], value:i18n.getLang()});
    const blockSelect = field(node, 'selected_neighborhood', 'Neighborhood / Vecindario / Kapitbahayan', 'select', {
      required:false, value:user?.neighborhood_id || '', choices:neighborhoods.map(n => [n.id,n.name])
    });
    const content = el('div', undefined, node);
    let risk = null; try {risk = await api('/risk');} catch (_) { /* show unavailable */ }
    const levels = {en:{LOW:'Low',MODERATE:'Moderate',HIGH:'High',CRITICAL:'Critical'},es:{LOW:'Bajo',MODERATE:'Moderado',HIGH:'Alto',CRITICAL:'Crítico'},tl:{LOW:'Mababa',MODERATE:'Katamtaman',HIGH:'Mataas',CRITICAL:'Kritikal'}};
    const render = () => {
      const lang = selector.value || 'en', text = copy[lang]; content.replaceChildren(); content.lang = lang;
      el('h3', text.title, content); el('p', text.body, content);
      const block = neighborhoods.find(n => String(n.id) === blockSelect.value);
      if (block) {
        const labels = {en:['Neighborhood','Evacuation zone','Coordinator','Not listed'],es:['Vecindario','Zona de evacuación','Coordinador','No indicado'],tl:['Kapitbahayan','Sona ng paglikas','Koordinator','Walang nakalista']}[lang];
        el('p', `${labels[0]}: ${block.name}. ${labels[1]}: ${block.zone || labels[3]}. ${labels[2]}: ${block.coordinator_name || labels[3]} ${block.coordinator_email || ''}`, content);
      }
      el('p', risk ? `${text.risk}: ${text.fire}: ${levels[lang][risk.fire_level] || '—'}; ${text.flood}: ${levels[lang][risk.flood_level] || '—'}; ${text.heat}: ${levels[lang][risk.heat_level] || '—'}. ${risk.updated_at || ''}${risk.is_stale ? ' (cached)' : ''}` : text.unavailable, content);
      const paths = ['/pages/checklist.html','/pages/find-your-neighborhood.html','/pages/preparedness-resources.html'];
      text.links.forEach((label,index) => {const p = el('p', undefined, content); const a = el('a', label, p); a.href = (window.PNEC_SITE_BASE || '') + paths[index];}); el('p', text.bot, content);
    };
    selector.addEventListener('change', () => {i18n.setLang(selector.value || 'en'); render();});
    blockSelect.addEventListener('change', render); render();
  }

  async function coordination(parent) {
    if (!managing()) {const node = section(parent, 'Neighborhood coordination'); loginNote(node); return;}
    const node = section(parent, 'Neighborhood coordination');
    el('p', user.role === 'coordinator' ? `Reports for ${neighborhoodName(user.neighborhood_id)}.` : 'Reports across all neighborhoods.', node);
    await checkins(node); await hazards(node);
    if (staff()) {
      const feedback = section(node, 'FAQ answers needing review');
      const data = await api('/faq/feedback');
      if (!data.feedback.length) el('p', 'No FAQ votes yet.', feedback);
      data.feedback.forEach(row => el('p', `${row.question}: ${row.not_helpful} not helpful out of ${row.votes} votes.`, feedback));
    }
  }

  async function init() {
    const roots = [...document.querySelectorAll('[data-community-tools]')];
    const main = document.querySelector('main');
    if (main && !document.querySelector('.community-links')) {
      const nav = document.createElement('nav'); nav.className = 'community-links'; nav.setAttribute('aria-label','Preparedness tools');
      [['/pages/checklist.html','My preparedness & check-in'],['/pages/volunteer.html','Volunteer shifts'],['/donation-form/','Supply drives'],['/pages/preparedness-resources.html','Weekly tips & languages'],['/pages/dashboard.html','Coordinator reports']].forEach(([href,title]) => {const a = el('a', title, nav); a.href = (window.PNEC_SITE_BASE || '') + href;}); main.prepend(nav);
    }
    if (!roots.length) return;
    try { user = await fetchCurrentUser(); neighborhoods = await fetchNeighborhoodsForSelect(); } catch (_) { /* individual tools show errors */ }
    const builders = {household, quiz, tasks, checkins, hazards, drives, weekly, feedback, language, coordination, 'tips-admin':tipsAdmin};
    for (const root of roots) {
      root.replaceChildren();
      for (const name of root.dataset.communityTools.split(' ')) {
        try {await builders[name]?.(root);} catch(error) {const message = status(root); message.textContent = `Could not load ${name}: ${error.message} Reload to retry.`; message.className = 'community-error';}
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
