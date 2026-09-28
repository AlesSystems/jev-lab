# Interruption budget

Interruption budget sorts synthetic events into Attention now, Review, and Digest. An event-type lookup is the baseline. Quiet hours and a page flag are code rules and run before either reading is shown. The page does not call Jev, and it does not send a notification.

```sh
python3 demos/interruption_budget/interruption_budget.py serve
```

Open http://127.0.0.1:8767

```sh
python3 -m unittest demos/interruption_budget/test_interruption_budget.py
```
