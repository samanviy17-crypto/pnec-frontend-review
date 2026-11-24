// Illustrative geometry only. The textual scope/rules are never replaced by a score.
(() => {
  const house=document.getElementById('tree-house-gap'), gap=document.getElementById('tree-canopy-gap');
  if(!house || !gap)return;
  const root=document.getElementById('tree-distance-status');
  function update() {
    const h=Number(house.value), g=Number(gap.value), scale=9, wall=160, radius=63;
    const first=wall+h*scale+radius, second=first+2*radius+g*scale;
    document.getElementById('tree-canopy-one').setAttribute('cx',first);
    document.getElementById('tree-canopy-two').setAttribute('cx',second);
    const houseLine=document.getElementById('tree-house-line');houseLine.setAttribute('x2',first-radius);
    const gapLine=document.getElementById('tree-gap-line');gapLine.setAttribute('x1',first+radius);gapLine.setAttribute('x2',second-radius);
    document.getElementById('tree-house-value').textContent=h+' feet';document.getElementById('tree-canopy-value').textContent=g+' feet';
    const label=document.getElementById('tree-house-label');label.textContent=h+' ft';label.setAttribute('x',wall+h*scale/2);
    const labelGap=document.getElementById('tree-gap-label');labelGap.textContent=g+' ft';labelGap.setAttribute('x',first+radius+g*scale/2);
    root.textContent=`Example: ${h} feet from structure to mature drip line; ${g} feet between mature canopies. `+(h>=10 && g>=20?'These meet the two illustrated Poway new-tree minimums when that local rule applies.':'Below the illustrated new-tree minimum: '+[h<10?'10 feet from a combustible structure':'',g<20?'20 feet between canopy edges':''].filter(Boolean).join(' and ')+'. Check applicability with Poway Fire Prevention.');
  }
  house.addEventListener('input',update);gap.addEventListener('input',update);update();
})();
