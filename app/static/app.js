const state = {
  file: null,
  portfolioFiles: [],
  result: null,
  mode: 'forecast',
  busy: false,
  chartKind: null,
  chartData: null,
  language: localStorage.getItem('marketforge-language') || 'en'
};
const el = id => document.getElementById(id);
const fileInput = el('fileInput');
const dropZone = el('dropZone');

const translations = {
  en: { skip: 'Skip to research workspace', eyebrow: 'LOCAL-FIRST MARKET RESEARCH', heroTitle: 'Forecast, compare and stress-test.<br><span>Keep the evidence attached.</span>', heroLead: 'Import exchange candles or private CSV files, evaluate uncertainty, simulate portfolios, classify regimes and preserve reproducible experiments.', chooseCsv: 'Choose CSV', sample: 'Download sample', setup: 'Research setup' },
  bg: { skip: 'Към работното пространство', eyebrow: 'ЛОКАЛНО ПАЗАРНО ИЗСЛЕДВАНЕ', heroTitle: 'Прогнозирайте, сравнявайте и тествайте риск.<br><span>Запазете доказателствата.</span>', heroLead: 'Импортирайте борсови свещи или CSV файлове, измервайте несигурността, симулирайте портфейли и запазвайте възпроизводими експерименти.', chooseCsv: 'Избери CSV', sample: 'Изтегли пример', setup: 'Настройки на изследването' },
  es: { skip: 'Ir al espacio de investigación', eyebrow: 'INVESTIGACIÓN DE MERCADOS LOCAL', heroTitle: 'Pronostica, compara y prueba escenarios.<br><span>Conserva la evidencia.</span>', heroLead: 'Importa velas de mercados o archivos CSV, evalúa la incertidumbre, simula carteras y guarda experimentos reproducibles.', chooseCsv: 'Elegir CSV', sample: 'Descargar ejemplo', setup: 'Configuración de investigación' }
};

function applyLanguage(language) {
  const dictionary = translations[language] || translations.en;
  document.documentElement.lang = language;
  state.language = language;
  localStorage.setItem('marketforge-language', language);
  document.querySelectorAll('[data-i18n]').forEach(node => {
    const value = dictionary[node.dataset.i18n];
    if (value) node.innerHTML = value;
  });
}


async function loadConnectorOptions() {
  try {
    const data = await parseResponse(await fetch('/api/connectors'));
    const update = () => {
      const connector = data.connectors.find(item => item.id === el('exchange').value);
      if (!connector) return;
      const current = el('exchangeInterval').value;
      el('exchangeInterval').innerHTML = connector.intervals.map(interval => `<option value="${escapeHtml(interval)}">${escapeHtml(interval)}</option>`).join('');
      if (connector.intervals.includes(current)) el('exchangeInterval').value = current;
      else el('exchangeInterval').value = connector.intervals.includes('1h') ? '1h' : connector.intervals[0];
      el('exchangeLimit').max = connector.maximum_candles;
      el('exchangeLimit').value = Math.min(Number(el('exchangeLimit').value), connector.maximum_candles);
      el('exchangeSymbol').placeholder = connector.symbol_example;
      el('connectorNote').textContent = connector.note;
    };
    el('exchange').addEventListener('change', update);
    update();
  } catch {
    el('connectorNote').textContent = 'Connector metadata could not be loaded. CSV upload remains available.';
  }
}

async function checkHealth() {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    el('statusDot').classList.add('ready');
    const kronos = data.kronos?.installed ? 'Kronos installed' : 'Baselines ready';
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

function setBusy(busy) {
  state.busy = busy;
  document.querySelectorAll('button').forEach(button => {
    if (!['contrastButton', 'tableButton'].includes(button.id)) button.disabled = busy;
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

function begin(options = {}) {
  if (state.busy) return false;
  if (!options.multi && !state.file) {
    showError('Choose or import a CSV file first.');
    return false;
  }
  if (options.multi && state.portfolioFiles.length < 2) {
    showError('Select at least two asset CSV files for multi-asset research.');
    return false;
  }
  clearError();
  el('fallbackBox').classList.add('hidden');
  el('emptyState').classList.add('hidden');
  el('resultContent').classList.add('hidden');
  el('loadingState').classList.remove('hidden');
  setBusy(true);
  return true;
}

async function parseResponse(response) {
  let data;
  try { data = await response.json(); } catch { throw new Error('The server returned an unreadable response.'); }
  if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
  return data;
}

async function postFile(endpoint, settings = {}) {
  const form = new FormData();
  form.append('file', state.file);
  form.append('settings_json', JSON.stringify(settings));
  return parseResponse(await fetch(endpoint, { method: 'POST', body: form }));
}

async function postMulti(endpoint, settings = {}) {
  const form = new FormData();
  state.portfolioFiles.forEach(file => form.append('files', file));
  form.append('names_json', JSON.stringify(state.portfolioFiles.map(file => file.name.replace(/\.csv$/i, ''))));
  form.append('settings_json', JSON.stringify(settings));
  return parseResponse(await fetch(endpoint, { method: 'POST', body: form }));
}

function finish(data, title) {
  state.result = data;
  setBusy(false);
  el('loadingState').classList.add('hidden');
  el('resultContent').classList.remove('hidden');
  el('exportButton').classList.remove('hidden');
  el('resultsTitle').textContent = title;
  renderReport(data.data_report || null);
  renderNotes(data.notes || []);
  el('tradesWrap').classList.add('hidden');
  el('forecastEvidence').classList.add('hidden');
  el('detailWrap').classList.add('hidden');
  if (data.fallback) {
    el('fallbackBox').textContent = `Visible fallback: ${data.fallback.from} → ${data.fallback.to}. ${data.fallback.reason}`;
    el('fallbackBox').classList.remove('hidden');
  }
}

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
    metric('Forecast range', `${summary.lower_close} – ${summary.upper_close}`) +
    metric('Regime', summary.regime || data.regime?.regime || 'unknown') +
    metric('Calibration', summary.calibration || data.metadata?.calibration?.method || 'none') +
    metric('Future candles', summary.horizon) +
    metric('Scenarios', summary.paths);
  state.chartKind = 'forecast';
  state.chartData = { history: data.history, forecast: data.forecast };
  redrawChart();
  renderAccessibleForecast(data.history, data.forecast);
  showDetail('Regime assessment', data.regime || {});
}

function renderBacktest(data) {
  const metrics = data.metrics;
  const cls = metrics.total_return_percent >= 0 ? 'positive' : 'negative';
  el('metrics').innerHTML =
    metric('Simulated trades', metrics.trades) +
    metric('Strategy return', `${metrics.total_return_percent}%`, cls) +
    metric('Buy & hold', `${metrics.benchmark_return_percent}%`, metrics.benchmark_return_percent >= 0 ? 'positive' : 'negative') +
    metric('Excess return', `${metrics.excess_return_percent}%`, metrics.excess_return_percent >= 0 ? 'positive' : 'negative') +
    metric('Win rate', `${metrics.win_rate_percent}%`) +
    metric('Max drawdown', `${metrics.max_drawdown_percent}%`, 'negative') +
    metric('Profit factor', metrics.profit_factor) +
    metric('Exposure', `${metrics.exposure_percent}%`);
  state.chartKind = 'equity';
  state.chartData = data.equity_curve || [];
  redrawChart();
  renderAccessibleEquity(state.chartData);
  const forecast = data.forecast_metrics || {};
  el('forecastMetrics').innerHTML = metric('Forecasts tested', forecast.evaluations || 0) + metric('MAE', `${forecast.mae_percent || 0}%`) + metric('RMSE', `${forecast.rmse_percent || 0}%`) + metric('Direction accuracy', `${forecast.directional_accuracy_percent || 0}%`) + metric('80% coverage', `${forecast.interval_80_coverage_percent || 0}%`) + metric('Average width', `${forecast.average_interval_width_percent || 0}%`);
  el('forecastEvidence').classList.remove('hidden');
  const body = el('tradesBody');
  body.innerHTML = (data.trades || []).slice(-40).reverse().map(trade => `<tr><td>${escapeHtml(formatTimestamp(trade.signal_timestamp))}</td><td>${escapeHtml(formatTimestamp(trade.entry_timestamp))}</td><td>${escapeHtml(trade.side)}</td><td>${escapeHtml(trade.exit_reason)}</td><td>${escapeHtml(String(trade.predicted_return_percent))}%</td><td class="${trade.net_return_percent >= 0 ? 'positive' : 'negative'}">${escapeHtml(String(trade.net_return_percent))}%</td><td>${escapeHtml(String(trade.equity))}</td></tr>`).join('');
  el('tradesWrap').classList.toggle('hidden', !(data.trades || []).length);
  showDetail('Expanded diagnostics', { ...data.regime, exit_counts: data.exit_counts });
}

function renderPortfolio(data) {
  const metrics = data.metrics;
  el('metrics').innerHTML = metric('Final equity', metrics.final_equity) + metric('Total return', `${metrics.total_return_percent}%`, metrics.total_return_percent >= 0 ? 'positive' : 'negative') + metric('Max drawdown', `${metrics.max_drawdown_percent}%`, 'negative') + metric('Sharpe / √candle', metrics.sharpe_per_sqrt_candle) + metric('Sortino / √candle', metrics.sortino_per_sqrt_candle) + metric('Rebalances', metrics.rebalances) + metric('Turnover', `${metrics.total_turnover_percent}%`) + metric('Matched rows', data.analysis?.matched_rows || 0);
  state.chartKind = 'equity';
  state.chartData = data.equity_curve || [];
  redrawChart();
  renderAccessibleEquity(state.chartData);
  showDetail('Latest allocation weights', data.latest_weights || {});
  renderMultiReports(data.data_reports || {});
}

function renderMultiAsset(data) {
  el('metrics').innerHTML = metric('Assets', data.assets.length) + metric('Matched rows', data.matched_rows) + metric('Start', formatTimestamp(data.start)) + metric('End', formatTimestamp(data.end)) + metric('Diversification ratio', data.diversification_ratio_equal_weight);
  state.chartKind = null;
  state.chartData = null;
  clearCanvas('Correlation analysis is shown below.');
  showDetail('Correlation matrix', data.correlation || {});
  renderMultiReports(data.data_reports || {});
}

function renderLab(data, kind) {
  const entries = [];
  if (kind === 'regime') {
    entries.push(['Regime', data.regime], ['Confidence', data.confidence], ['Trend strength', `${data.trend_strength_percent}%`], ['Recent return', `${data.recent_return_percent}%`], ['Volatility percentile', `${data.volatility_percentile}%`], ['Down/up vol ratio', data.downside_upside_volatility_ratio]);
  } else if (kind === 'volatility') {
    entries.push(['Method', data.method], ['Per-candle volatility', `${data.per_candle_volatility_percent}%`], ['Horizon volatility', `${data.horizon_volatility_percent}%`], ['Annualised volatility', `${data.annualised_volatility_percent}%`], ['Horizon', data.horizon], ['Lookback', data.lookback]);
  } else {
    entries.push(['Stress scenarios', data.scenarios], ['Loss probability', `${data.loss_probability_percent}%`], ['Expected stressed return', `${data.expected_stressed_return_percent}%`], ['95% VaR', `${data.value_at_risk_95_percent}%`], ['95% expected shortfall', `${data.expected_shortfall_95_percent}%`], ['Average loss', `${data.average_loss_percent}%`]);
  }
  el('metrics').innerHTML = entries.map(([label, value]) => metric(label, value, typeof value === 'number' && value < 0 ? 'negative' : '')).join('');
  state.chartKind = null;
  state.chartData = null;
  clearCanvas(`${kind[0].toUpperCase()}${kind.slice(1)} analysis complete.`);
  showDetail(kind === 'regime' ? 'Regime evidence' : kind === 'volatility' ? 'Volatility components' : 'Stress distribution', data.component_estimates_percent || data.return_percentiles || data);
}

function renderRegistry(data) {
  el('metrics').innerHTML = metric('Registered models', data.models.length) + metric('Active models', data.models.filter(model => model.active).length);
  clearCanvas('Model registry loaded.');
  showDetail('Model registry', data.models.map(model => `${model.name} · ${model.family} · ${model.version} · ${model.revision}`));
}

function showDetail(title, value) {
  el('detailTitle').textContent = title;
  const content = el('detailContent');
  if (Array.isArray(value)) {
    content.innerHTML = value.map(item => `<div>• ${escapeHtml(typeof item === 'string' ? item : JSON.stringify(item))}</div>`).join('');
  } else if (value && typeof value === 'object') {
    content.innerHTML = Object.entries(value).map(([key, item]) => `<div class="report-item"><span>${escapeHtml(key.replaceAll('_', ' '))}</span><b>${escapeHtml(typeof item === 'object' ? JSON.stringify(item) : String(item))}</b></div>`).join('');
  } else {
    content.textContent = String(value || 'No detail available.');
  }
  el('detailWrap').classList.remove('hidden');
}

function renderReport(report) {
  if (!report) { el('dataReport').innerHTML = ''; return; }
  const entries = [['Quality score', `${report.quality_score}/100`], ['Data fingerprint', report.data_fingerprint], ['Rows received', report.rows_received], ['Rows kept', report.rows_kept], ['Invalid removed', report.invalid_rows_removed], ['Duplicates removed', report.duplicates_removed], ['Candles repaired', report.candles_repaired], ['Irregular intervals', report.irregular_intervals], ['Estimated missing', report.estimated_missing_candles], ['Detected interval', report.inferred_interval], ['Outlier moves', report.outlier_returns]];
  el('dataReport').innerHTML = entries.map(([label, value]) => `<div class="report-item"><span>${escapeHtml(label)}</span><b>${escapeHtml(String(value))}</b></div>`).join('') + (report.warnings || []).map(warning => `<div class="warning">⚠ ${escapeHtml(warning)}</div>`).join('');
}

function renderMultiReports(reports) {
  const rows = Object.entries(reports).map(([name, report]) => `<div class="report-item"><span>${escapeHtml(name)}</span><b>${escapeHtml(`${report.quality_score}/100 · ${report.rows_kept} rows`)}</b></div>`).join('');
  el('dataReport').innerHTML = rows || '<div>No data-quality reports.</div>';
}
function renderNotes(notes) { el('notes').innerHTML = notes.map(note => `<div>• ${escapeHtml(note)}</div>`).join(''); }
function formatTimestamp(value) { return String(value || '').replace('T', ' ').replace('Z', ' UTC'); }

function selectedRange(length) {
  const value = el('chartRange').value;
  return value === 'all' ? length : Math.min(length, Number(value));
}

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
function drawGrid(context, width, height) { context.strokeStyle = 'rgba(181,255,223,.08)'; context.lineWidth = 1; for (let i = 1; i < 6; i += 1) { const y = i * height / 6; context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke(); } }
function clearCanvas(message) { const { context, width, height } = prepCanvas(); drawGrid(context, width, height); context.fillStyle = '#91aaa0'; context.font = '16px system-ui'; context.fillText(message, 30, height / 2); }
function redrawChart() { if (state.chartKind === 'forecast') drawForecastChart(state.chartData.history, state.chartData.forecast); else if (state.chartKind === 'equity') drawEquityChart(state.chartData); else clearCanvas('No time-series chart for this result.'); }
function drawForecastChart(history, forecast) {
  const limit = selectedRange(history.length + forecast.length);
  const historyLimit = Math.max(20, limit - forecast.length);
  const visibleHistory = history.slice(-historyLimit);
  const { context, width, height } = prepCanvas(); drawGrid(context, width, height);
  const historical = visibleHistory.map(row => Number(row.close)); const median = forecast.map(row => Number(row.close)); const lower = forecast.map(row => Number(row.lower_close)); const upper = forecast.map(row => Number(row.upper_close));
  const all = [...historical, ...lower, ...upper].filter(Number.isFinite); if (!all.length) return clearCanvas('No chart data.');
  const min = Math.min(...all), max = Math.max(...all), padding = (max - min || 1) * .08;
  const y = value => height - 26 - (value - (min - padding)) / (max - min + 2 * padding) * (height - 52); const total = historical.length + median.length; const x = index => 18 + index / Math.max(total - 1, 1) * (width - 36); const split = historical.length - 1;
  context.fillStyle = 'rgba(111,255,193,.09)'; context.beginPath(); forecast.forEach((_, index) => index ? context.lineTo(x(historical.length + index), y(upper[index])) : context.moveTo(x(historical.length + index), y(upper[index]))); for (let index = forecast.length - 1; index >= 0; index -= 1) context.lineTo(x(historical.length + index), y(lower[index])); context.closePath(); context.fill();
  line(context, historical.map((value, index) => [x(index), y(value)]), '#91aaa0', 1.6); line(context, [[x(split), y(historical[historical.length - 1])], ...median.map((value, index) => [x(historical.length + index), y(value)])], '#6fffc1', 2.4);
  context.setLineDash([5, 5]); context.strokeStyle = 'rgba(255,255,255,.24)'; context.beginPath(); context.moveTo(x(split), 10); context.lineTo(x(split), height - 10); context.stroke(); context.setLineDash([]); context.fillStyle = '#91aaa0'; context.font = '12px system-ui'; context.fillText(min.toFixed(4), 8, height - 9); context.fillText(max.toFixed(4), 8, 16);
}
function drawEquityChart(equityCurve) {
  const visible = equityCurve.slice(-selectedRange(equityCurve.length));
  const { context, width, height } = prepCanvas(); drawGrid(context, width, height); const values = visible.map(point => Number(point.equity)).filter(Number.isFinite);
  if (values.length < 2) { context.fillStyle = '#91aaa0'; context.font = '16px system-ui'; context.fillText('Not enough completed observations.', 30, height / 2); return; }
  const min = Math.min(...values), max = Math.max(...values), padding = (max - min || .02) * .15; const y = value => height - 25 - (value - (min - padding)) / (max - min + 2 * padding) * (height - 50); const x = index => 18 + index / Math.max(values.length - 1, 1) * (width - 36); line(context, values.map((value, index) => [x(index), y(value)]), '#6fffc1', 2.4); context.fillStyle = '#91aaa0'; context.font = '12px system-ui'; context.fillText(`Start ${values[0].toFixed(3)}`, 10, 18); context.fillText(`End ${values[values.length - 1].toFixed(3)}`, width - 100, 18);
}
function line(context, points, color, width) { context.strokeStyle = color; context.lineWidth = width; context.lineJoin = 'round'; context.lineCap = 'round'; context.beginPath(); points.forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y)); context.stroke(); }

function renderAccessibleForecast(history, forecast) {
  const rows = [...history.slice(-25).map(row => ({ ...row, type: 'history' })), ...forecast.slice(0, 50).map(row => ({ ...row, type: 'forecast' }))];
  el('accessibleChart').innerHTML = `<table><caption>Accessible forecast data</caption><thead><tr><th>Type</th><th>Timestamp</th><th>Close</th><th>Lower</th><th>Upper</th></tr></thead><tbody>${rows.map(row => `<tr><td>${escapeHtml(row.type)}</td><td>${escapeHtml(formatTimestamp(row.timestamp))}</td><td>${escapeHtml(row.close)}</td><td>${escapeHtml(row.lower_close || '')}</td><td>${escapeHtml(row.upper_close || '')}</td></tr>`).join('')}</tbody></table>`;
}
function renderAccessibleEquity(points) {
  el('accessibleChart').innerHTML = `<table><caption>Accessible equity curve</caption><thead><tr><th>Timestamp</th><th>Equity</th></tr></thead><tbody>${points.slice(-250).map(point => `<tr><td>${escapeHtml(formatTimestamp(point.timestamp))}</td><td>${escapeHtml(point.equity)}</td></tr>`).join('')}</tbody></table>`;
}
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

fileInput.addEventListener('change', event => setFile(event.target.files[0]));
dropZone.addEventListener('click', () => fileInput.click());
['dragenter', 'dragover'].forEach(name => dropZone.addEventListener(name, event => { event.preventDefault(); dropZone.classList.add('drag'); }));
['dragleave', 'drop'].forEach(name => dropZone.addEventListener(name, event => { event.preventDefault(); dropZone.classList.remove('drag'); }));
dropZone.addEventListener('drop', event => setFile(event.dataTransfer.files[0]));
el('portfolioFiles').addEventListener('change', event => { state.portfolioFiles = [...event.target.files]; clearError(); });
el('paths').addEventListener('input', event => { el('pathsValue').textContent = event.target.value; });

for (const tab of document.querySelectorAll('.tab')) {
  tab.addEventListener('click', () => {
    for (const item of document.querySelectorAll('.tab')) { item.classList.remove('active'); item.setAttribute('aria-selected', 'false'); }
    tab.classList.add('active'); tab.setAttribute('aria-selected', 'true'); state.mode = tab.dataset.tab;
    document.querySelectorAll('.mode-controls').forEach(group => group.classList.add('hidden'));
    el(`${state.mode}Controls`).classList.remove('hidden');
  });
}

el('importButton').addEventListener('click', async () => {
  if (state.busy) return;
  setBusy(true); clearError();
  try {
    const response = await fetch('/api/import-market-data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ exchange: el('exchange').value, symbol: el('exchangeSymbol').value.trim(), interval: el('exchangeInterval').value, limit: Number(el('exchangeLimit').value) }) });
    const data = await parseResponse(response);
    const name = `${data.metadata.connector.id}-${data.metadata.symbol}-${data.metadata.interval}.csv`;
    setFile(new File([data.csv], name, { type: 'text/csv' }));
    state.result = data; el('resultsTitle').textContent = `Imported ${data.metadata.symbol} from ${data.metadata.connector.name}`; el('emptyState').classList.add('hidden'); el('resultContent').classList.remove('hidden'); renderReport(data.report); renderNotes([data.metadata.connector.note, `${data.metadata.received_rows} candles imported and normalised.`]); el('metrics').innerHTML = metric('Exchange', data.metadata.connector.name) + metric('Symbol', data.metadata.symbol) + metric('Interval', data.metadata.interval) + metric('Rows', data.metadata.received_rows) + metric('Quality', `${data.report.quality_score}/100`); clearCanvas('Data imported. Choose a research mode to continue.');
  } catch (error) { showError(error.message); } finally { setBusy(false); }
});

el('forecastButton').addEventListener('click', async () => { if (!begin()) return; try { const data = await postFile('/api/forecast', { engine: el('engine').value, baseline_model: el('baselineModel').value, model_size: el('modelSize').value, horizon: Number(el('horizon').value), lookback: Number(el('lookback').value), paths: Number(el('paths').value), block_size: Number(el('blockSize').value), kronos_samples: Number(el('kronosSamples').value), calibration: el('calibration').value }); finish(data, `Forecast · ${data.engine}`); renderForecast(data); } catch (error) { showError(error.message); } });

el('backtestButton').addEventListener('click', async () => { if (!begin()) return; try { const data = await postFile('/api/backtest', { baseline_model: el('btModel').value, horizon: Number(el('btHorizon').value), lookback: Number(el('btLookback').value), step: Number(el('btStep').value), block_size: Number(el('btBlockSize').value), threshold_percent: Number(el('threshold').value), fee_percent: Number(el('fee').value), slippage_percent: Number(el('slippage').value), position_size_percent: Number(el('positionSize').value), direction: el('direction').value, execution_delay: Number(el('executionDelay').value), stop_loss_percent: nullableNumber('stopLoss'), take_profit_percent: nullableNumber('takeProfit'), allow_overlap: el('allowOverlap').checked, calibration: el('calibration').value }); finish(data, 'Evidence-aware walk-forward backtest'); renderBacktest(data); } catch (error) { showError(error.message); } });

el('portfolioButton').addEventListener('click', async () => { if (!begin({ multi: true })) return; try { const data = await postMulti('/api/portfolio', { allocation: el('allocation').value, lookback: Number(el('portfolioLookback').value), rebalance_every: Number(el('rebalanceEvery').value), max_weight_percent: Number(el('maxWeight').value), fee_percent: Number(el('portfolioFee').value) }); finish(data, 'Portfolio-level simulation'); renderPortfolio(data); } catch (error) { showError(error.message); } });
el('multiAssetButton').addEventListener('click', async () => { if (!begin({ multi: true })) return; try { const data = await postMulti('/api/multi-asset'); finish(data, 'Multi-asset analysis'); renderMultiAsset(data); } catch (error) { showError(error.message); } });

el('regimeButton').addEventListener('click', async () => { if (!begin()) return; try { const data = await postFile('/api/regime'); finish(data, 'Market-regime classification'); renderLab(data, 'regime'); } catch (error) { showError(error.message); } });
el('volatilityButton').addEventListener('click', async () => { if (!begin()) return; try { const data = await postFile('/api/volatility', { method: el('volMethod').value, horizon: Number(el('volHorizon').value), lookback: Number(el('volLookback').value) }); finish(data, 'Volatility forecast'); renderLab(data, 'volatility'); } catch (error) { showError(error.message); } });
el('stressButton').addEventListener('click', async () => { if (!begin()) return; try { const data = await postFile('/api/stress', { price_shock_percent: Number(el('shock').value), volatility_multiplier: Number(el('volMultiplier').value), liquidity_cost_percent: Number(el('liquidityCost').value) }); finish(data, 'Scenario stress test'); renderLab(data, 'stress'); } catch (error) { showError(error.message); } });

el('saveProjectButton').addEventListener('click', async () => { const name = el('projectName').value.trim(); if (!name) return showError('Enter a project name first.'); try { const response = await fetch('/api/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, description: 'Saved from the MarketForge browser studio.', settings: { mode: state.mode }, dataset_fingerprints: state.result?.data_report?.data_fingerprint ? [state.result.data_report.data_fingerprint] : [], language: state.language }) }); const data = await parseResponse(response); showDetail('Project saved', data); } catch (error) { showError(error.message); } });

el('saveExperimentButton').addEventListener('click', async () => { if (!state.result) return showError('Run an analysis before saving an experiment.'); const name = el('projectName').value.trim() || `${state.mode} experiment`; try { const response = await fetch('/api/experiments', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, kind: ['forecast', 'backtest', 'portfolio'].includes(state.mode) ? state.mode : 'stress', dataset_fingerprint: state.result.data_report?.data_fingerprint || '', settings: state.result.settings || state.result.metadata || {}, metrics: state.result.metrics || state.result.summary || {}, result: state.result, tags: [state.mode, 'browser'] }) }); const data = await parseResponse(response); showDetail('Experiment saved', { id: data.id, result_hash: data.result_hash, created_at: data.created_at }); } catch (error) { showError(error.message); } });

el('projectsButton').addEventListener('click', async () => { try { const data = await parseResponse(await fetch('/api/projects')); finish(data, 'Saved research projects'); el('metrics').innerHTML = metric('Saved projects', data.projects.length); clearCanvas('Saved projects loaded.'); showDetail('Projects', data.projects.map(project => `${project.id} · ${project.name} · ${project.updated_at}`)); } catch (error) { showError(error.message); } });

el('experimentsButton').addEventListener('click', async () => { try { const data = await parseResponse(await fetch('/api/experiments?limit=50')); finish(data, 'Experiment history'); el('metrics').innerHTML = metric('Experiments', data.experiments.length); clearCanvas('Experiment history loaded.'); showDetail('Recent experiments', data.experiments.map(item => `${item.id} · ${item.kind} · ${item.name} · ${item.result_hash.slice(0, 12)}`)); } catch (error) { showError(error.message); } });

el('modelsButton').addEventListener('click', async () => { try { const data = await parseResponse(await fetch('/api/models')); finish(data, 'Local model registry'); renderRegistry(data); } catch (error) { showError(error.message); } });

el('reportButton').addEventListener('click', async () => { if (!state.result) return showError('Run an analysis before creating a report.'); try { const response = await fetch('/api/reports', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ template: el('reportTemplate').value, title: el('projectName').value.trim() || 'MarketForge AI Report', result: state.result, format: 'markdown' }) }); if (!response.ok) throw new Error('The report could not be generated.'); const blob = await response.blob(); downloadBlob(blob, 'marketforge-report.md'); } catch (error) { showError(error.message); } });

el('exportButton').addEventListener('click', () => { if (state.result) downloadBlob(new Blob([JSON.stringify(state.result, null, 2)], { type: 'application/json' }), `marketforge-${state.mode}-result.json`); });
el('chartRange').addEventListener('change', redrawChart);
el('tableButton').addEventListener('click', () => { const hidden = el('accessibleChart').classList.toggle('hidden'); el('tableButton').textContent = hidden ? 'Show data table' : 'Hide data table'; el('tableButton').setAttribute('aria-expanded', String(!hidden)); });
el('contrastButton').addEventListener('click', () => { const active = document.body.classList.toggle('high-contrast'); el('contrastButton').setAttribute('aria-pressed', String(active)); localStorage.setItem('marketforge-contrast', active ? '1' : '0'); });
el('languageSelect').value = state.language; el('languageSelect').addEventListener('change', event => applyLanguage(event.target.value));
window.addEventListener('resize', () => { if (state.chartData) redrawChart(); });

function downloadBlob(blob, filename) { const anchor = document.createElement('a'); const url = URL.createObjectURL(blob); anchor.href = url; anchor.download = filename; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 0); }

if (localStorage.getItem('marketforge-contrast') === '1') { document.body.classList.add('high-contrast'); el('contrastButton').setAttribute('aria-pressed', 'true'); }
applyLanguage(state.language);
loadConnectorOptions();
checkHealth();
