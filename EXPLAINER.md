# 🧠 What We're Building — Explained Simply
> *A plain-language breakdown of our project: the problem, the solution, the tech, and why we win.*

---

## 🐟 Part 1: The Problem — Your Smart Friend Has Amnesia

Imagine you have a **super-smart best friend**. She knows everything — coding, design, math, debugging. You spend all of Monday with her building your dream app. You explain how every piece fits together. She helps you fix a really tricky bug. It's an amazing day.

Then she goes to sleep.

Tuesday morning she wakes up and **remembers absolutely nothing.** Zero. You have to explain everything again — what the app does, how the files are connected, what bugs you already fixed, what rules you follow. Every single day. From scratch.

**That friend is an AI coding assistant** like Claude or ChatGPT or Cursor.

This problem has a real name: **Context Amnesia.** And it's costing developers enormous amounts of time and money every single day.

---

## 🔍 Part 2: Why "Just Give It a Better Memory" Doesn't Work

The obvious fix sounds simple: *just keep feeding it the old conversations!* Dump everything into the AI's memory at the start of each session.

But here's the thing — **AI brains work differently from human brains.**

An AI reads your entire conversation at once, like reading a book from cover to cover before answering. The longer the book, the harder it is to remember the stuff in the middle. Scientists tested this: when a context window is more than half full, accuracy for information buried in the middle **drops from 75% to 55%.**

Imagine you told your friend 1,000 things. She'd remember the first few things you said and the last few things. Everything in the middle? Gone. That's called the **"Lost in the Middle" problem.**

So dumping everything in doesn't fix amnesia — it just creates a different, slower, more expensive kind of confusion.

There's also a cost problem. Every word you send to an AI costs money (in API tokens). Resending your entire codebase every morning is like reprinting a 500-page book every time you want to ask a question. Wildly wasteful.

---

## 💡 Part 3: Our Goal — Give AI a Real, Structured Brain

We want to build something that works like **how humans actually remember things.**

Think about how YOU remember your school project:
- You don't memorize every sentence of every conversation you've had about it.
- You remember the **key facts**: "the login button calls the database," "we use blue for buttons," "we fixed that crash last Thursday."
- When you need details, you know *where to look* — you go find the specific notebook or file.
- You understand **how things connect** — "if I change the button, it affects the login flow, which affects the database call."

That's what we're building for AI. A **persistent memory engine** that:

1. **Remembers key facts** across sessions (not just raw text dumps)
2. **Understands structure** — how files, functions, and components are connected
3. **Retrieves smartly** — gives the AI only what it needs, not everything at once
4. **Never forgets** — even when you close the app and come back a week later

---

## 🏗️ Part 4: What We're Actually Building (The Architecture)

We use **three storage layers**, each doing a different job. Think of it like how your brain has different kinds of memory.

### Layer 1 — The Diary 📓 (SQLite Database)
Every action the AI takes gets written down in a timestamped diary. "At 3:04pm, read file main.rs. At 3:06pm, fixed a Mutex bug. At 3:09pm, user approved the change."

This is an **append-only log** — we never delete history, we only add to it. This means we can always go back and ask "what exactly happened on Tuesday?" It's like a flight recorder for your coding session.

**Tech used:** SQLite with FTS5 (Full Text Search) — blazing fast, runs locally, zero setup.

### Layer 2 — The Fuzzy Memory 🌫️ (Vector Database)
Sometimes you want to search vaguely — "what did we do with authentication last week?" You don't remember the exact file or function name.

We take all our diary entries, compress them into short summaries using AI (Claude Haiku, the fast cheap model), then convert those summaries into **numbers that represent meaning** (called embeddings). Sentences that mean similar things get similar numbers.

Now when you ask "anything about login?" the system finds the most *meaningfully similar* entries — even if the exact word "login" wasn't used.

**Tech used:** ChromaDB (runs in-process, no server needed) + Ollama embeddings (free, local, private).

### Layer 3 — The Relationship Map 🕸️ (Knowledge Graph)
This is our **secret weapon** and what makes us different from everyone else.

Code isn't just words. It's a **web of relationships.** A button in `App.jsx` calls a function in `api.js` which invokes a Rust command in `main.rs` which locks a variable called `AppState`. That chain of causality is what an AI needs to understand to be truly helpful.

A knowledge graph stores this as **nodes** (things) and **edges** (relationships between things):

```
[SettingsButton in App.jsx]
        ↓ CALLS
[invoke("save_settings")]
        ↓ TRIGGERS
[save_settings() in main.rs]
        ↓ LOCKS
[AppState Mutex]
```

Now when you ask "why does changing the settings button break the backend?", the AI can **traverse this map** and give you a precise, correct answer — not a guess.

We also track **time**: when a function is deprecated, we don't delete it. We mark it as *invalidated* and link it to the new function. So the AI knows "this old pattern existed, it was replaced, here's why." It never regresses to old broken patterns.

**Tech used:** NetworkX (Python graph library, no infrastructure, serializes to JSON).

---

## 🤝 Part 5: How the AI Accesses All This — MCP

We expose all three layers through a **local MCP server** (Model Context Protocol — an open standard built by Anthropic).

Think of MCP like a universal remote control. We build it once, and it works with:
- Claude Code ✓
- Cursor IDE ✓
- VS Code ✓
- Google Antigravity ✓

The AI has access to exactly **3 tools**, in a hierarchy:

| Tool | What it returns | Token cost |
|------|----------------|------------|
| `search_index(query)` | Just titles + IDs of relevant memories | ~50 tokens |
| `get_timeline(id)` | Events before/after a specific memory | ~200 tokens |
| `retrieve_node(id)` | Full raw details of one memory | ~500 tokens |

The AI starts with the cheap search, drills down only if it needs more. This is called **Progressive Disclosure** — like a doctor asking "where does it hurt?" before ordering a full body scan. We save up to **90% of context tokens per session.**

---

## 🪞 Part 6: The Dashboard — You Can See What AI Knows

A web dashboard runs at `localhost:37777`. It shows you:

- A **visual graph** of your entire codebase as AI understands it — nodes are files and functions, edges are relationships
- Every memory entry, searchable and readable
- **Full edit control** — you can correct, delete, or add anything the AI believes about your project

Why does this matter? Because AI memory was always a "black box." You didn't know what it remembered or misremembered. We make it fully transparent and auditable. **You're always in control.**

---

## ⚔️ Part 7: How We're Different From Competitors

There are existing AI memory tools. Here's why we beat them:

### Mem0
✅ Good at storing facts  
❌ **Overwrites history** — when a decision changes, the old one is gone forever. No record of *why* things changed.  
❌ No knowledge graph — can't understand code structure

### Zep
✅ Has temporal graph (our inspiration!)  
❌ **Massive infrastructure overhead** — requires complex setup, not suitable for a local dev tool  
❌ Too expensive and complex for indie developers

### Supermemory
✅ Smart semantic features  
❌ **Proxy-based** — all your code goes through their server. Privacy nightmare for proprietary codebases.  
❌ You lose control over what gets remembered

### Claude-Mem
✅ Local-first, good compression  
❌ **No knowledge graph** — can't map structural code relationships  
❌ No dashboard — still a black box  
❌ Only works with Claude Code

### Us 🏆
✅ **Temporal knowledge graph** — understands code structure AND history  
✅ **Fully local** — your code never leaves your machine  
✅ **Visual dashboard** — full transparency and control  
✅ **MCP universal** — works with every major IDE  
✅ **Progressive disclosure** — 90% token savings  
✅ **Scoped by git repo** — zero memory bleed between projects  
✅ **Ephemeral mode** — experiment without polluting your memory

---

## 🎯 Part 8: The One-Sentence Pitch

> **We give AI coding assistants a permanent, structured, auditable brain — so they never forget your codebase, understand how your code connects, and get smarter every session instead of starting from zero.**

---

## 🔬 Part 9: The Tech Stack at a Glance

| What | Tool | Why |
|------|------|-----|
| Event hooks | Python CLI | Non-invasive, works with any IDE |
| Diary/log | SQLite + FTS5 | Zero infra, millisecond search |
| Fuzzy memory | ChromaDB | Embedded, no server needed |
| Embeddings | Ollama (local) | Free, private, offline |
| Relationship map | NetworkX | No infra, fully serializable |
| AI compression | Claude Haiku | Cheapest + fastest model |
| Universal adapter | FastMCP (Python) | Works with all MCP-compatible IDEs |
| Dashboard | React + Cytoscape.js | Beautiful graph visualization |

---

## 🚀 Part 10: Why This Wins the Hackathon

The hackathon judges are looking for:

1. **Clear problem** ✓ — Context amnesia costs developers real time and money every day
2. **Strong hypothesis** ✓ — A neurosymbolic (graph + vector + log) local-first memory layer solves it
3. **Demonstrated utility** ✓ — Live demo: show AI forgetting without us, then remembering with us
4. **Differentiation** ✓ — No competitor has all of: knowledge graph + local + auditable + universal MCP + progressive disclosure

The demo moment: introduce a Tauri Mutex bug, fix it, end the session, start fresh — watch the AI find the previous fix automatically and avoid repeating the mistake. That's the "whoa" moment that wins rooms.

---

*Built for Campus Fund x ECell Hackathon — Idea 6: Memory Layer for Agentic AI*