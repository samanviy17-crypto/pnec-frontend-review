// Filter existing content without replacing checklists, forms or saved state.
(() => {
  function filter(inputId, selector, statusId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    function update() {
      const query = input.value.trim().toLocaleLowerCase();
      const items = [...document.querySelectorAll(selector)];
      let count = 0;
      items.forEach(item => {const match = item.textContent.toLocaleLowerCase().includes(query); item.hidden = !match; if (match) count++;});
      document.getElementById(statusId).textContent = query ? `${count} matching ${count === 1 ? 'result' : 'results'}. Clear the search to see everything.` : '';
    }
    input.addEventListener('input',update);
    // Kit data initializes independently; reapply a pending filter after re-render/reset.
    const host = document.getElementById('kit-categories-grid');
    if (inputId === 'pnec-kit-filter' && host) new MutationObserver(update).observe(host,{childList:true});
  }
  document.querySelectorAll('[data-resource-query]').forEach(button => button.addEventListener('click', () => {
    const input = document.getElementById('pnec-resource-filter');
    if (!input) return;
    input.value = button.dataset.resourceQuery;
    input.dispatchEvent(new Event('input'));
    input.focus();
  }));
  filter('pnec-kit-filter','.kit-category-card .kit-item','kit-filter-status');
  filter('pnec-resource-filter','.pnec-legacy-content .elementor-widget-image-box','resource-filter-status');
})();
