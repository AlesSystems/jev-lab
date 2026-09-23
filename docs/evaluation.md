# How to tell whether a demo is useful

**Status:** evaluation protocol. Per-demo evidence notes record offline baseline results; live Jev performance remains unmeasured. This protocol applies to the [demo ideas](demo-ideas.md). Small fixture sets are learning tools, not proof of production reliability.

## One short experiment

1. Write 10 development examples and the expected decision for each before calling Jev. Include clear positives, clear negatives, missing context, misleading keywords, and text trying to steer the decision. Keep sensitive data out of the fixtures.
2. Implement the idea's simplest baseline: a required field, keyword rule, alias map, or lookup table. Keep a “send everything to review” baseline too.
3. Try the questions on development examples. Change one question or threshold at a time and record what changed. For disputed labels, agree on the criteria or label the case for review.
4. Freeze questions, criteria, model version, thresholds, and baseline. Create the held-out set specified by the idea (usually 20 inputs) independently of tuning; keep related paraphrases in the same split.
5. Run both systems on the same held-out inputs. Save results, errors, and wall-clock durations. Manually compare each final action with its label. If you tune after seeing failures, use a new held-out set before calling it an improvement.
6. Keep Jev only if it solves errors that matter without unacceptable review volume, cost, or delay. A baseline win is a successful research outcome.

## Record enough to reproduce the result

Use one JSONL/CSV result file and a short Markdown note per experiment; a dashboard is unnecessary. Record:

- Fixture ID, expected decision, split, and whether the label is disputed.
- Baseline result and final Jev-assisted action, including `review` or `unavailable`.
- Exact questions/criteria or a versioned fixture reference; selected thresholds.
- Requested model and returned model ID; SDK version if used; run date.
- Raw answer probabilities, Choice/Score confidence when available, and token usage.
- End-to-end elapsed milliseconds, request attempts, errors, and any missing usage data.

Use synthetic source text in committed artifacts. Before later using customer data, decide which fields are necessary and what may leave the application; model classification must not bypass tenant authorization or secret redaction.

## Read the trade-offs

| Measure | Calculation or interpretation |
| --- | --- |
| Automatic coverage | Automatic decisions / all eligible inputs, including failures in the denominator |
| Selective accuracy | Correct automatic decisions / automatic decisions; report `N/A` when none occur |
| Review rate | Review outcomes / all eligible inputs |
| Unavailable rate | Failed or invalid results / all eligible inputs |
| Important misses | Count wrong automatic dismissals separately; for notifications, urgent items put in a digest |
| Baseline gain | Correct cases rescued from the baseline, plus regressions introduced by Jev |
| Latency | Per-input wall time and p50/p95, with retry time included; keep failure timing visible |
| Cost | Sum known billed input tokens × current input-token price; label estimates and unknown retry usage |

For Repro Coach, score the **whole checklist**, not just individual answers. For a multi-question demo, thresholds apply to every answer needed for the action; one confident answer must not conceal an uncertain dependency.

An illustrative result of 11 correct automatic actions out of 12, from 20 inputs, means 60% coverage and about 91.7% selective accuracy. Those numbers are arithmetic examples, not Jev results. Show counts alongside percentages so a tiny sample does not look conclusive.

For Noul, inspect whether high yes-probabilities coincide with true labels. For Choice/Score, inspect the full distribution as well as confidence. A small dataset is insufficient to establish calibration; save the pairs for a larger later analysis. A confidence threshold is an operational policy, not a universal accuracy promise. [Source: TypeSafe confidence guidance](https://docs.typesafe.ai/confidence)

Repeat a few boundary fixtures under the same settings to look for changed actions, without assuming repeatability proves correctness. Pinning a model makes comparisons easier; it does not make a wrong answer right.

## Automation-specific checks

Simulate outputs before connecting a destination. Replay the same source ID to test duplicate handling. Exercise missing data, timeouts, invalid responses, and uncertain answers: these must produce visible review/unavailable outcomes, not silently become “nothing to do.” Keep dates, scheduling, permissions, and idempotent writes in code.

For the Promise Catcher, a proposed task must retain its source sentence and unset due date. For Interruption Budget, report critical misses independently of average accuracy and preserve any authoritative event priority.

## Decision note for each completed experiment

Record the dataset and settings, metric counts, representative failures, and one decision: **keep**, **revise**, or **use the baseline**. Explain where the decision might change on real inputs. Link the implementation commit and reproducible command when an implementation exists. Never replace a failed experiment with a vendor benchmark.
