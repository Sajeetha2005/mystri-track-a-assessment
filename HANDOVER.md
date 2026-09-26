# ClearLedger handover

## Why Track A
I chose Track A because it aligns with my interest and experience in Python and product/backend engineering. I wanted to demonstrate debugging, data integrity, testing, and practical software improvement within a contained environment.

## What I delivered
- Fixed duplicate invoice detection so re-importing the same `(customer_id, invoice_number)` with identical details is skipped instead of creating a second row.
- Fixed duplicate payment detection so reusing the same `payment_id` with identical data is skipped; conflicting data is rejected.
- Corrected payment matching to use the invoice reference `(customer_id, invoice_number)` instead of matching on amount alone.
- Fixed import validation so one invalid row no longer aborts the whole CSV; valid rows still import and rejected rows report their line number and reason.
- Corrected the `open`/`paid` status filters and overview totals so the register matches the balance logic.
- Fixed money export formatting to preserve two-decimal values.
- Improvement: Added a clearer import summary that groups imported, skipped and rejected rows and displays rejection reasons so users can immediately understand what happened to their upload.
- Added edge case tests for overpayments, invalid headers, unmatched payments, and conflicting records.

## Evidence

Failing-before / passing-after:
- Duplicate invoice import initially changed the register. After the storage fix, re-importing identical data returns `skipped=1` and leaves totals unchanged.
- A single invalid row in a CSV previously failed the entire import. It now rejects only the invalid row while successfully processing the valid ones.

Existing register:
- 9 invoices → preserved
- 5 payments → preserved
- 7 open invoices → preserved
- ₹3,698.19 outstanding → preserved
- 1 unmatched payment → preserved
After restoring the fixture, importing a new invoice and new payment, and restarting the application, the totals correctly updated and persisted (10 invoices, 7 open, ₹3,698.19 outstanding).

Improvement:
Added import summary layout with count breakdown and clear lines indicating reasons for rejected rows.

## Tools and judgment
VS Code – used for code inspection and implementation.
Python unittest – used for regression and smoke testing verification.
Google Gemini Pro – used to reason about possible defect locations, test cases, and edge scenarios. I independently inspected the implementation and verified suggestions by running the application/tests rather than accepting generated changes without checking them. For example, I ran tests interactively and verified the database persistence with a Python one-liner to ensure the fixture survived application restarts without data loss.
