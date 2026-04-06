# Retail Support Example

This example demonstrates a multi-purpose evaluation setup for:

- recommendation tasks
- customer support responses
- retrieval-grounded answers (RAG-style)
- simple agent workflows (tool usage simulation)
- structured output validation

## Purpose

This example is designed to showcase the flexibility of the eval engine beyond a single domain.

It combines multiple real-world assistant behaviors into a single evaluation pack.

## Task Categories

- recommendation
- support_policy
- order_support
- agent_workflow

## Data Files

- `dataset.json` — evaluation cases across multiple categories
- `rubric.json` — scoring logic and critical gates
- `knowledge_base.json` — policy and support documents
- `catalog.json` — product data for recommendations
- `orders.json` — mock order data
- `tool_scenarios.json` — simulated tool responses
- `expected_outputs.json` — deterministic evaluation hints

## Status

Initial scaffold only. Logic will be wired in upcoming commits.