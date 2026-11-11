# payrecon in n8n: M-Pesa payment matching with human approval

A small n8n version of [payrecon](https://github.com/mikekeror-rgb/payrecon): it matches an incoming
M-Pesa payment to an open invoice. Code makes every exact match; Claude is asked only about the
payments code cannot match, a guardrail checks its answer, and a person approves before anything
is applied. Every decision goes into an audit log.

## Flow

1. **Payment received** (webhook `POST /webhook/mpesa-payment`).
2. **Match in code**: rejects invalid payments, flags a repeated transaction and a second payment
   for an already-paid invoice, applies an exact reference-and-amount match, and lists the open
   invoices with the same amount as candidates.
3. **Exact match** → applied and logged, no model call.
4. **Candidates but no exact match** → **Ask Claude** (Haiku) to pick one candidate or `null`,
   answering in JSON with a one-line reason.
5. **Check the answer**: the guardrail accepts only an invoice that is one of the candidates, and
   treats anything unreadable as "no suggestion".
6. **Ask for approval**: the webhook replies with the reason, the suggestion and approve/reject
   links, then **Wait for a person** pauses the run until one is clicked.
7. **Record decision**: applies only an approved suggestion and logs the decision either way.

`GET /webhook/mpesa-audit` returns paid invoices and the audit log. `POST /webhook/mpesa-reset`
clears them (test data only).

## Run it

n8n needs Node 20 or 22:

```bash
brew install node@22
PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx -y n8n
```

Open http://localhost:5678, import `payrecon-n8n.workflow.json`, create a **Header Auth**
credential named `Anthropic API key` (header `x-api-key`, value your key), select it on the
**Ask Claude** node, save, and set the workflow to **Active**.

## Evaluate

```bash
python3 run_eval.py
```

Deterministic code paths must all pass. Model suggestions are scored separately, because a model's
answer can vary between runs; the guardrail means a wrong suggestion can only ever reach a person,
never the ledger.

Test data is fictional.
