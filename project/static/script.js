let chart;

function creaGrafico(stat) {
  const ctx = document.getElementById('chart');
  chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Speso', 'Incassato', 'Profitto'],
      datasets: [{
        label: '€',
        data: [stat.speso, stat.guadagnato, stat.profitto],
        backgroundColor: ['#DC2626', '#16A34A', '#2563EB']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => '€ ' + ctx.raw.toFixed(2) } }
      }
    }
  });
}

function aggiornaTesti(stat) {
  document.getElementById('speso').textContent = '€ ' + stat.speso.toFixed(2);
  document.getElementById('guadagnato').textContent = '€ ' + stat.guadagnato.toFixed(2);
  document.getElementById('profitto').textContent = '€ ' + stat.profitto.toFixed(2);
}

async function aggiornaGrafico() {
  const res = await fetch('/api/statistiche');
  const stat = await res.json();
  chart.data.datasets[0].data = [stat.speso, stat.guadagnato, stat.profitto];
  chart.update();
  aggiornaTesti(stat);
}

function rigaProdotto(p) {
  const vendita = p.prezzo_vendita !== null;
  const profitto = vendita ? (p.prezzo_vendita - p.prezzo_acquisto).toFixed(2) : '-';

  return `
    <tr class="border-t">
      <td class="p-2">${p.nome}</td>
      <td class="p-2">€ ${p.prezzo_acquisto.toFixed(2)}</td>
      <td class="p-2">
        ${vendita
          ? '€ ' + p.prezzo_vendita.toFixed(2)
          : `<input type="number" step="0.01" class="border px-1 rounded w-24" id="sell-input-${p.id}" placeholder="Prezzo">
             <button onclick="vendi(${p.id})" class="text-green-600 hover:underline ml-1">Vendi</button>`
        }
      </td>
      <td class="p-2">${profitto}</td>
      <td class="p-2">
        <button onclick="elimina(${p.id})" class="text-red-600 hover:underline">Elimina</button>
      </td>
    </tr>
  `;
}

async function caricaProdotti() {
  const res = await fetch('/api/prodotti');
  const prodotti = await res.json();
  const body = document.getElementById('product-body');
  body.innerHTML = prodotti.map(p => rigaProdotto(p)).join('');
}

async function vendi(id) {
  const input = document.getElementById(`sell-input-${id}`);
  const vendita = parseFloat(input.value);
  if (!vendita) return alert("Inserisci un prezzo valido!");
  await fetch(`/sell/${id}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ vendita })
  });
  await aggiornaGrafico();
  await caricaProdotti();
}

async function elimina(id) {
  await fetch(`/delete/${id}`, { method: 'DELETE' });
  await aggiornaGrafico();
  await caricaProdotti();
}

async function aggiungiProdotto(event) {
  event.preventDefault();
  const nome = document.getElementById('nome').value;
  const acquisto = parseFloat(document.getElementById('acquisto').value);
  if (!nome || !acquisto) return alert("Inserisci nome e prezzo validi.");
  await fetch('/add', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ nome, acquisto })
  });
  document.getElementById('nome').value = '';
  document.getElementById('acquisto').value = '';
  await aggiornaGrafico();
  await caricaProdotti();
}

document.addEventListener('DOMContentLoaded', async () => {
  const stat = await fetch('/api/statistiche').then(r => r.json());
  creaGrafico(stat);
  aggiornaTesti(stat);
  await caricaProdotti();

  // collega il form
  document.getElementById('form-add').addEventListener('submit', aggiungiProdotto);
});
