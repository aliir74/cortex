# how-to-html reference: narrative

On-demand reference for `how-to-html`. **Read this before writing any report, analysis,
review, investigation or decision artifact, and before choosing a single section heading.**
A report is not a container for findings; it is an argument that arrives somewhere. The
shape below is what makes it readable by someone who was not in the session that produced it.

Scope: reports and analysis only. Plans (`/create-plan`), slide decks (`/make-slides`),
verification reports and custom editor UIs have their own
shapes and are exempt.

## Contents

1. [The spine](#the-spine): the six parts every report has, in order
2. [The orientation line](#the-orientation-line): what it is, and what it is not
3. [The two-minute version](#the-two-minute-version): the block that has to stand alone
4. [The actions block](#the-actions-block): three buckets, empty ones omitted
5. [Severity tiers](#severity-tiers): blocking, major, context
6. [The connective rule](#the-connective-rule): what makes sections a thread instead of a pile
7. [Section budget](#section-budget): when to split instead of adding a heading
8. [The five middles](#the-five-middles): pick one before writing anything

## The spine

Six parts, always, in this order. Only part 5 varies.

| # | Part | Rule |
|---|---|---|
| 1 | **Orientation** | One line. The question, who asked, when, what was read. |
| 2 | **The answer** | The verdict, recommendation or number. The `h1` or immediately under it. |
| 3 | **Two-minute version** | Standalone. Top-tier findings only, plus what the reader must decide. |
| 4 | **Actions** | What to do, above the evidence. |
| 5 | **The middle** | One of the five shapes below. This is the only part that varies. |
| 6 | **Detail** | Collapsed. Reference material, long tables, charts, appendices. |

Parts 3 and 4 sit **above** the evidence, not below it. The evidence exists to justify the
answer and the actions; a reader who accepts both never has to reach it. Burying actions at
the bottom forces every reader to read everything to find out what is being asked of them.

## The orientation line

One line, before or inside the hero. It answers: what question, asked by whom, when, and
what was read to answer it. It is a **locator**, not a preamble. Its job is to stop the
reader reconstructing the artifact's purpose from its findings.

Good:

> Spike PLAT-412, asked by the platform lead last Tuesday. Read the epic, its 12 subtasks,
> the architecture doc, the backend, and current vendor docs.

> Why the CRM batch-sync call started returning 403 on Monday, from a support escalation.
> Read the prod ingress logs, PR #132, and the permission class it changed.

Not this, which restates the brief instead of locating it:

> The platform lead has asked us to evaluate whether the proposed email platform architecture
> is the right approach for our needs, considering both the technical merits and the
> alternatives available in the current market.

Not this, which narrates method instead of naming the source:

> This analysis was conducted by first reviewing the available documentation, then
> examining the codebase, and finally researching vendor options before forming a view.

## The two-minute version

A bounded block directly under the answer. It must survive being read **alone**, because
often it will be: no `see below`, no `as discussed above`, no dependency on later context.

- At most **three** findings, all `blocking` tier, ranked by consequence.
- Plus the decision the reader owns, if there is one.
- No new evidence. Anything here is stated again in full in the middle.

If more than three findings feel essential, the tiering is wrong, not the limit. Re-tier
them; only what actually stops a decision is `blocking`.

## The actions block

Three buckets, a shape the reader parses fast. **Omit a bucket entirely when it is empty**; never write "none".

- **Already done** so it is not asked for twice.
- **Only you can do** the judgement calls, the approvals nobody else can give, the things
  needing access or authority the writer lacks.
- **Needs your approval** work that is drafted and ready, waiting on a yes.

Each entry is one line naming the action, not a description of the problem behind it.

## Severity tiers

Three tiers. A blocking finding and a minor note must be **visually** distinguishable at a
glance, not merely labelled: different border, weight or badge, so the reader can triage
without reading.

| Tier | Means | Appears in the two-minute block |
|---|---|---|
| `blocking` | Stops a decision, a start, or a merge until resolved. | Yes, this tier only |
| `major` | Does not stop anything, but changes the shape of the answer. | No |
| `context` | True and worth knowing; changes nothing. | No |

The common error is inflation. If everything is `blocking`, nothing is, and the two-minute
block becomes the whole report again. Most findings are `major`.

## The connective rule

**Every section in the middle opens with one sentence saying why it follows the previous
one.** This single rule is what turns a pile of findings into a thread. Without it, section
order is invisible and the reader assumes it is arbitrary, because usually it is.

Good connectives carry the logic forward:

> Those three defects are all ordering problems. The next one is not: it is a gap in what
> the plan covers at all.

> That settles whether the stack works. It says nothing about whether we can afford it.

> Everything above came from the ticket. The rest came from the code, and it disagrees.

Bad, because it only restates the heading and could sit above any section:

> Now let us look at the alternatives.

## Section budget

Five to seven sections in the middle. Past seven, the reader stops holding the structure
and starts scrolling blind.

Over budget means **split, never shrink**: promote the material into an overview section
plus a collapsed detail section. Do not solve it by making sections shorter, and never by
lowering the type size or merging two unrelated findings under one heading.

## The five middles

**Pick one before any section exists**, and record it in a comment on the first line of the
HTML so a later edit keeps the same shape:

```html
<!-- report-middle: verdict -->
```

The choice is what determines section order. Made after the sections exist, it is not a
choice, it is a label on whatever order happened.

### 1. Investigation

Something broke, and the report explains it.

1. **Symptom and blast radius** what is failing, since when, who or what is affected.
2. **What was ruled out** each candidate cause and the evidence that killed it.
3. **The actual cause** the mechanism, named precisely enough to fix.
4. **The fix** what to change, and what it does not cover.

The ruled-out section is **required**, not optional. It is what stops the reader spending
their first ten minutes re-asking questions already answered, and it is the part most often
dropped because it feels like showing work.

### 2. Verdict

Reviewing someone else's plan, estimate, claim or diff.

1. **The claim** stated as its author would state it, fairly.
2. **What holds** the parts that survive scrutiny.
3. **What does not hold** with the evidence against each.
4. **What is missing** things absent from the claim entirely.

Order matters here more than anywhere. Leading with what is missing, before establishing
what holds, reads as hostile and buries the agreement, so the author defends instead of
reading. Establish the agreement first and the disagreement lands.

### 3. Options

A decision is pending and the report makes it.

1. **The decision and its constraints** what is being chosen, and what bounds the choice.
2. **The contenders** scored against **one shared set of criteria**.
3. **Why the winner wins** the specific criteria that decided it.
4. **What would change the answer** the conditions under which this flips.

Criteria must be identical across contenders. Scoring each option on the dimensions where
it happens to look good is theatre, and it is obvious to the reader.

### 4. Research

Synthesis from sources.

1. **The question** as asked, and how it was scoped.
2. **What the sources agree on** the settled ground.
3. **Where they disagree** and which to believe, with the reason.
4. **What it means for us** the translation to this situation.

The last section is **required**. A synthesis that stops at what the sources said is a
literature review; the reader wanted the implication, and they cannot derive it because
they have not read the sources.

### 5. Audit

A survey or sweep across many things.

1. **Scope and method** in one line: what was covered, how, and what was not.
2. **What is healthy** the things checked and found fine.
3. **What is not** ranked by severity.
4. **What to act on** the subset worth doing something about.

The healthy section is **required**, because without it the reader cannot tell coverage
from omission. A finding absent from an audit could mean checked-and-fine or never-looked,
and those are very different.

## Picking a middle

Match on what the task actually was, not on the subject matter.

| If the task was | Middle |
|---|---|
| Explain why something is failing or behaving wrongly | Investigation |
| Assess someone else's plan, estimate, PR, or claim | Verdict |
| Choose between options, or recommend build versus buy | Options |
| Answer a question from external sources | Research |
| Sweep a set of things and report the state | Audit |

**Fallback:** when a report genuinely fits none of the five, use **Options** if a decision
is pending and **Audit** otherwise. Do not invent a sixth shape silently. If a sixth shape
is genuinely needed more than once, add it here deliberately rather than improvising it
twice.
