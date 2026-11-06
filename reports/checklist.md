# Implementation progress

- [x] Inspect required D: location and preserve existing files (initial project directory empty).
- [x] Evaluate source candidates; acquire real Olist data; record attribution, licence, pinned URLs and checksums.
- [x] Build schemas, quarantine, quality reports, warehouse and cleaned exports.
- [x] Execute ten analytical questions and generate findings/actions.
- [x] Implement read-only API and responsive seven-page companion.
- [x] Prepare typed Power Query, DAX, theme, model/page specifications and real reconciliation totals.
- [x] Document setup, grains, metrics, limitations, architecture and portfolio demo.
- [x] Expanded Python tests: 13 passed on 2026-11-05; evidence in pytest.xml.
- [x] React/TypeScript production build passed on 2026-11-05.
- [x] Idempotence audit: all 17 table content hashes unchanged on 2026-11-05.
- [ ] Fresh browser checks: previous 2026-11-04 report records 2 passes; rerun on 2026-11-05 blocked before tests by process-launch error `spawn EPERM` in the restricted execution environment. Playwright now manages missing local servers automatically; run the README verification command in a local terminal.
- [ ] Power BI Desktop assembly and engine validation (external manual step; Desktop unavailable).

## Recovery notes — 2026-11-05

Existing implementation and raw data were preserved. The directory has no .git repository, so no Git history or baseline diff is available. Requirements were recovered from README, docs, code and this checklist; no restart was needed.

The warehouse rebuild retained 99,252 accepted orders. Python checks cover API/SQL reconciliation, attribution, eligibility boundaries, quarantine, adjustment, scenarios and exports. The production build reports a non-fatal bundle-size warning. Python reports an upstream AnyIO deprecation warning.

Remaining work is a fresh browser run and Power BI Desktop assembly/engine validation using powerbi/ASSEMBLY.md. No PBIX or Desktop validation is claimed. Power BI Desktop was not found in its standard Program Files location or installed Appx packages during recovery.

Browser failure investigation: Playwright debug logging shows `spawn EPERM` while starting the backend web server, before browser launch. A minimal Node `child_process.spawn(process.execPath, ['--version'])` also fails with the same error in this execution environment. This is broader than Playwright configuration; the precise Windows policy responsible was not established. No security settings were changed. Run the documented servers and browser tests in a normal local PowerShell terminal; existing Chromium is under .cache/playwright. Verification remains incomplete.
