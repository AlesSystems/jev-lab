# Interruption budget

Interruption budget sorts synthetic events into Attention now, Review, and Digest. An event-type lookup is the baseline. Quiet hours and a page flag are code rules and run before either reading is shown. The page does not send a notification.

Without `TYPESAFE_API_KEY`, the page stays on that baseline. With the key, the server asks `jev-1.13.0` to score the remaining events. Low confidence goes to review. Quiet hours skip the call. A page flag stays in Attention now and is not sent to Jev. A failed call puts the other events in review instead of using the fixture lane. The key stays on the server.

```sh
python3 demos/interruption_budget/interruption_budget.py serve
TYPESAFE_API_KEY=... python3 demos/interruption_budget/interruption_budget.py serve
```

Open http://127.0.0.1:8767

```sh
python3 -m unittest demos/interruption_budget/test_interruption_budget.py
```
