import re
from datetime import date
from decimal import Decimal, InvalidOperation


HEADERS = {
    'invoices': ['customer_id', 'invoice_number', 'amount', 'due_date'],
    'payments': ['payment_id', 'customer_id', 'invoice_number', 'amount'],
}


def normalize(row, kind, customer_ids):
    result = {}
    for key in HEADERS[kind]:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{key} is required')
        result[key] = value.strip()
    if result['customer_id'] not in customer_ids:
        raise ValueError('Unknown customer_id')
    try:
        amount = Decimal(result['amount'])
    except InvalidOperation:
        raise ValueError('Amount must be a positive decimal with at most two places') from None
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', result['amount']):
        raise ValueError('Amount must be a positive decimal with at most two places')
    if not 0 < amount <= Decimal('10000000'):
        raise ValueError('Amount must be a positive decimal with at most two places')
    result['amount'] = float(amount.quantize(Decimal('0.01')))
    if kind == 'invoices':
        try:
            parsed = date.fromisoformat(result['due_date'])
            if parsed.isoformat() != result['due_date']:
                raise ValueError()
        except ValueError:
            raise ValueError('due_date must be YYYY-MM-DD') from None
    return result
