# Eight small Jev demos

For developer tools, small SaaS products, and automations. These are proposed designs, not tested capabilities or claims of globally novel inventions. The distinctiveness is in the narrow workflow and visible comparison against simpler code.

Scope estimates below are our planning estimates for one developer after API access works. They exclude production integrations. Start with synthetic text, a local script, and a terminal table or static report; no database, agent framework, or deployed UI is needed.

## Shortlist

| Demo | Useful in | Jev primitive | First version | Why try it |
| --- | --- | --- | --- | --- |
| [1. Repro Coach](#1-repro-coach) | Issue intake | Noul | 2–3 hours | Turn vague reports into specific follow-up prompts |
| [2. CI Next-Check Cards](#2-ci-next-check-cards) | Developer workflow | Choice | Half a day | Pick the next diagnostic card from a short log |
| [3. Release Claim Check](#3-release-claim-check) | Release preparation | Choice | Half a day | Find claims that overstate their linked evidence |
| [4. CSV Field Matchmaker](#4-csv-field-matchmaker) | SaaS onboarding | Choice | Half a day | Suggest schema mappings from unfamiliar headers |
| [5. Feedback Reunion](#5-feedback-reunion) | Product feedback | Noul | Half a day | Surface an existing request despite different wording |
| [6. Changelog Audience Switch](#6-changelog-audience-switch) | Product communication | Noul | 2–3 hours | Select which existing notes each audience sees |
| [7. Follow-up Promise Catcher](#7-follow-up-promise-catcher) | Task automation | Noul | 2–3 hours | Catch explicit commitments buried in notes |
| [8. Interruption Budget](#8-interruption-budget) | Notification automation | Score | Half a day | Suggest immediate attention or a digest |

Each experiment uses the shared [evaluation protocol](evaluation.md). The acceptance numbers below are proposed learning targets on small fixtures, not production guarantees. Count abstentions and API failures; an empty auto-action set cannot pass.

## 1. Repro Coach

**Moment:** someone submits “Export is broken again,” and the maintainer must ask what happened.

- **Input:** one short bug report, including any form fields already supplied.
- **Jev's job:** three independent Nouls: are repeatable steps present, is an observed result present, and is an execution environment identified?
- **Code's job:** show the missing items using fixed templates; send borderline answers to review. Structured fields can bypass checks when the necessary information is already validated.
- **Demo reveal:** compare “Chrome 128: open Billing, select CSV export; download is empty” with “Please fix export.” Show raw probabilities and the resulting checklist side by side.
- **Baseline:** a required-fields form, or keyword rules for browser names and action verbs.
- **Useful result:** on 20 held-out reports, at least 10 receive an automatic checklist and no more than one of those checklists is wrong. Show whether Jev recovers evidence written in prose that the rules miss.
- **Edge to expose:** “Steps: none provided” contains a heading but no steps. A confidently wrong result is still a failure.
- **Keep it small:** output text locally; no GitHub bot or automatic issue comments.

**Transfer:** forms, support intake, internal incident reports. [Detailed first experiment](first-demo-repro-coach.md).

## 2. CI Next-Check Cards

**Moment:** a developer sees a failed CI job and needs a useful starting point.

- **Input:** the failed step name and a manually selected short error excerpt.
- **Jev's job:** Choice among `dependency_access`, `missing_configuration`, `assertion_failure`, and `unknown`, each tied to a fixed diagnostic card.
- **Code's job:** display the selected card only above a tuned confidence threshold; otherwise show the original log and the card list. Never execute the card's commands.
- **Demo reveal:** “401 while fetching private package” should suggest checking registry access; “expected 200, got 401” in an application test should suggest inspecting the failed assertion.
- **Baseline:** regexes for known CI error signatures.
- **Useful result:** select the maintainer-labeled next card correctly on at least 12 of 15 held-out excerpts, with at least 10 automatic selections and no more than one incorrect automatic selection.
- **Edge to expose:** a downstream error can conceal the root cause. This is a next-check selector, not a root-cause diagnosis system.
- **Keep it small:** four Markdown cards and text fixtures; no CI webhook or auto-retry.

**Transfer:** developer portals and internal troubleshooting tools.

## 3. Release Claim Check

**Moment:** a draft release note says “all exports are faster,” but its evidence only describes a CSV optimization.

- **Input:** one manually paired claim and one short linked issue/PR description.
- **Jev's job:** Choice among `supported`, `contradicted`, and `insufficient_evidence` using only the supplied passage.
- **Code's job:** display the original claim, source link, verdict, and confidence; route uncertain claims for inspection. Do not generate corrected prose.
- **Demo reveal:** change “CSV exports are faster” to “all exports are faster” while holding evidence fixed.
- **Baseline:** keyword overlap plus manual review.
- **Useful result:** on 20 held-out pairs, flag all five planted unsupported/contradicted claims and automatically clear at least 10 of the 15 supported claims.
- **Edge to expose:** a PR description is evidence of what was claimed, not proof of runtime behavior. Passing this check does not validate code or performance.
- **Keep it small:** manually paired text; no repository crawling, automatic release publication, or factual web search.

**Transfer:** product documentation and internal release checks. Adapted from the vendor's [citation-checking pattern](https://docs.typesafe.ai/cookbooks/citation_check), with release communication as the application.

## 4. CSV Field Matchmaker

**Moment:** onboarding stalls because an imported file uses “Trading name” where the app expects `company_name`.

- **Input:** one column header and three synthetic sample values, plus descriptions of five allowed target fields.
- **Jev's job:** Choice of a target field or `unmapped`.
- **Code's job:** parse CSV, enforce type checks, detect duplicate target assignments, and require confirmation of the complete mapping. `unmapped`, conflicts, and low confidence remain visible.
- **Demo reveal:** “Trading name” with company values versus “Account” with mixed numeric/text values.
- **Baseline:** an alias dictionary and normalized exact header matching.
- **Useful result:** compare 20 held-out columns; aim for at least four correct mappings missed by aliases, no more than one incorrect confident suggestion, and zero silently accepted conflicts.
- **Edge to expose:** several independent choices can select the same target. Jev does not enforce a globally valid schema mapping.
- **Keep it small:** a preview table for one synthetic CSV, with no actual import or customer records.

**Transfer:** import wizards and migration tools. This tests semantic matching; CSV parsing stays deterministic.

## 5. Feedback Reunion

**Moment:** “Let me save my filters” and “Remember my search setup” may belong to the same feature request.

- **Input:** one new feedback item and five existing requests from a tiny local catalog.
- **Jev's job:** one Noul per candidate: does it request the same user-visible capability? Include each candidate's text explicitly in its question or referenced state.
- **Code's job:** propose a link when exactly one candidate passes the tuned threshold; show multiple matches or uncertainty for review. If all are below the negative threshold, suggest a new item.
- **Demo reveal:** “remember my filters” versus “share my filters with teammates”: shared words do not imply the same feature.
- **Baseline:** token overlap ranking.
- **Useful result:** on 20 held-out arrivals, correctly reunite at least 7 of 10 known duplicates while making no automatic link on the 10 distinct requests. Report review volume separately.
- **Edge to expose:** a missed retrieval candidate cannot be recovered by classification. Multiple requests in one message need manual splitting in this version.
- **Keep it small:** five candidates per input; no embeddings, clustering, vector store, or automatic merging.

**Transfer:** support deduplication and product feedback inboxes. Add retrieval only when the fixed catalog becomes a real constraint.

## 6. Changelog Audience Switch

**Moment:** a release contains UI changes, API changes, and infrastructure work, but everyone receives the same digest.

- **Input:** one existing changelog entry.
- **Jev's job:** separate Nouls for whether end users need to know and whether API integrators need to know. Both can be true.
- **Code's job:** assemble audience-specific views from the unchanged text; uncertain entries stay in an editorial review list. Nothing is sent automatically.
- **Demo reveal:** “API token rotation is now required” should reach integrators; “updated the internal formatter” should not appear just because it mentions tooling.
- **Baseline:** path/label rules such as `api`, `ui`, and `internal`.
- **Useful result:** on 20 held-out notes, omit none of the five manually designated must-see entries and correctly filter at least five irrelevant entries for each audience.
- **Edge to expose:** a backend change can alter user behavior; file paths alone are weak evidence. Missing release context can also mislead Jev.
- **Keep it small:** two local digest previews; no email, writing assistant, or personalization engine.

**Transfer:** release emails, admin announcements, and in-app change feeds.

## 7. Follow-up Promise Catcher

**Moment:** “I will send the migration checklist tomorrow” is buried in a support note and never becomes a task.

- **Input:** one manually selected sentence plus its known author and source ID.
- **Jev's job:** Noul for an explicit commitment by that author to a future action; a second Noul for whether the action is already complete. Define “we should” and quoted third-party promises as non-commitments.
- **Code's job:** propose a task containing the verbatim sentence only when commitment is high and completion is low; deduplicate by source ID. Mixed or uncertain signals go to review.
- **Demo reveal:** compare “I will send it,” “we should send it,” and “I already sent it.”
- **Baseline:** phrases such as “I will” and “I'll.”
- **Useful result:** on 20 held-out sentences, surface at least 7 of 10 true commitments with at most one false suggestion among 10 non-commitments; replaying inputs creates no duplicate suggestions.
- **Edge to expose:** relative dates and vague owners. The first version leaves the due date unset and asks a person to confirm ownership/date; it does not ask Jev to calculate tomorrow.
- **Keep it small:** a local task-preview file; no calendar, scheduled job, email, or task-tracker connection.

**Transfer:** meeting follow-ups and customer-success workflows. This is an automation design, not a request to schedule an automation in Codex.

[Run the local Follow-up Promise Catcher demo](../demos/promise_catcher/README.md).

## 8. Interruption Budget

**Moment:** every deployment or integration message interrupts you, including expected maintenance chatter.

- **Input:** one event description plus a short user preference such as “interrupt for blocked work; otherwise digest.”
- **Jev's job:** Score against three concrete levels: informational/no action, action needed but work can continue, and current work blocked/action needed now.
- **Code's job:** use score and confidence to suggest `digest`, `review`, or `attention_now`. Low confidence goes to review; code enforces quiet hours and honors authoritative priority flags before calling Jev.
- **Demo reveal:** “Your export completed” versus “Your export failed; your team cannot finish today's handoff.”
- **Baseline:** event-type priority lookup.
- **Useful result:** on 20 held-out events, miss none of five important events, put at least 8 of 10 routine events in the digest, and report how many of the five ambiguous events need review.
- **Edge to expose:** dramatic wording is not business impact. This demo must not suppress real paging, security, or operational alerts.
- **Keep it small:** a simulated inbox with three sections; no push notifications or scheduler.

**Transfer:** SaaS notification preferences and personal work queues. Add a real digest schedule only after labeling performance is useful.

## What to build first

**Recommend Repro Coach:** its inputs are easy to invent and label, incorrect checklists are easy to spot, and the outcome can be generated entirely from templates. **Choose CSV Field Matchmaker** if SaaS onboarding is the priority. **Choose Follow-up Promise Catcher** if automation is the main motivation.

Keep the ideas independent. A good result for one classifier does not validate the others. If a form, alias map, or event lookup wins the comparison, keep that simpler solution and document the finding.
