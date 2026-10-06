const booksBody = document.querySelector('#books-body');
const inventoryBody = document.querySelector('#inventory-body');
const selectedIds = new Set();
let currentBooks = [];
let toastTimer;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

function showToast(message) {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 3500);
}

function updateSelection() {
  const amount = selectedIds.size;
  document.querySelector('#selection-count').textContent = `${amount} seleccionados · mínimo 4`;
  document.querySelector('#print-button').disabled = amount < 4;
  const latest = [...selectedIds].at(-1);
  const book = currentBooks.find(item => item.id === latest) || currentBooks.find(item => selectedIds.has(item.id));
  renderFiche(book);
}

function renderFiche(book) {
  const content = document.querySelector('#fiche-content');
  const record = document.querySelector('#preview-record');
  if (!book) {
    content.innerHTML = '<p class="fiche-placeholder">Selecciona un libro para consultar su descripción bibliográfica.</p>';
    record.textContent = 'Sin selección';
    return;
  }
  content.innerHTML = `
    <div class="fiche-author">${escapeHtml(book.autor || 'Autor no registrado')}</div>
    <div class="fiche-title">${escapeHtml(book.titulo)}</div>
    <div class="fiche-pub">${escapeHtml(book.edicion || 'Edición no indicada')}. ${escapeHtml(book.editorial || 'Editorial no registrada')}, ${escapeHtml(book.anio || 's. f.')}</div>
    <div class="fiche-detail">${escapeHtml(book.paginas || '—')} páginas · ${escapeHtml(book.idioma || 'Idioma no indicado')}<br>ISBN ${escapeHtml(book.isbn || 'No registrado')}<br>Cota ${escapeHtml(book.cota || 'Sin cota')}<br>${escapeHtml(book.sistema || 'Sin sistema')} ${escapeHtml(book.codigo_clasificacion || '')}</div>`;
  record.textContent = book.numero_registro;
}

function renderBooks(books) {
  currentBooks = books;
  const availableIds = new Set(books.map(book => book.id));
  for (const id of selectedIds) if (!availableIds.has(id)) selectedIds.delete(id);
  document.querySelector('#book-count').textContent = `${books.length} cédulas catalogadas`;
  if (!books.length) {
    booksBody.innerHTML = '<tr><td colspan="5" class="empty-cell">No hay libros catalogados que coincidan con la búsqueda.</td></tr>';
    updateSelection();
    return;
  }
  booksBody.innerHTML = books.map(book => `
    <tr data-book-id="${book.id}">
      <td class="check-col"><input class="select-book" type="checkbox" aria-label="Seleccionar ${escapeHtml(book.titulo)}" ${selectedIds.has(book.id) ? 'checked' : ''}></td>
      <td><span class="record-number">${escapeHtml(book.numero_registro)}</span></td>
      <td><span class="book-title">${escapeHtml(book.titulo)}</span><span class="book-author">${escapeHtml(book.autor || 'Autor no registrado')}</span></td>
      <td><span class="area-tag">${escapeHtml(book.area || 'Sin área temática')}</span></td>
      <td><span class="shelf-code">${escapeHtml(book.cota || 'Sin cota')}</span></td>
    </tr>`).join('');
  updateSelection();
}

function renderInventory(groups) {
  const total = groups.reduce((sum, group) => sum + group.total, 0);
  document.querySelector('#inventory-total').textContent = total;
  if (!groups.length) {
    inventoryBody.innerHTML = '<tr><td colspan="5" class="empty-cell">No hay registros activos en el inventario.</td></tr>';
    return;
  }
  inventoryBody.innerHTML = groups.map(group => {
    const cataloguedWidth = group.total ? (group.catalogados / group.total) * 100 : 0;
    const pendingWidth = group.total ? (group.pendientes / group.total) * 100 : 0;
    return `<tr>
      <td>${escapeHtml(group.area)}</td><td>${escapeHtml(group.sistema)}</td>
      <td>${group.catalogados}</td><td>${group.pendientes}</td>
      <td class="quantity-cell"><div class="quantity-line"><span>${group.total}</span><span class="muted">libros</span></div>
        <div class="quantity-track"><span class="quantity-catalogued" style="width:${cataloguedWidth}%"></span><span class="quantity-pending" style="width:${pendingWidth}%"></span></div>
      </td></tr>`;
  }).join('');
}

async function loadBooks(query = '') {
  booksBody.innerHTML = '<tr><td colspan="5" class="empty-cell">Actualizando el fichero…</td></tr>';
  try {
    const response = await fetch(`/api/books?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('No fue posible consultar los libros.');
    renderBooks(await response.json());
  } catch (error) {
    booksBody.innerHTML = `<tr><td colspan="5" class="empty-cell">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function loadData() {
  try {
    const [summaryResponse, inventoryResponse] = await Promise.all([
      fetch('/api/summary'), fetch('/api/inventory'),
    ]);
    if (!summaryResponse.ok || !inventoryResponse.ok) throw new Error('No fue posible cargar el resumen.');
    const [summary, inventory] = await Promise.all([summaryResponse.json(), inventoryResponse.json()]);
    document.querySelector('#stat-total').textContent = summary.total;
    document.querySelector('#stat-catalogued').textContent = summary.catalogados;
    document.querySelector('#stat-pending').textContent = summary.pendientes;
    document.querySelector('#sidebar-total').textContent = `${summary.total} registros activos`;
    document.querySelector('#mode-badge').textContent = summary.demo ? 'Datos de demostración' : 'Base conectada';
    document.querySelector('#today-label').textContent = new Intl.DateTimeFormat('es', { dateStyle: 'long' }).format(new Date());
    renderInventory(inventory);
    await loadBooks();
  } catch (error) {
    showToast(error.message);
    booksBody.innerHTML = '<tr><td colspan="5" class="empty-cell">No hay conexión con el servidor de prueba.</td></tr>';
    inventoryBody.innerHTML = '<tr><td colspan="5" class="empty-cell">No se pudo cargar el inventario.</td></tr>';
  }
}

let searchTimer;
document.querySelector('#search').addEventListener('input', event => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadBooks(event.target.value), 180);
});

booksBody.addEventListener('change', event => {
  if (!event.target.matches('.select-book')) return;
  const id = Number(event.target.closest('tr').dataset.bookId);
  if (event.target.checked) selectedIds.add(id);
  else selectedIds.delete(id);
  updateSelection();
});

document.querySelector('#print-button').addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const response = await fetch('/api/fichas', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [...selectedIds] }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'No fue posible generar las cédulas.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'cedulas_libros.pdf';
    link.click();
    URL.revokeObjectURL(url);
    showToast('Cédulas listas: cuatro fichas por hoja A4.');
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = selectedIds.size < 4;
  }
});

const selectedDistribution = new Set();
const selectedLabels = new Set();
let currentPending = [];
let currentLocations = [];
let currentLibraries = [];
let selectedLocationId = null;

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const type = response.headers.get('content-type') || '';
  const result = type.includes('application/json') ? await response.json() : null;
  if (!response.ok) throw new Error(result?.error || result?.message || 'No fue posible completar la solicitud.');
  return result;
}

function jsonOptions(method, body) {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}

async function downloadPost(url, body, filename) {
  const response = await fetch(url, jsonOptions('POST', body));
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || error.message || 'No fue posible generar el documento.');
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

function showScreen(name) {
  const screen = document.querySelector(`#screen-${name}`);
  if (!screen) return;
  document.querySelectorAll('.screen').forEach(item => item.classList.toggle('active-screen', item === screen));
  document.querySelectorAll('.nav-link').forEach(item => item.classList.toggle('active', item.dataset.screen === name));
  const nav = document.querySelector(`.nav-link[data-screen="${name}"]`);
  document.querySelector('#current-module').textContent = nav?.textContent.trim().replace(/^\d+\s*/, '') || 'Biblioteca';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function statusLabel(value) {
  return ({ recibido: 'Recibido', en_catalogacion: 'En catalogación', catalogado: 'Catalogado', distribuido: 'Distribuido', prestado: 'Prestado' })[value] || value || 'Sin estado';
}

function bookTitle(book) {
  return `<span class="book-title">${escapeHtml(book.titulo)}</span><span class="book-author">${escapeHtml(book.autor || 'Autor no registrado')}</span>`;
}

async function loadDashboard() {
  const data = await requestJson('/api/dashboard');
  const summary = data.summary;
  document.querySelector('#dashboard-stats').innerHTML = `
    <article class="stat-item stat-total"><span class="stat-label">LIBROS ACTIVOS</span><strong>${summary.total}</strong><span>En el registro central</span></article>
    <article class="stat-item stat-catalogued"><span class="stat-label">CATALOGADOS</span><strong>${summary.estados.catalogado || 0}</strong><span>Con cota asignada</span></article>
    <article class="stat-item stat-pending"><span class="stat-label">PENDIENTES</span><strong>${summary.catalogacion.pendientes}</strong><span>Por catalogar</span></article>`;
  document.querySelector('#sidebar-total').textContent = `${summary.total} registros activos`;
}

async function loadReception(query = '') {
  const rows = await requestJson(`/api/recepcion?q=${encodeURIComponent(query)}`);
  const body = document.querySelector('#reception-body');
  body.innerHTML = rows.length ? rows.map(book => `<tr><td><span class="record-number">${escapeHtml(book.numero_registro)}</span></td><td>${bookTitle(book)}</td><td>${escapeHtml(statusLabel(book.estado))}</td><td>${escapeHtml(book.procedencia)}</td></tr>`).join('') : '<tr><td colspan="4" class="empty-cell">No hay ingresos que coincidan.</td></tr>';
}

async function loadCatalog(query = '') {
  currentPending = await requestJson(`/api/catalogacion?q=${encodeURIComponent(query)}`);
  document.querySelector('#pending-count').textContent = `${currentPending.length} pendientes`;
  document.querySelector('#catalog-body').innerHTML = currentPending.length ? currentPending.map(book => `<tr data-id="${book.id}"><td><input class="selection-checkbox pending-choice" type="radio" name="pending-book" aria-label="Seleccionar ${escapeHtml(book.titulo)}"></td><td>${bookTitle(book)}</td><td>${escapeHtml(book.isbn || '—')}</td><td>${escapeHtml(book.numero_registro)}</td></tr>`).join('') : '<tr><td colspan="4" class="empty-cell">No hay libros pendientes de catalogación.</td></tr>';
}

async function loadDistribution(query = '') {
  const data = await requestJson(`/api/distribucion?q=${encodeURIComponent(query)}`);
  currentLibraries = data.libraries;
  const librarySelect = document.querySelector('#distribution-library');
  const previous = librarySelect.value;
  librarySelect.innerHTML = data.libraries.filter(item => !item.nombre.includes('Biblioteca Central')).map(item => `<option value="${item.id}">${escapeHtml(item.nombre)}</option>`).join('');
  if ([...librarySelect.options].some(option => option.value === previous)) librarySelect.value = previous;
  const body = document.querySelector('#distribution-body');
  body.innerHTML = data.books.length ? data.books.map(book => `<tr data-id="${book.id}"><td><input class="selection-checkbox distribution-choice" type="checkbox" ${selectedDistribution.has(book.id) ? 'checked' : ''} aria-label="Seleccionar ${escapeHtml(book.titulo)}"></td><td>${bookTitle(book)}</td><td class="shelf-code">${escapeHtml(book.cota || 'Sin cota')}</td><td>${escapeHtml(book.numero_registro)}</td></tr>`).join('') : '<tr><td colspan="4" class="empty-cell">No hay libros catalogados disponibles.</td></tr>';
  document.querySelector('#distribution-selected').textContent = `${selectedDistribution.size} seleccionados`;
  document.querySelector('#shipments-body').innerHTML = data.shipments.length ? data.shipments.map(item => `<tr><td>${escapeHtml(item.codigo)}</td><td>${escapeHtml(item.destino)}</td><td>${escapeHtml(item.fecha)}</td><td>${item.cantidad}</td><td><button class="mini-button shipment-document" data-code="${escapeHtml(item.codigo)}" type="button">PDF</button></td></tr>`).join('') : '<tr><td colspan="5" class="empty-cell">Aún no hay envíos.</td></tr>';
}

async function loadLocations(query = '') {
  const estado = document.querySelector('#location-state').value;
  currentLocations = await requestJson(`/api/ubicacion?q=${encodeURIComponent(query)}&estado=${encodeURIComponent(estado)}`);
  document.querySelector('#location-body').innerHTML = currentLocations.length ? currentLocations.map(book => `<tr data-id="${book.id}"><td><input class="selection-checkbox location-choice" type="radio" name="location-book" aria-label="Seleccionar ${escapeHtml(book.titulo)}"></td><td>${escapeHtml(book.numero_registro)}</td><td>${bookTitle(book)}</td><td>${escapeHtml(statusLabel(book.estado))}</td><td>${escapeHtml(book.biblioteca)}</td><td>${escapeHtml([book.sala, book.estante].filter(Boolean).join(' / ') || book.tipo_ubicacion)}</td><td>${escapeHtml(book.ultimo_movimiento)}</td></tr>`).join('') : '<tr><td colspan="7" class="empty-cell">No se encontraron libros.</td></tr>';
}

async function loadLabels(query = '') {
  const books = await requestJson(`/api/books?q=${encodeURIComponent(query)}`);
  document.querySelector('#labels-body').innerHTML = books.length ? books.map(book => `<tr data-id="${book.id}"><td><input class="selection-checkbox label-choice" type="checkbox" ${selectedLabels.has(book.id) ? 'checked' : ''} aria-label="Seleccionar ${escapeHtml(book.titulo)}"></td><td>${escapeHtml(book.numero_registro)}</td><td>${bookTitle(book)}</td><td class="shelf-code">${escapeHtml(book.cota || 'Sin cota')}</td></tr>`).join('') : '<tr><td colspan="4" class="empty-cell">No hay libros catalogados.</td></tr>';
  document.querySelector('#labels-selected').textContent = `${selectedLabels.size} seleccionados`;
}

async function loadLibraries() {
  const libraries = await requestJson('/api/libraries');
  document.querySelector('#libraries-body').innerHTML = libraries.map(item => `<tr><td>${escapeHtml(item.nombre)}</td><td>${escapeHtml(item.direccion)}</td><td>${escapeHtml(item.encargado)}</td><td>${escapeHtml([item.telefono, item.email].filter(Boolean).join(' · '))}</td><td>${item.activa ? 'Activa' : 'Inactiva'}</td><td>${item.activa && !item.nombre.includes('Biblioteca Central') ? `<button class="mini-button deactivate-library" data-id="${item.id}" type="button">Desactivar</button>` : ''}</td></tr>`).join('') || '<tr><td colspan="6" class="empty-cell">No hay bibliotecas registradas.</td></tr>';
  const options = libraries.filter(item => item.activa).map(item => `<option value="${item.id}">${escapeHtml(item.nombre)}</option>`).join('');
  document.querySelector('#location-library').innerHTML = options;
}

async function loadUsers() {
  const users = await requestJson('/api/users');
  document.querySelector('#users-body').innerHTML = users.map(user => `<tr><td>${escapeHtml(user.username)}</td><td>${escapeHtml(user.nombre)}</td><td>${escapeHtml(user.rol)}</td><td>${user.activo ? 'Activo' : 'Inactivo'}</td><td><button class="mini-button toggle-user" data-id="${user.id}" data-active="${user.activo}" type="button">${user.activo ? 'Desactivar' : 'Activar'}</button></td></tr>`).join('') || '<tr><td colspan="5" class="empty-cell">No hay usuarios disponibles.</td></tr>';
}

async function loadReports() {
  const params = new URLSearchParams();
  const desde = document.querySelector('#report-from').value;
  const hasta = document.querySelector('#report-to').value;
  if (desde) params.set('desde', desde);
  if (hasta) params.set('hasta', hasta);
  const data = await requestJson(`/api/reportes?${params}`);
  const summary = data.summary;
  document.querySelector('#report-summary').innerHTML = `
    <div><strong>${summary.total}</strong><span>Registros del período</span></div>
    <div><strong>${summary.catalogacion.catalogados}</strong><span>Catalogados en rango · ${summary.catalogacion.pendientes} pendientes actuales</span></div>
    <div><strong>${summary.distribucion.reduce((total, row) => total + row[1], 0)}</strong><span>Libros distribuidos</span></div>`;
  document.querySelector('#report-count').textContent = `${data.inventory.length} libros`;
  document.querySelector('#report-body').innerHTML = data.inventory.length ? data.inventory.map(row => `<tr><td>${escapeHtml(row.registro)}</td><td>${bookTitle(row)}</td><td>${escapeHtml(statusLabel(row.estado))}</td><td class="shelf-code">${escapeHtml(row.cota)}</td><td>${escapeHtml(row.biblioteca)}</td><td>${escapeHtml([row.sala, row.estante].filter(Boolean).join(' / ') || row.tipo_ubicacion)}</td></tr>`).join('') : '<tr><td colspan="6" class="empty-cell">No hay registros para este período.</td></tr>';
}

async function initializeModules() {
  const hoy = new Date();
  const inicio = new Date(hoy);
  inicio.setDate(hoy.getDate() - 30);
  document.querySelector('#report-from').value = inicio.toISOString().slice(0, 10);
  document.querySelector('#report-to').value = hoy.toISOString().slice(0, 10);
  await loadData();
  const tasks = [loadDashboard(), loadReception(), loadCatalog(), loadDistribution(), loadLocations(), loadLabels(), loadLibraries(), loadUsers(), loadReports()];
  const results = await Promise.allSettled(tasks);
  const failure = results.find(result => result.status === 'rejected');
  if (failure) showToast(failure.reason.message);
}

function showPasswordChange() {
  document.body.classList.remove('authenticated');
  document.querySelector('#web-login-panel').hidden = true;
  document.querySelector('#web-password-panel').hidden = false;
  document.querySelector('#web-gate').hidden = false;
}

async function startAuthenticatedApp(user) {
  if (user.debe_cambiar_clave) {
    showPasswordChange();
    return;
  }
  document.querySelector('#web-gate').hidden = true;
  document.querySelector('#web-login-panel').hidden = false;
  document.querySelector('#web-password-panel').hidden = true;
  document.body.classList.add('authenticated');
  document.querySelector('#web-user-name').textContent = `${user.nombre || user.username} · ${user.rol}`;
  document.querySelector('#web-session-notice').textContent = user.demo ? 'Base de demostración' : 'Base bibliotecaria';
  document.querySelector('#mode-badge').textContent = user.demo ? 'Datos de demostración' : 'Base conectada';
  document.querySelector('#demo-disclaimer').hidden = !user.demo;
  document.querySelectorAll('.admin-link, .admin-screen').forEach(item => {
    item.hidden = user.rol !== 'admin';
  });
  try {
    await initializeModules();
  } catch (error) {
    showToast(error.message);
  }
}

document.querySelector('#web-login-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const errorLabel = document.querySelector('#login-error');
  errorLabel.textContent = '';
  try {
    const user = await requestJson('/api/login', jsonOptions('POST', Object.fromEntries(new FormData(form))));
    await startAuthenticatedApp(user);
  } catch (error) {
    errorLabel.textContent = error.message;
  }
});

document.querySelector('#web-password-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const errorLabel = document.querySelector('#password-error');
  errorLabel.textContent = '';
  if (values.nueva !== values.confirmacion) {
    errorLabel.textContent = 'Las contraseñas no coinciden.';
    return;
  }
  try {
    await requestJson('/api/password', jsonOptions('POST', { actual: values.actual, nueva: values.nueva }));
    const user = await requestJson('/api/session');
    form.reset();
    await startAuthenticatedApp(user);
  } catch (error) {
    errorLabel.textContent = error.message;
  }
});

document.querySelector('#logout-button').addEventListener('click', async () => {
  try { await requestJson('/api/logout', jsonOptions('POST', {})); }
  finally {
    document.body.classList.remove('authenticated');
    document.querySelector('#web-gate').hidden = false;
    document.querySelector('#web-login-panel').hidden = false;
    document.querySelector('#web-password-panel').hidden = true;
    document.querySelector('#web-login-form').reset();
    document.querySelector('#login-error').textContent = '';
  }
});

async function checkExistingSession() {
  try {
    const user = await requestJson('/api/session');
    if (user.authenticated) await startAuthenticatedApp(user);
  } catch (error) {
    document.querySelector('#login-error').textContent = error.message;
  }
}

document.querySelectorAll('[data-screen]').forEach(button => button.addEventListener('click', () => showScreen(button.dataset.screen)));
document.querySelector('[data-refresh="dashboard"]').addEventListener('click', () => loadDashboard().catch(error => showToast(error.message)));

let moduleSearchTimer;
for (const [id, loader] of [['reception-search', loadReception], ['catalog-search', loadCatalog], ['distribution-search', loadDistribution], ['location-search', loadLocations], ['labels-search', loadLabels]]) {
  document.querySelector(`#${id}`).addEventListener('input', event => {
    clearTimeout(moduleSearchTimer);
    moduleSearchTimer = setTimeout(() => loader(event.target.value).catch(error => showToast(error.message)), 180);
  });
}

document.querySelector('#reception-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const result = await requestJson('/api/recepcion', jsonOptions('POST', Object.fromEntries(new FormData(form))));
    showToast(`Ingreso registrado: ${result.message}`);
    form.reset();
    await Promise.all([loadReception(), loadCatalog(), loadDashboard()]);
  } catch (error) { showToast(error.message); }
});

document.querySelector('#catalog-body').addEventListener('change', event => {
  if (!event.target.matches('.pending-choice')) return;
  const book = currentPending.find(item => item.id === Number(event.target.closest('tr').dataset.id));
  if (!book) return;
  const form = document.querySelector('#catalog-form');
  form.elements.id.value = book.id;
  form.elements.cutter.value = '';
  form.elements.codigo.value = '';
  form.elements.cota.value = '';
  form.elements.genero.value = 'No ficción';
  form.elements.seccion.value = '';
  form.elements.numero_autores.value = '';
  form.elements.nacionalidad.value = '';
  form.elements.material.value = '';
  form.elements.alto.value = '';
  form.elements.ancho.value = '';
  form.elements.biografiado.value = '';
  form.elements.tomo.value = '';
  form.elements.tipo_tomo.value = 'v';
  document.querySelector('#catalog-selected').textContent = `${book.titulo} · ${book.numero_registro}`;
  requestJson('/api/cutter', jsonOptions('POST', { autor: book.autor })).then(result => {
    form.elements.cutter.value = result.cutter;
    if (form.elements.modo_cota.value === 'manual') {
      form.elements.cota.value = [form.elements.codigo.value, result.cutter, book.anio || ''].filter(Boolean).join('\n');
    }
  }).catch(error => showToast(error.message));
  form.elements.codigo.oninput = form.elements.cutter.oninput = () => {
    if (form.elements.modo_cota.value === 'manual') {
      form.elements.cota.value = [form.elements.codigo.value, form.elements.cutter.value, book.anio || ''].filter(Boolean).join('\n');
    }
  };
  if (form.elements.modo_cota.value === 'automatica') generateShelfmark(form, book);
});

async function generateShelfmark(form, book) {
  try {
    const data = Object.fromEntries(new FormData(form));
    const result = await requestJson('/api/cota', jsonOptions('POST', { ...data, id: book.id }));
    form.elements.cutter.value = result.cutter;
    form.elements.cota.value = result.cota;
  } catch (error) { showToast(error.message); }
}

document.querySelector('#catalog-form').elements.modo_cota.addEventListener('change', event => {
  if (event.target.value !== 'automatica') return;
  const form = document.querySelector('#catalog-form');
  const book = currentPending.find(item => item.id === Number(form.elements.id.value));
  if (book) generateShelfmark(form, book);
});

document.querySelector('#generate-shelfmark').addEventListener('click', () => {
  const form = document.querySelector('#catalog-form');
  const book = currentPending.find(item => item.id === Number(form.elements.id.value));
  if (!book) return showToast('Selecciona un libro pendiente.');
  form.elements.modo_cota.value = 'automatica';
  generateShelfmark(form, book);
});

document.querySelector('#suggest-cutter').addEventListener('click', async () => {
  const bookId = Number(document.querySelector('#catalog-form').elements.id.value);
  const book = currentPending.find(item => item.id === bookId);
  if (!book) return showToast('Selecciona un libro pendiente.');
  try {
    const result = await requestJson('/api/cutter', jsonOptions('POST', { autor: book.autor }));
    const form = document.querySelector('#catalog-form');
    form.elements.cutter.value = result.cutter;
    form.elements.cutter.dispatchEvent(new Event('input'));
  } catch (error) { showToast(error.message); }
});

document.querySelector('#catalog-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    id: Number(form.elements.id.value), sistema: form.elements.sistema.value,
    codigo: form.elements.codigo.value, cutter: form.elements.cutter.value, cota: form.elements.cota.value,
  };
  try {
    await requestJson('/api/catalogacion', jsonOptions('POST', payload));
    showToast('Libro catalogado. Ya aparece en Fichero e inventario.');
    form.reset();
    form.elements.id.value = '';
    document.querySelector('#catalog-selected').textContent = 'Selecciona un libro pendiente.';
    await Promise.all([loadCatalog(), loadBooks(), loadLabels(), loadDashboard()]);
  } catch (error) {
    if (error.message.includes('Ya existe') && confirm(`${error.message}\n¿Continuar como multivolumen?`)) {
      try {
        await requestJson('/api/catalogacion', jsonOptions('POST', { ...payload, permitir_duplicada: true }));
        showToast('Libro catalogado como multivolumen.');
        await Promise.all([loadCatalog(), loadBooks(), loadLabels(), loadDashboard()]);
      } catch (retryError) { showToast(retryError.message); }
    } else showToast(error.message);
  }
});

document.querySelector('#distribution-body').addEventListener('change', event => {
  if (!event.target.matches('.distribution-choice')) return;
  const id = Number(event.target.closest('tr').dataset.id);
  event.target.checked ? selectedDistribution.add(id) : selectedDistribution.delete(id);
  document.querySelector('#distribution-selected').textContent = `${selectedDistribution.size} seleccionados`;
});

document.querySelector('#distribution-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const payload = Object.fromEntries(new FormData(form));
    payload.biblioteca_id = Number(payload.biblioteca_id);
    payload.ids = [...selectedDistribution];
    const result = await requestJson('/api/distribucion', jsonOptions('POST', payload));
    showToast(`Envío creado: ${result.codigo}`);
    selectedDistribution.clear();
    await Promise.all([loadDistribution(), loadLocations(), loadDashboard()]);
    if (confirm('Envío creado. ¿Descargar el documento para las dos copias?')) {
      await downloadPost('/api/distribution-document', { codigo: result.codigo }, 'documento_envio.pdf');
    }
  } catch (error) { showToast(error.message); }
});

document.querySelector('#shipments-body').addEventListener('click', async event => {
  const button = event.target.closest('.shipment-document');
  if (!button) return;
  try { await downloadPost('/api/distribution-document', { codigo: button.dataset.code }, `${button.dataset.code}.pdf`); }
  catch (error) { showToast(error.message); }
});

document.querySelector('#location-refresh').addEventListener('click', () => loadLocations(document.querySelector('#location-search').value).catch(error => showToast(error.message)));
document.querySelector('#location-state').addEventListener('change', () => loadLocations(document.querySelector('#location-search').value).catch(error => showToast(error.message)));
document.querySelector('#location-body').addEventListener('change', event => {
  if (!event.target.matches('.location-choice')) return;
  selectedLocationId = Number(event.target.closest('tr').dataset.id);
  document.querySelector('#location-form').elements.id.value = selectedLocationId;
});
document.querySelector('#location-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  payload.id = Number(payload.id);
  payload.biblioteca_id = Number(payload.biblioteca_id);
  try {
    const result = await requestJson('/api/ubicacion', jsonOptions('POST', payload));
    showToast(result.message);
    await loadLocations(document.querySelector('#location-search').value);
  } catch (error) { showToast(error.message); }
});
document.querySelector('#history-button').addEventListener('click', async () => {
  if (!selectedLocationId) return showToast('Selecciona un libro para consultar su historial.');
  try {
    const history = await requestJson(`/api/history?id=${selectedLocationId}`);
    alert(history.length ? history.map(item => `${item.fecha} · ${item.tipo}\n${item.origen} → ${item.destino}\n${item.detalle}`).join('\n\n') : 'Sin movimientos registrados.');
  } catch (error) { showToast(error.message); }
});

document.querySelector('#labels-body').addEventListener('change', event => {
  if (!event.target.matches('.label-choice')) return;
  const id = Number(event.target.closest('tr').dataset.id);
  event.target.checked ? selectedLabels.add(id) : selectedLabels.delete(id);
  document.querySelector('#labels-selected').textContent = `${selectedLabels.size} seleccionados`;
});
document.querySelector('#labels-export').addEventListener('click', async () => {
  if (!selectedLabels.size) return showToast('Selecciona al menos un libro catalogado.');
  try {
    await downloadPost('/api/labels', {
      ids: [...selectedLabels], ancho: Number(document.querySelector('#label-width').value),
      alto: Number(document.querySelector('#label-height').value),
    }, 'cotas_lomo.pdf');
    showToast('Etiquetas PDF generadas.');
  } catch (error) { showToast(error.message); }
});

document.querySelector('#report-refresh').addEventListener('click', () => loadReports().catch(error => showToast(error.message)));
for (const [id, url, filename] of [['report-pdf', '/api/reportes/pdf', 'reporte_bibliotecario.pdf'], ['report-excel', '/api/reportes/excel', 'reporte_bibliotecario.xlsx']]) {
  document.querySelector(`#${id}`).addEventListener('click', async () => {
    try {
      await downloadPost(url, { desde: document.querySelector('#report-from').value, hasta: document.querySelector('#report-to').value }, filename);
      showToast('Reporte generado.');
    } catch (error) { showToast(error.message); }
  });
}
document.querySelector('#backup-now').addEventListener('click', async () => {
  try {
    const result = await requestJson('/api/backup', jsonOptions('POST', {}));
    showToast(result.ok ? `Backup creado: ${result.message}` : result.message);
  } catch (error) { showToast(error.message); }
});

document.querySelector('#library-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const result = await requestJson('/api/libraries', jsonOptions('POST', Object.fromEntries(new FormData(form))));
    showToast(result.message);
    form.reset();
    await Promise.all([loadLibraries(), loadDistribution()]);
  } catch (error) { showToast(error.message); }
});
document.querySelector('#libraries-body').addEventListener('click', async event => {
  const button = event.target.closest('.deactivate-library');
  if (!button || !confirm('¿Desactivar esta sucursal?')) return;
  try {
    const result = await requestJson('/api/libraries', jsonOptions('PATCH', { id: Number(button.dataset.id) }));
    showToast(result.message);
    await Promise.all([loadLibraries(), loadDistribution()]);
  } catch (error) { showToast(error.message); }
});

document.querySelector('#user-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const result = await requestJson('/api/users', jsonOptions('POST', Object.fromEntries(new FormData(form))));
    showToast(result.message);
    form.reset();
    await loadUsers();
  } catch (error) { showToast(error.message); }
});
document.querySelector('#users-body').addEventListener('click', async event => {
  const button = event.target.closest('.toggle-user');
  if (!button) return;
  try {
    const result = await requestJson('/api/users', jsonOptions('PATCH', { id: Number(button.dataset.id), activo: button.dataset.active !== 'true' }));
    showToast(result.message);
    await loadUsers();
  } catch (error) { showToast(error.message); }
});

checkExistingSession();