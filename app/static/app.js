const state = { file: null, result: null, mode: 'forecast', busy: false };
const el = id => document.getElementById(id);
const fileInput = el('fileInput');
const dropZone = el('dropZone');

async function checkHealth() {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    el('statusDot').classList.add('ready');
    const kronos = data.kronos?.installed ? 'Kronos installed' : 'Baseline ready';
    el('statusText').textContent = `${kronos} · v${data.version}`;
  } catch {
    el('statusText').textContent = 'Server unavailable';
  }
}

function setFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.csv')) return showError('Please choose a CSV file.');
  if (file.size > 15 * 1024 * 1024) return showError('The CSV is larger than 15 MB.');
  state.file = file;
  el('fileName').textContent = file.name;
  clearError();
}

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', event => setFile(event.target.files[0]));
['dragenter', 'dragover'].forEach(name => dropZone.addEventListener(name, event => {
  event.preventDefault(); dropZone.classList.add('drag');
}));
['dragleave', 'drop'].forEach(name => dropZone.addEventListener(name, event => {
  event.preventDefault(); dropZone.classList.remove('drag');
}));
dropZone.addEventListener('drop', event => setFile(event.dataTransfer.files[0]));
el('paths').addEventListener('input', event => { el('pathsValue').textContent = event.target.value; });

for (const tab of document.querySelectorAll('.tab')) {
  tab.addEventListener('click', () => {
    for (const item of document.querySelectorAll('.tab')) {
      item.classList.remove('active'); item.setAttribute('aria-selected', 'false');
    }
    tab.classList.add('active'); tab.setAttribute('aria-selected', 'true');
    state.mode = tab.dataset.tab;
    el('forecastControls').classList.toggle('hidden', state.mode !== 'forecast');
    el('backtestControls').classList.toggle('hidden', state.mode !== 'backtest');
  });
}

function showError(message) {
  el('errorBox').textContent = message;
  el('errorBox').classList.remove('hidden');
  el('loadingState').classList.add('hidden');
  el('emptyState').classList.add('hidden');
  setBusy(false);
}
function clearError() { el('errorBox').classList.add('hidden'); }
function nullableNumber(id) { const value = el(id).value.trim(); return value === '' ? null : Number(value); }
function setBusy(busy) {
  state.busy = busy;
  el('forecastButton').disabled = busy;
  el('backtestButton').disabled = busy;
}
function begin() {
  if (state.busy) return false;
  if (!state.file) { showError('Choose a CSV file first. Try the sample file if you do not have one.'); return false; }
  clearError();
  el('fallbackBox').classList.add('hidden');
  el('emptyState').classList.add('hidden');
  el('resultContent').classList.add('hidden');
  el('loadingState').classList.remove('hidden');
  setBusy(true);
  return true;
}
async function post(endpoint, settings) {
  const form = new FormData();
  form.append('file', state.file);
  form.append('settings_json', JSON.stringify(settings));
  const response = await fetch(endpoint, { method: 'POST', body: form });
  let data;
  try { data = await response.json(); } catch { throw new Error('The server returned an unreadable response.'); }
  if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
  return data;
}
function finish(data, title) {
  state.result = data;
  setBusy(false);
  el('loadingState').classList.add('hidden');
  el('resultContent').classList.remove('hidden');
  el('exportButton').classList.remove('hidden');
  el('resultsTitle').textContent = title;
  renderReport(data.data_report);
  renderNotes(data.notes || []);
  if (data.fallback) {
    el('fallbackBox').textContent = `Visible fallback: ${data.fallback.from} → ${data.fallback.to}. ${data.fallback.reason}`;
    el('fallbackBox').classList.remove('hidden');
  }
}

el('forecastButton').addEventListener('click', async () => {
  if (!begin()) return;
  try {
    const data = await post('/api/forecast', {
      engine: el('engine').value,
      baseline_model: el('baselineModel').value,
      model_size: el('modelSize').value,
      horizon: Number(el('horizon').value),
      lookback: Number(el('lookback').value),
      paths: Number(el('paths').value),
      block_size: Number(el('blockSize').value),
      kronos_samples: Number(el('kronosSamples').value)
    });
    finish(data, `Forecast · ${data.engine}`);
    renderForecast(data);
    el('tradesWrap').classList.add('hidden');
    el('forecastEvidence').classList.add('hidden');
  } catch (error) { showError(error.message); }
});

el('backtestButton').addEventListener('click', async () => {
  if (!begin()) return;
  try {
    const data = await post('/api/backtest', {
      baseline_model: el('btModel').value,
      horizon: Number(el('btHorizon').value),
      lookback: Number(el('btLookback').value),
      step: Number(el('btStep').value),
      block_size: Number(el('btBlockSize').value),
      threshold_percent: Number(el('threshold').value),
      fee_percent: Number(el('fee').value),
      slippage_percent: Number(el('slippage').value),
      position_size_percent: Number(el('positionSize').value),
      direction: el('direction').value,
      execution_delay: Number(el('executionDelay').value),
      stop_loss_percent: nullableNumber('stopLoss'),
      take_profit_percent: nullableNumber('takeProfit'),
      allow_overlap: el('allowOverlap').checked
    });
    finish(data, 'Evidence-aware walk-forward backtest');
    renderBacktest(data);
  } catch (error) { showError(error.message); }
});

el('exportButton').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(state.result, null, 2)], { type: 'application/json' });
  const anchor = document.createElement('a');
  const url = URL.createObjectURL(blob);
  anchor.href = url;
  anchor.download = `marketforge-${state.mode}-result.json`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
});

function metric(label, value, cls = '') {
  return `<div class="metric"><small>${escapeHtml(label)}</small><strong class="${cls}">${escapeHtml(String(value))}</strong></div>`;
}
function renderForecast(data) {
  const summary = data.summary;
  const cls = summary.expected_return_percent >= 0 ? 'positive' : 'negative';
  el('metrics').innerHTML =
    metric('Last close', summary.last_close) +
    metric('Forecast median', summary.forecast_close) +
    metric('Expected change', `${summary.expected_return_percent}%`, cls) +
    metric('80% range', `${summary.lower_close} – ${summary.upper_close}`) +
    metric('Future candles', summary.horizon) +
    metric('Scenarios', summary.paths);
  drawForecastChart(data.history, data.forecast);
}
function renderBacktest(data) {
  const metrics = data.metrics;
  const cls = metrics.total_return_percent >= 0 ? 'positive' : 'negative';
  const excessCls = metrics.excess_return_percent >= 0 ? 'positive' : 'negative';
  el('metrics').innerHTML =
    metric('Simulated trades', metrics.trades) +
    metric('Strategy return', `${metrics.total_return_percent}%`, cls) +
    metric('Buy & hold', `${metrics.benchmark_return_percent}%`, metrics.benchmark_return_percent >= 0 ? 'positive' : 'negative') +
    metric('Excess return', `${metrics.excess_return_percent}%`, excessCls) +
    metric('Win rate', `${metrics.win_rate_percent}%`) +
    metric('Max drawdown', `${metrics.max_drawdown_percent}%`, 'negative');

  drawEquityChart(data.equity_curve || []);
  const forecast = data.forecast_metrics || {};
  el('forecastMetrics').innerHTML =
    metric('Forecasts tested', forecast.evaluations || 0) +
    metric('MAE', `${forecast.mae_percent || 0}%`) +
    metric('Direction accuracy', `${forecast.directional_accuracy_percent || 0}%`) +
    metric('80% coverage', `${forecast.interval_80_coverage_percent || 0}%`);
  el('forecastEvidence').classList.remove('hidden');

  const body = el('tradesBody');
  body.innerHTML = (data.trades || []).slice(-40).reverse().map(trade => `<tr>
    <td>${escapeHtml(formatTimestamp(trade.signal_timestamp))}</td>
    <td>${escapeHtml(formatTimestamp(trade.entry_timestamp))}</td>
    <td>${escapeHtml(trade.side)}</td>
    <td>${escapeHtml(trade.exit_reason)}</td>
    <td>${escapeHtml(String(trade.predicted_return_percent))}%</td>
    <td class="${trade.net_return_percent >= 0 ? 'positive' : 'negative'}">${escapeHtml(String(trade.net_return_percent))}%</td>
    <td>${escapeHtml(String(trade.equity))}</td>
  </tr>`).join('');
  el('tradesWrap').classList.toggle('hidden', !(data.trades || []).length);
}
function renderReport(report) {
  if (!report) { el('dataReport').innerHTML = ''; return; }
  const entries = [
    ['Quality score', `${report.quality_score}/100`],
    ['Data fingerprint', report.data_fingerprint],
    ['Rows received', report.rows_received],
    ['Rows kept', report.rows_kept],
    ['Invalid removed', report.invalid_rows_removed],
    ['Duplicates removed', report.duplicates_removed],
    ['Candles repaired', report.candles_repaired],
    ['Irregular intervals', report.irregular_intervals],
    ['Estimated missing', report.estimated_missing_candles],
    ['Detected interval', report.inferred_interval],
    ['Outlier moves', report.outlier_returns]
  ];
  el('dataReport').innerHTML = entries.map(([label, value]) => `<div class="report-item"><span>${escapeHtml(label)}</span><b>${escapeHtml(String(value))}</b></div>`).join('') +
    (report.warnings || []).map(warning => `<div class="warning">⚠ ${escapeHtml(warning)}</div>`).join('');
}
function renderNotes(notes) { el('notes').innerHTML = notes.map(note => `<div>• ${escapeHtml(note)}</div>`).join(''); }
function formatTimestamp(value) { return String(value || '').replace('T', ' ').replace('Z', ' UTC'); }

function prepCanvas() {
  const canvas = el('chart');
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = 390;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const context = canvas.getContext('2d');
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  return { context, width, height };
}
function drawGrid(context, width, height) {
  context.strokeStyle = 'rgba(181,255,223,.08)';
  context.lineWidth = 1;
  for (let i = 1; i < 6; i += 1) {
    const y = i * height / 6;
    context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke();
  }
}
function drawForecastChart(history, forecast) {
  const { context, width, height } = prepCanvas();
  drawGrid(context, width, height);
  const historical = history.map(row => Number(row.close));
  const median = forecast.map(row => Number(row.close));
  const lower = forecast.map(row => Number(row.lower_close));
  const upper = forecast.map(row => Number(row.upper_close));
  const all = [...historical, ...lower, ...upper].filter(Number.isFinite);
  const min = Math.min(...all), max = Math.max(...all), padding = (max - min || 1) * .08;
  const y = value => height - 26 - (value - (min - padding)) / (max - min + 2 * padding) * (height - 52);
  const total = historical.length + median.length;
  const x = index => 18 + index / Math.max(total - 1, 1) * (width - 36);
  const split = historical.length - 1;

  context.fillStyle = 'rgba(111,255,193,.09)';
  context.beginPath();
  forecast.forEach((_, index) => index ? context.lineTo(x(historical.length + index), y(upper[index])) : context.moveTo(x(historical.length + index), y(upper[index])));
  for (let index = forecast.length - 1; index >= 0; index -= 1) context.lineTo(x(historical.length + index), y(lower[index]));
  context.closePath(); context.fill();
  line(context, historical.map((value, index) => [x(index), y(value)]), '#91aaa0', 1.6);
  line(context, [[x(split), y(historical[historical.length - 1])], ...median.map((value, index) => [x(historical.length + index), y(value)])], '#6fffc1', 2.4);
  context.setLineDash([5, 5]); context.strokeStyle = 'rgba(255,255,255,.24)'; context.beginPath(); context.moveTo(x(split), 10); context.lineTo(x(split), height - 10); context.stroke(); context.setLineDash([]);
  context.fillStyle = '#91aaa0'; context.font = '12px system-ui'; context.fillText(min.toFixed(4), 8, height - 9); context.fillText(max.toFixed(4), 8, 16);
}
function drawEquityChart(equityCurve) {
  const { context, width, height } = prepCanvas();
  drawGrid(context, width, height);
  const values = (equityCurve || []).map(point => Number(point.equity)).filter(Number.isFinite);
  if (values.length < 2) { context.fillStyle = '#91aaa0'; context.font = '16px system-ui'; context.fillText('No completed trades.', 30, height / 2); return; }
  const min = Math.min(...values), max = Math.max(...values), padding = (max - min || .02) * .15;
  const y = value => height - 25 - (value - (min - padding)) / (max - min + 2 * padding) * (height - 50);
  const x = index => 18 + index / Math.max(values.length - 1, 1) * (width - 36);
  line(context, values.map((value, index) => [x(index), y(value)]), '#6fffc1', 2.4);
  context.fillStyle = '#91aaa0'; context.font = '12px system-ui'; context.fillText('Start 1.000', 10, 18); context.fillText(`End ${values[values.length - 1].toFixed(3)}`, width - 95, 18);
}
function line(context, points, color, width) {
  context.strokeStyle = color; context.lineWidth = width; context.lineJoin = 'round'; context.lineCap = 'round'; context.beginPath();
  points.forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y)); context.stroke();
}
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }
window.addEventListener('resize', () => { if (!state.result) return; state.mode === 'forecast' ? renderForecast(state.result) : renderBacktest(state.result); });
checkHealth();
