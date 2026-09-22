# Where Jev fits in your software

Research snapshot: **2026-09-22**. This is a reading of TypeSafe's public documentation, not a benchmark. No API requests were made for this research.

Jev is worth exploring when an application needs a small judgment about language and already knows the allowed outcomes. For example: does a bug report include reproduction steps, which existing field does a CSV column represent, or does a source paragraph support a release-note claim?

It is not a replacement for the model in your coding agent. TypeSafe documents Jev as a decision model rather than a text or code generator. Your coding agent can build an application that calls it. [Source: Jev with coding agents](https://docs.typesafe.ai/introduction/coding-agents)

## Three primitives to learn

| Primitive | Ask it for | Read from the answer | Small example |
| --- | --- | --- | --- |
| **Noul** | Whether one proposition is true | `noul`, the probability of yes, from 0 to 1 | Does this report state what actually happened? |
| **Choice** | One member of a defined set | `choice`, `probabilities`, `confidence` | Is this column a company, contact, or unknown field? |
| **Score** | A position on an ordered descriptive rubric | `score`, `probabilities`, `confidence`, `legend` | No interruption needed / attention soon / attention now |

Noul has **no separate confidence field**. A value of 0.9 means a high estimated probability of yes; it does not mean “90% severe.” A Score with three levels spans 0–2 and may be fractional. It is a probability-weighted position, not a measurement such as minutes or dollars. [Sources: Noul](https://docs.typesafe.ai/primitives/noul), [Choice](https://docs.typesafe.ai/primitives/choice), [Score](https://docs.typesafe.ai/primitives/score)

For Choice and Score, confidence summarizes how concentrated the returned distribution is. Do not read `confidence: 0.9` as a demonstrated 90% chance of correctness in your application. Choose action thresholds using labeled examples and inspect errors as well as uncertainty. [Source: Confidence](https://docs.typesafe.ai/confidence)

## The integration boundary

Supply the relevant text or structured JSON as `state`, with narrow questions in `questions`. Questions in one request see that same state independently; one question cannot use another question's answer from that call. Compose dependent decisions in code or make a second request. [Sources: State](https://docs.typesafe.ai/concepts/state), [Introduction](https://docs.typesafe.ai/introduction)

| Responsibility | Keep it in |
| --- | --- |
| Parsing CSV, matching exact IDs, counting, comparing dates | Ordinary code |
| Interpreting a short description against explicit criteria | Jev |
| Generating an explanation or new prose, if actually needed | A template or a separate generative model |
| Permissions, tenant isolation, validation, schedules, retries, writes | Application code |
| Ambiguous or unsupported outcomes | A visible review path |

See the [architecture diagram](diagrams/jev-decision-loop.html). The first version of every proposed automation writes a local suggestion, so its errors can be inspected before connecting a real action.

## Start with the smallest interface

The documented HTTP interface is `POST https://api.typesafe.ai/v1/systemone`, authenticated with a bearer key, with `state`, `model`, and `questions` in the body. TypeSafe also supplies Python and JavaScript SDKs. Try the Playground or a single HTTP request before choosing a framework. [Sources: Quick start](https://docs.typesafe.ai/introduction/quickstart), [API reference](https://docs.typesafe.ai/api)

As of this snapshot, the Models page lists `jev-1.13.0`, with `jev-latest` pointing to it, text-only input, and input-token pricing of $0.042 per million tokens with free output tokens. These are vendor-published details, not measured results. Pin the version for comparisons and record the returned model ID. Recheck availability, pricing, and limits before a live run. [Source: Models](https://docs.typesafe.ai/models)

## Limits that shape these ideas

TypeSafe's Jev 1.13 limitation notes identify trouble with arithmetic, date comparison, indirect questions, irrelevant context, adversarial text, and text generation. Independently asked questions also need not satisfy logical identities. Keep inputs short, use precise criteria, and calculate exact facts in code. Treat text claiming “ignore your instructions” as untrusted input; model confidence is not an authorization check. [Source: Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13)

The homepage's speed, cost, and reliability claims do not establish performance on these demos. The useful question here is empirical: **does this improve decisions or reduce manual effort compared with a simple baseline, at an acceptable cost?** [Vendor positioning](https://typesafe.ai/)

## Pick a learning path

1. **Repro Coach:** learn Noul and explicit uncertainty handling.
2. **CSV Field Matchmaker:** learn closed-set Choice and application constraints.
3. **Interruption Budget:** learn Score and compare thresholds against missed-important-event errors.

For automation first, choose **Follow-up Promise Catcher** instead of step 2. The [idea catalog](demo-ideas.md) includes the scope and acceptance experiment for each. Stay with rules or forms if they solve the problem just as well.
