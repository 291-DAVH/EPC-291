# ADR-0018: Use of Claude is metered per organization and limited by a monthly allowance

Status: Accepted (design; not implemented yet). Date: 2026-10-24. Extends ADR-0016.

## Context
The platform uses the Claude API for one optional function today: the automatic analysis of what the customer sends (`intake/analyzer.py`, key in `ANTHROPIC_API_KEY`). Customers never subscribe to Claude: the platform pays the API per token. Cost has to be visible, bounded and attributable to the organization that caused it, without making the platform depend on the AI (every other function works without it).

## Decision
- **Who pays.** The platform pays the API with its own key; every organization has a **monthly allowance of credits included in its plan**. No billing is built into the platform for now. The team can export the consumption per organization to invoice outside the platform if it ever decides to charge for more.
- **Unit.** Customers see **credits** (1 credit = US$0.01 of cost to the platform, adjustable), not dollars, so that changing the model or the price does not change what the customer reads.
- **Metering.** Every call is recorded in the database (table `ai_usage`, with `organization_id`): organization, project, person, feature, provider, model, input / output / cache-read / cache-write tokens, cost, request id and result. The cost is computed when the call is recorded from a **versioned price table** kept in one file; that table is edited when the provider changes its prices. The per-project JSON log that exists today is replaced by this table (single source of truth).
- **Limits, in four layers.**
  1. *Per organization:* a monthly credit limit; a notice at 80 %, and at 100 % the AI functions **stop** with a clear message until the next month or until the team raises the limit.
  2. *Per call:* the cost is estimated before spending (token counting) and shown with the month's consumption in the confirmation the person already gives; `max_tokens` is capped.
  3. *Against abuse:* a maximum number of calls per hour per organization; only the owner or an administrator may spend, a member only when allowed.
  4. *Global:* a monthly budget for the whole platform and an emergency switch for the team.
- **Visibility.** The owner sees the use of the month (by project and function) and the limit; the team sees every organization in the console, adjusts limits and exports the consumption.
- **Provider.** A module `ai` with a provider interface (Claude by default), so that another provider, for example an open-weights model on the platform's own server, can be plugged in without touching the features. Without a key or provider the AI functions are simply not offered.
- **Use of the model.** Features ask for structured output with a strict schema and set a low reasoning effort for extraction; the cheapest model that passes the feature's checks is the default, chosen by measurement.

## Known defect to fix with this work
The current analyzer forces a tool call (`tool_choice` of type `tool`) on the default model `claude-sonnet-5-5`; the current API rejects forced tool use on that model with a 400. The tests use a fake client, so it has not shown. It must be fixed (strict-schema structured output) and checked against the real API before the function is offered.

## Consequences
- (+) Cost is bounded per organization and globally, attributable and visible; nothing is billed to customers yet and nothing is lost if it is.
- (-) The team carries the API cost of the allowances; the allowance sizes have to be chosen and revisited with real usage.
- (-) A table and a module more to maintain, in exchange for the removal of the per-project log.
