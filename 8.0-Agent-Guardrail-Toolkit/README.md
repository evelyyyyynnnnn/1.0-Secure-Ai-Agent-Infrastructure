# 8.0 — Agent Guardrail Toolkit

A small, embeddable runtime policy layer that sits between an agent and its
tools. Intended as the reusable component that projects 3.0–7.0 all depend on
rather than each reimplementing.

## Problem

Guardrails are usually written per-application, in the prompt, and are therefore
bypassable by the same channel that carries the attack. Enforcement has to live
outside the model, at the call boundary.

## Scope

- **Policy engine** — declarative allow/deny over (tool, argument, context),
  evaluated before dispatch, deny-by-default.
- **Egress control** — restrict network destinations and outbound payload shape;
  catch exfiltration through a tool the agent is legitimately allowed to use.
- **Injection detection** — screen untrusted content entering context, and mark
  it so downstream policy can refuse to act on instructions from it.
- **Rate and budget limits** — per-task ceilings on calls, spend, and blast
  radius.
- **Structured trace** — emit the decision record consumed by 4.0.

## Non-goals

Not a model, not a proxy service, not a hosted product. A library with a policy
file.

## Status

Scaffold. No implementation yet.
