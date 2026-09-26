# ClearLedger Handover

## Why Track A

I chose Track A because it aligns with my interest and experience in Python and product/backend engineering. I wanted to demonstrate practical debugging, data integrity, testing, and software improvement within a contained application.

---

## What I Delivered

I investigated the ClearLedger application against the supplied business rules and repaired the following areas:

- Fixed duplicate invoice handling so that re-importing an invoice with the same `(customer_id, invoice_number)` and identical details is skipped instead of creating a duplicate record.
- Fixed conflicting invoice handling so that an existing invoice cannot be silently overwritten by conflicting data.
- Fixed duplicate payment handling so that a payment with the same `payment_id` and identical details is skipped.
- Fixed conflicting payment handling so that conflicting payment data is rejected instead of overwriting an existing payment.
- Corrected payment matching to use `(customer_id, invoice_number)` rather than matching payments based on amount alone.
- Fixed CSV validation so that invalid data rows are rejected individually while valid rows in the same file can still be processed.
- Added validation for legitimate currency amounts, dates, and required values.
- Corrected CSV import processing so that the API reports the actual imported, skipped, and rejected counts.
- Corrected the `open` and `paid` filters so that they are based on the invoice balance/status rules.
- Corrected outstanding balance and invoice status calculations.
- Fixed export formatting so monetary values retain consistent two-decimal formatting.
- Improved browser-side import feedback so that failed requests are not presented as successful imports.
- Added clear rejection reasons and line numbers to import feedback.

### Additional Improvement

Beyond the required repairs, I added a structured **Import Summary** to the web interface.

After an import, the application now clearly displays:

- Number of records imported
- Number of records skipped
- Number of records rejected
- Rejected row line numbers
- Reasons for rejected rows

This uses the existing API response data and provides users with a clearer understanding of what happened during an import.

---

## Evidence

### Failing-Before / Passing-After

#### Duplicate invoice import

Before the repair, re-importing the same invoice could change the register by creating another record.

After the repair:

- Identical duplicate invoice → skipped
- Register totals remain unchanged
- Conflicting invoice data → rejected rather than silently changing the existing record

#### Duplicate payment import

After the repair:

- Identical duplicate payment → skipped
- Conflicting payment data → rejected
- Existing payment records are not overwritten

#### Payment matching

Payment allocation was corrected to use the invoice reference `(customer_id, invoice_number)`.

This prevents a payment from being incorrectly matched to an invoice simply because the amounts happen to be equal.

#### Partial CSV import

Before the repair, an invalid row could prevent the complete import from being processed.

After the repair:

- Valid rows continue to be processed
- Invalid rows are rejected individually
- Rejected rows include their line number and reason
- Import statistics accurately report imported, skipped, and rejected records

#### Invalid CSV header

An invalid header is treated as a file-level validation error and the import is rejected rather than partially processing a file with an unsupported schema.

#### Open and paid reporting

The `open` and `paid` views were corrected to use the invoice balance/status rules, ensuring that the displayed records and totals are consistent.

---

## Existing Register Preservation

The supplied fixture was restored and verified before testing the changes.

The expected starting state was confirmed as:

- 9 invoices
- 5 payments
- 7 open invoices
- ₹3,698.19 outstanding
- 1 unmatched payment

These existing records remained intact after importing additional invoice and payment data.

I also restarted the application context after adding new records and verified that both the original fixture records and the newly added records persisted correctly in SQLite.

---

## Edge-Case Verification

The following important business-rule cases were specifically tested:

- Identical duplicate invoice → skipped
- Conflicting invoice → rejected
- Identical duplicate payment → skipped
- Conflicting payment → rejected
- Payment matched using customer and invoice reference
- Payment for a non-existent invoice → retained as unmatched
- Invalid data row → rejected without preventing valid rows from importing
- Invalid CSV header → entire import rejected
- Overpayment → accepted and represented as a negative invoice balance with paid status
- Open/paid filtering → verified against balance status
- Existing fixture records → preserved
- Database persistence after application restart → verified

---

## Automated Verification

Regression and edge-case coverage was added to `tests/test_smoke.py`.

The final test suite contains **14 tests**, covering the main repaired behaviors and important edge cases.

Final result:

**14/14 tests passed.**

The tests include coverage for:

- Duplicate invoice handling
- Duplicate payment handling
- Conflicting invoice records
- Conflicting payment records
- Payment matching
- Partial invalid-row imports
- Invalid CSV headers
- Open/paid filtering
- Overpayments
- Unmatched payments
- Fixture preservation and related ledger behavior

---

## Files Changed

The main implementation changes were made in:

- `ledger/storage.py` — duplicate and conflicting record handling
- `ledger/matching.py` — payment-to-invoice matching
- `ledger/validation.py` — CSV and field validation
- `ledger/importing.py` — row-level import processing and result reporting
- `ledger/reporting.py` — balance, status, filtering, and export behavior
- `web/app.js` — browser-side import feedback and import summary
- `tests/test_smoke.py` — regression and edge-case tests
- `HANDOVER.md` — implementation, evidence, and verification documentation

No unnecessary rewrite of the application architecture was performed.

---

## Tools and Judgment

### VS Code

Used for:

- Inspecting the existing codebase
- Debugging
- Implementing changes
- Reviewing modified files

### Python unittest

Used for:

- Regression testing
- Edge-case verification
- Confirming that existing behavior remained intact after the changes

The final test suite completed with:

**14/14 tests passing.**

### Google Gemini Pro

Used to assist with:

- Reasoning about possible defect locations
- Identifying useful test cases
- Considering edge cases
- Reviewing possible implementation approaches

AI-generated suggestions were treated as hypotheses rather than automatically accepted changes. I independently inspected the implementation, checked the suggestions against the supplied business rules, and verified the resulting behavior using automated tests and manual application checks.

### Example of Tool Judgment

For duplicate record handling, the suggested approach was not accepted without verification. I tested both:

1. An identical duplicate record, which should be skipped.
2. A conflicting record with the same identity but different details, which should be rejected.

The final implementation was retained only after the behavior matched the business rules and the corresponding regression tests passed.

I also manually verified database persistence by restoring the supplied fixture, adding new records, restarting the application context, and confirming that the original and newly added records remained available.

---

## Questions I Would Investigate in a Real Project

The assessment environment provides a defined set of business rules. In a production system, I would clarify the following before deployment:

- What is the expected workflow for correcting an invoice after it has already been paid?
- Should conflicting imports always be rejected, or should there be an explicit update/reconciliation workflow?
- How should refunds, chargebacks, or reversed payments be represented?
- What audit trail is required for changes to financial records?
- What authentication and authorization controls are required before production deployment?
- What backup and recovery requirements apply to the ledger database?
- What concurrency and transaction guarantees are required if multiple users import or update records simultaneously?
- What retention and reporting requirements apply to historical invoice and payment records?
- Should users be able to undo or review an import before committing changes to the ledger?

These questions would be clarified with the product and finance stakeholders before treating the application as production-ready.

---

## Known Scope / Limitations

The work was intentionally scoped to the supplied assessment requirements and the four-hour assessment constraint.

I focused on:

- Correctness of the specified business rules
- Data integrity
- Regression prevention
- Verification of important edge cases
- A small user-facing improvement
- Clear documentation and handover

I did not introduce broader architectural changes, authentication systems, deployment infrastructure, or unrelated product features because they were outside the assessment scope.

---

## Final Verification Summary

The final ClearLedger submission:

- Preserves the supplied fixture data
- Correctly handles duplicate and conflicting records
- Matches payments using invoice references
- Handles invalid rows without unnecessarily rejecting valid rows
- Rejects invalid CSV headers
- Correctly calculates invoice status and balances
- Preserves consistent monetary formatting
- Provides accurate import feedback
- Includes an additional user-facing import summary improvement
- Includes regression and edge-case coverage
- Passes **14/14 automated tests**
- Includes documented verification and tool-use decisions
