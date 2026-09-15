# WOLFE

**Weightless Ontological Language Function Engine**

> I solve problems.

A neural tool caller. One C file. Zero pretrained parameters.

The model files are text. You can read them. You can edit them. WOLFE rebuilds
its numerical field from them when it starts. There is no checkpoint to download,
no training command to discover, and no API secretly doing the work.

Some problems need a billion parameters. Selecting one of your six functions
deserves the courtesy of trying something smaller first.

## Run the wolf

```sh
cc -O2 -std=c99 wolfe.c -o wolfe -lm
./wolfe 'play music by Portishead'
```

The response includes:

```json
{"calls":[{"name":"play_music","arguments":{"query":"Portishead"}}],"status":"call","confidence":0.984372}
```

`confidence` is an activation score, **not a calibrated probability**. The engine
returns a decision; your application executes the tool.

The C body needs a C99 compiler, the C standard library and `libm`. The readable
Python body uses only the standard library:

```sh
python3 wolfe.py 'play music by Portishead'
```

Or keep the Python field loaded in your application:

```python
from wolfe import Wolfe

wolf = Wolfe("tools.json", "examples.jsonl")
result = wolf.call("play music by Portishead", reasoning=True)
```

## Your functions. Your language.

The starter surface has six ordinary functions:

| Tool | Arguments |
| --- | --- |
| `get_weather` | `city`, optional `unit` |
| `set_timer` | `seconds` |
| `cancel_timer` | none |
| `play_music` | `query` |
| `pause_music` | none |
| `create_note` | `text` |

`tools.json` describes the interface. `examples.jsonl` supplies phrases and
argument boundaries. For example:

```json
{"text":"play music by {query}","tool":"play_music","arguments":{"query":"{query}"}}
{"text":"do not play music","tool":null,"arguments":{}}
```

`{query}` is a span to copy, not a word the user must type. Include multiple ways
to express an action, near-neighbour actions, and examples that should cause no
call. Literal example arguments can supply values when the example matches.

Change those files and restart. No compiler or training step is involved in
changing the tool vocabulary. An unrelated interface is included:

```sh
./wolfe --tools examples/custom_tools.json \
        --examples examples/custom_examples.jsonl \
        'set kitchen lamp to 30'
```

It declares package delivery, room lighting and device power. The C source
contains none of these tool names.

The supported JSON Schema subset is deliberately small: flat object arguments
with `string`, `number`, `integer` and `boolean` properties; `required`, `enum`,
numeric `minimum`/`maximum`, and `default`. Only declared properties are emitted.
Nested objects, arrays, references, unions and unsupported constraints are
rejected. OpenAI-style `{"type":"function","function":{...}}` declarations
and `input_schema` are accepted as wrappers around this same subset.

Two optional schema extensions keep extraction declarative:

- `"x-unit":{"minute":60,"minutes":60}` converts quantities to a property's
  base unit.
- `"x-aliases":{"true":["on","enabled"],"false":["off","disabled"]}` maps
  phrases to boolean or enum values.

## What is actually neural here?

The corpus constructs token vectors from signed lexical projections and
distance-weighted co-occurrence. These are the metaweights: numerical
connections derived from the supplied text.

Query tokens activate example units through content attention. Ordered token
pairs contribute predictive evidence — **prophecy**. Example activity excites
tool units. Those units feed back into the semantic context and settle through
six nonlinear recurrent steps with lateral inhibition — **destiny**. A no-call
unit competes alongside the functions.

The settled field selects the tool. Generic span alignment then fills arguments;
ordinary code validates and serializes them. A malformed brace is not a deep
thought.

Concrete argument values in construction examples are replaced by slots before
the field is built. An example containing a particular city or brightness does
not require the next request to use that same city or number.

There is no transformer hiding in the basement. WOLFE uses a small recurrent
associative network. Its tokenizer uses words and character-trigram similarity,
not BPE. Numerical coefficients are fixed algorithm constants; token vectors and
tool attractors are rebuilt from the definitions. Neither is gradient-trained.

PostGPT and Q are the ancestors, not dependencies. WOLFE borrows their
corpus-to-field idea and gives it a smaller output language. See
[the engineering record](docs/ENGINEERING.md) for the implementation decisions.

## Reasoning you can point at

```sh
./wolfe --reasoning 'play music by Portishead'
```

This adds actual evidence: competing tool scores, the strongest example,
matched input spans, ordered-pair evidence, the activation trajectory, and the
source of each argument. For the request above, the useful part is `play music
by` → `play_music`, with `Portishead` copied from the input.

It is an inspection of the computation, not a generated internal monologue.
Span offsets are UTF-8 **byte offsets**. `--reasoning` does not change the call.

## State with a job

Normal inference does not write anything. Optional feedback keeps two bounded
counters per tool:

```sh
./wolfe --state user.state.json --feedback accepted 'play Rammstein'
./wolfe --state user.state.json --feedback rejected 'play Rammstein'
./wolfe --state user.state.json 'play Portishead'
```

Explicit acceptance/rejection modestly adjusts a tool's reliability multiplier.
WOLFE never treats its own prediction as confirmation. Counters are halved at
saturation; the file is replaced atomically and tied to the exact definition
bytes. Delete it to restore the original field. After editing definitions,
start with a new state file.

This is a small feedback bias, not evidence of calibrated probabilities or
continuous semantic learning. It is not a training mode.

## Pipe it into something useful

```sh
printf '%s\n' '{"text":"set a timer for two minutes"}' \
              '{"text":"pause the music"}' | ./wolfe --batch
```

Batch mode builds the field once and emits one JSON response per input line.
Possible statuses are `call`, `no_call`, `ambiguous`, `missing_arguments` and
`error`. A request emits at most one call. Multiple requested actions are outside
this first interface; ambiguity and negation remain part of the measured error
surface. Missing required arguments are reported, not invented.

## Make it answer in court

```sh
make test
make evaluate
make sanitize
ASAN_OPTIONS=detect_leaks=0 python3 tests/fuzz_smoke.py --engine ./wolfe-sanitize
```

The repository includes independently authored language fixtures, strict parser
and schema contracts, arbitrary tool-vocabulary replacement, explicit-state
contracts, randomized input checks, and C/Python parity checks. The engineering
set guides fixes. A first blind set exposed four further errors; its original
result is retained. After bounded repairs, a separately authored confirmation
set is opened. Reports distinguish routing, arguments, complete responses and
false calls. They also identify verbatim overlap with the construction corpus.

Three selectable modes share the same definitions and argument machinery:
`keyword` (literal IDF overlap), `field` (static corpus relations) and `neural`
(attention plus recurrent field). Comparisons are measured, not decided by the
name on the executable.

Current measurements and remaining failures belong in [RESULTS.md](docs/RESULTS.md).
No claim about an ARM phone or microcontroller follows from an x86 benchmark.

The supplied C body compiles to **75 KiB**, peaks at **5.38 MiB RSS**, and takes
**1.51 ms median** per warm request on the measured Linux host. The fresh
confirmation set gives **29/32 complete responses**, including two false calls;
the developer-visible engineering set gives 116/119. Small is measured. Perfect
is not claimed.

## The boundary

This is a narrow, editable tool caller. The supplied corpus is English. UTF-8
argument text is preserved, but that is not a multilingual benchmark. Unknown
semantics do not appear from an empty file: supply the vocabulary and examples
your interface needs.

The first body bounds requests to 2,047 bytes and 96 tokens, tool count to 64,
properties per tool to 16, and vocabulary to 4,096 tokens. Limits are explicit
errors, not silent truncation. Definitions are bounded to 4 MiB per file; the
2,048-example limit includes synthetic tool-name/description examples.

The wolf doesn't need to know everything. It needs to know which function you
meant, what belongs in its arguments, and when the evidence is insufficient.

## Family

- [PostGPT](https://github.com/ariannamethod/postgpt) — corpus-derived metaweights.
- [Q](https://github.com/ariannamethod/q) — the more elaborate relative.
- [Molequla](https://github.com/ariannamethod/molequla) — the ecosystem that made
  this worth building; WOLFE's starter interface is independent of it.
- [Microkarpathy](https://github.com/ariannamethod/microkarpathy) — family manners.
- [Cactus](https://github.com/cactus-compute/cactus) — Needle made the small
  tool-caller question concrete. No head-to-head Needle benchmark is claimed.

Named after Winston Wolfe. GPL-3.0; see [LICENSE](LICENSE).

**The joke has become an architecture.**
