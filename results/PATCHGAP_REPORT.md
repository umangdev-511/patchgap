# PATCHGAP REPORT

Status: **VERIFIED AFTER REPAIR**

## CHANGE UNDERSTOOD

Users occasionally receive duplicate entitlement after payment.

- Language: python
- Affected symbols: access_count, grant_access, handle_payment
- Domain signals: payment, event, entitlement, access

## RISKS DISCOVERED

- H1 [HIGH] Duplicate event may grant entitlement twice: Call the handler twice with one successful event id; assert access_count is 1.
- H2 [HIGH] Processing payment may fulfill early: Call the handler with processing status; assert access_count is 0.
- H3 [MEDIUM] Distinct payments must still fulfill: Deliver two succeeded events with distinct ids for one user; assert access_count is 2.
- H4 [MEDIUM] Unverified events may cross a trust boundary: No automatic probe: the API has no authentication or signature argument.

## TESTS GENERATED

3 executable replay-generated probe(s); probes ran independently against a fresh repository copy.

- Duplicate event may grant entitlement twice: FAIL (delivery #1 → fulfillment_count = 1; delivery #2 → fulfillment_count = 2; invariant expected 1.)
- Processing payment may fulfill early: PASS (Invariant held.)
- Distinct payments must still fulfill: PASS (Invariant held.)
- Unverified events may cross a trust boundary: NOT_RUN (Unable to verify automatically: no safe executable strategy for this repository API.)

## FAILURES REPRODUCED

1 valid behavioral violation(s) reproduced. Existing public suite: PASS.

## REPAIR ATTEMPTS

- Minimalist: REJECT — At least one verification layer failed.
- Root-cause: ACCEPT — All verification layers passed.
- Defensive: REJECT — At least one verification layer failed.

## FINAL VERIFICATION

1 repair candidate(s) survived every generated probe and existing public test.

## VERDICT

Winner: **Root-cause**

## REPLAYED COMPONENTS

The specialist hypotheses, generated-probe artifacts, and repair strategies are recorded deterministic replay inputs. Their **execution evidence is live**: PatchGap created isolated workspaces, applied patches, and ran assertions and process commands.

## LIMITATIONS

The replay does not establish Codex behavior. This MVP recognizes the payment-handler API well and is best-effort for generic repositories. Generated code runs in temporary directories, not a hardened OS sandbox.
