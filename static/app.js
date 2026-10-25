'use strict';
const $ = id => document.getElementById(id);
const money = new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'});
const form = $('vehicle-form');
let vehicles = [];
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function notice(message, error = false) {
  $('notice').textContent = message;
  $('notice').classList.toggle('error', error);
}
async function api(path, method = 'GET', body) {
  const response = await fetch(path, {method, headers: {
    'Content-Type': 'application/json', 'X-Requested-With': 'MinhaFrota'
  }, body: body === undefined ? undefined : JSON.stringify(body)});
  if (response.status === 204) return null;
  const content = response.headers.get('Content-Type') || '';
  if (!content.includes('application/json')) throw new Error('Acesso não autorizado ou serviço indisponível. Atualize a página.');
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || 'Falha na requisição.');
  return result.data || result;
}
function reset() {form.reset();form.elements.id.value = '';$('form-title').textContent = 'Cadastrar veículo';}
async function load() {
  try {
    const [items, summary] = await Promise.all([api('/api/vehicles'), api('/api/dashboard')]);
    vehicles = items;
    $('total').textContent = summary.active_vehicles;
    $('cost').textContent = money.format(summary.monthly_cost);
    $('pending').textContent = summary.upcoming.length;
    $('count').textContent = `${vehicles.length} cadastrado(s)`;
    $('vehicles').replaceChildren();
    for (const vehicle of vehicles) {
      const card = node('article', undefined, 'vehicle');
      card.append(node('h3', `${vehicle.brand} ${vehicle.model}`), node('div', vehicle.plate, 'plate'),
        node('span', `${vehicle.type} · ${vehicle.year} · ${vehicle.status}`, 'badge'),
        node('p', `${Number(vehicle.odometer_km).toLocaleString('pt-BR')} km`, 'muted'));
      const actions = node('div', undefined, 'actions');
      const edit = node('button', 'Editar', 'secondary');
      edit.onclick = () => {for (const field of ['id','type','brand','model','year','plate','odometer_km']) form.elements[field].value = vehicle[field];$('form-title').textContent = 'Editar veículo';form.elements.brand.focus();};
      const remove = node('button', 'Excluir', 'danger');
      remove.onclick = async () => {
        if (!confirm(`Excluir ${vehicle.plate} e todos os registros relacionados?`)) return;
        try {await api(`/api/vehicles/${vehicle.id}?confirm=true`, 'DELETE');reset();await load();} catch (error) {notice(error.message, true);}
      };
      actions.append(edit, remove);card.append(actions);$('vehicles').append(card);
    }
    if (!vehicles.length) $('vehicles').append(node('p', 'Nenhum veículo cadastrado. Use o formulário abaixo.', 'empty'));
    $('records').replaceChildren();
    for (const record of summary.upcoming) {
      const item = node('div', undefined, 'record');
      item.append(node('strong', record.description), node('p', `${record.vehicle_name} · ${record.due_date || 'Sem data'} · ${money.format(record.amount)}`, 'muted'));
      $('records').append(item);
    }
    if (!summary.upcoming.length) $('records').append(node('p', 'Nenhum registro pendente.', 'empty'));
    notice('Dados atualizados.');
  } catch (error) {notice(error.message, true);}
}
form.onsubmit = async event => {
  event.preventDefault();
  const id = form.elements.id.value;
  const payload = Object.fromEntries(['type','brand','model','plate'].map(key => [key, form.elements[key].value]));
  payload.year = Number(form.elements.year.value);
  payload.odometer_km = Number(form.elements.odometer_km.value);
  try {await api(`/api/vehicles${id ? '/' + id : ''}`, id ? 'PUT' : 'POST', payload);reset();await load();notice('Veículo salvo.');} catch (error) {notice(error.message, true);}
};
$('refresh').onclick = load;$('cancel').onclick = reset;load();
