"""Starter checks exercise basic setup. They are not complete acceptance coverage."""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting, importing


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_seed_is_repeatable(self):
        storage.seed(self.db)
        self.assertEqual(len(reporting.invoices(self.db)), 6)

    def test_seed_summary(self):
        summary = reporting.overview(self.db)['summary']
        self.assertEqual(summary['invoice_count'], 6)
        self.assertEqual(summary['outstanding'], 3209.99)

    def test_one_valid_invoice(self):
        result = importing.import_csv(self.db, 'customer_id,invoice_number,amount,due_date\nHARBOR,SMOKE-1,25.00,2026-09-09\n', 'invoices')
        self.assertEqual(result['imported'], 1)

    def test_payment_reference_when_amount_is_unique(self):
        result = importing.import_csv(self.db, 'payment_id,customer_id,invoice_number,amount\nSMOKE-P1,HARBOR,INV-100,20.00\n', 'payments')
        self.assertEqual(result['imported'], 1)
        invoice = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'INV-100')
        self.assertEqual(invoice['paid'], 20.00)

    def test_export_has_header(self):
        self.assertTrue(reporting.export_csv(self.db).startswith('customer_id,invoice_number,amount,paid,balance,status'))

    def test_duplicate_invoice_is_skipped(self):
        result = importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\nHARBOR,INV-100,1250.00,2026-09-01\n',
            'invoices',
        )
        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['skipped'], 1)
        self.assertEqual(result['rejected'], 0)
        self.assertEqual(len(reporting.invoices(self.db)), 6)

    def test_payment_is_matched_by_reference_not_amount(self):
        result = importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\nMATCH-ONLY,HARBOR,WAIT-999,1250.00\n',
            'payments',
        )
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['rejected'], 0)
        unmatched = reporting.overview(self.db)['unmatched_payments']
        self.assertIn('MATCH-ONLY', [p['payment_id'] for p in unmatched])

    def test_partial_import_keeps_valid_rows(self):
        result = importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\nHARBOR,OK-1,12.50,2026-11-11\nHARBOR,BAD-1,0,2026-11-12\n',
            'invoices',
        )
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(result['errors'][0]['line'], 3)
        self.assertIn('OK-1', [r['invoice_number'] for r in reporting.invoices(self.db)])

    def test_open_and_paid_filters_use_balance_status(self):
        paid = reporting.invoices(self.db, 'paid')
        open_rows = reporting.invoices(self.db, 'open')
        self.assertTrue(any(r['status'] == 'paid' for r in paid))
        self.assertTrue(any(r['status'] == 'open' for r in open_rows))
        self.assertEqual(set(r['status'] for r in paid), {'paid'})
        self.assertEqual(set(r['status'] for r in open_rows), {'open'})

    def test_overpayment_creates_negative_balance(self):
        importing.import_csv(self.db, 'customer_id,invoice_number,amount,due_date\nHARBOR,OVER-1,100.00,2026-09-09\n', 'invoices')
        importing.import_csv(self.db, 'payment_id,customer_id,invoice_number,amount\nPAY-OVER-1,HARBOR,OVER-1,150.00\n', 'payments')
        invoice = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'OVER-1')
        self.assertEqual(invoice['balance'], -50.00)
        self.assertEqual(invoice['status'], 'paid')

    def test_invalid_header_aborts_import(self):
        with self.assertRaises(ValueError):
            importing.import_csv(self.db, 'customer,invoice,amount,date\nHARBOR,INV-1,100.00,2026-09-20\n', 'invoices')

    def test_unmatched_payment_does_not_reduce_balance(self):
        # We start with existing invoices
        initial_balance = reporting.overview(self.db)['summary']['outstanding']
        result = importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\nU-999,MAPLE,WAIT-900,33.33\n',
            'payments'
        )
        self.assertEqual(result['imported'], 1)
        new_balance = reporting.overview(self.db)['summary']['outstanding']
        self.assertEqual(initial_balance, new_balance)

    def test_conflicting_invoice_rejected(self):
        # Insert first
        importing.import_csv(self.db, 'customer_id,invoice_number,amount,due_date\nHARBOR,CONF-1,100.00,2026-09-09\n', 'invoices')
        # Insert conflicting (different amount)
        result = importing.import_csv(self.db, 'customer_id,invoice_number,amount,due_date\nHARBOR,CONF-1,200.00,2026-09-09\n', 'invoices')
        self.assertEqual(result['rejected'], 1)
        
    def test_conflicting_payment_rejected(self):
        # Insert first
        importing.import_csv(self.db, 'payment_id,customer_id,invoice_number,amount\nPAY-CONF-1,HARBOR,INV-1,50.00\n', 'payments')
        # Insert conflicting (different amount)
        result = importing.import_csv(self.db, 'payment_id,customer_id,invoice_number,amount\nPAY-CONF-1,HARBOR,INV-1,60.00\n', 'payments')
        self.assertEqual(result['rejected'], 1)

if __name__ == '__main__':
    unittest.main()
