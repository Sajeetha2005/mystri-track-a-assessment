const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const money = n => currency.format(n);
const text = (tag, value, className = '') => {
  const node = document.createElement(tag);
  node.textContent = value;
  node.className = className;
  return node;
};

async function refresh() {
  const status = document.querySelector('#status').value;
  const responses = await Promise.all([fetch('/api/overview'), fetch(`/api/invoices?status=${status}`)]);
  if (responses.some(r => !r.ok)) throw new Error('Could not refresh the register.');
  const [data, rows] = await Promise.all(responses.map(r => r.json()));
  document.querySelector('#invoice-count').textContent = data.summary.invoice_count;
  document.querySelector('#open-count').textContent = data.summary.open_count;
  document.querySelector('#outstanding').textContent = money(data.summary.outstanding);
  const body = document.querySelector('#invoices');
  body.replaceChildren();
  rows.forEach(r => {
    const row = document.createElement('tr');
    [r.customer_name, r.invoice_number, r.due_date].forEach(v => row.append(text('td', v)));
    [r.amount, r.paid, r.balance].forEach(v => row.append(text('td', money(v), 'number')));
    row.append(text('td', r.status));
    body.append(row);
  });
  const unmatched = document.querySelector('#unmatched');
  unmatched.replaceChildren(...data.unmatched_payments.map(p => text('li', `${p.payment_id} · ${p.customer_id} / ${p.invoice_number} · ${money(p.amount)}`)));
  if (!data.unmatched_payments.length) unmatched.append(text('li', 'No unmatched payments.'));
  document.querySelector('#page-error').textContent = '';
}

async function submitImport(form) {
  const feedback = form.querySelector('.feedback');
  const button = form.querySelector('button');
  button.disabled = true;
  feedback.textContent = 'Importing…';
  try {
    const csv = await form.querySelector('input').files[0].text();
    const response = await fetch(`/api/import?kind=${form.dataset.kind}`, {
      method: 'POST', headers: { 'Content-Type': 'text/csv' }, body: csv
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data?.error || 'Import failed.');
    }
    feedback.innerHTML = '';
    
    const summaryHeader = document.createElement('div');
    summaryHeader.textContent = 'Import completed';
    summaryHeader.style.fontWeight = 'bold';
    summaryHeader.style.marginBottom = '8px';
    feedback.append(summaryHeader);

    const statsDiv = document.createElement('div');
    statsDiv.innerHTML = `Imported: ${data.imported}<br>Skipped: ${data.skipped}<br>Rejected: ${data.rejected}`;
    statsDiv.style.marginBottom = '8px';
    feedback.append(statsDiv);

    if (data.errors && data.errors.length > 0) {
      const errorsHeader = document.createElement('div');
      errorsHeader.textContent = 'Rejected rows:';
      errorsHeader.style.fontWeight = 'bold';
      feedback.append(errorsHeader);
      
      const errorsList = document.createElement('ul');
      errorsList.style.marginTop = '4px';
      errorsList.style.paddingLeft = '20px';
      data.errors.forEach(e => {
        const li = document.createElement('li');
        li.textContent = `Line ${e.line} – ${e.reason}`;
        errorsList.append(li);
      });
      feedback.append(errorsList);
    }
    await refresh();
  } catch (error) {
    feedback.textContent = `Import failed: ${error.message}`;
  } finally {
    button.disabled = false;
  }
}

document.querySelector('#status').addEventListener('change', () => refresh().catch(e => { document.querySelector('#page-error').textContent = e.message; }));
document.querySelectorAll('form[data-kind]').forEach(form => form.addEventListener('submit', e => { e.preventDefault(); submitImport(form); }));
refresh().catch(e => { document.querySelector('#page-error').textContent = e.message; });
