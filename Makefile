CC = cc
CFLAGS = -O2 -std=c99 -Wall -Wextra -Wpedantic
LDLIBS = -lm

.PHONY: all clean test test-c test-python parity evaluate evaluate-v2 benchmark sanitize
all: wolfe

wolfe: wolfe.c
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

test: test-c test-python
	python3 tests/state_interop.py

test-c: wolfe
	python3 tests/contracts.py
	python3 tests/parser_contracts.py
	python3 tests/state_contracts.py
	python3 tests/custom_contracts.py
	python3 tests/semantic_contracts.py
	python3 tests/correction_contracts.py
	python3 tests/correction_state_validation.py
	python3 tests/embedding_contracts.py
	python3 tests/fuzz_smoke.py

test-python:
	python3 tests/contracts.py --engine 'python3 wolfe.py'
	python3 tests/parser_contracts.py --engine 'python3 wolfe.py'
	python3 tests/state_contracts.py --engine 'python3 wolfe.py'
	python3 tests/custom_contracts.py --engine 'python3 wolfe.py'
	python3 tests/semantic_contracts.py --engine 'python3 wolfe.py'
	python3 tests/correction_contracts.py --engine 'python3 wolfe.py'
	python3 tests/correction_state_validation.py --engine 'python3 wolfe.py'

evaluate: wolfe
	mkdir -p .work
	python3 tests/evaluate.py --python-engine 'python3 wolfe.py' --report .work/evaluation.json

evaluate-v2: wolfe
	mkdir -p .work
	python3 tests/evaluate.py --fixtures tests/v2_engineering.jsonl --report .work/v2-engineering.json
	python3 tests/evaluate.py --fixtures tests/v2_blind.jsonl --report .work/v2-blind.json

parity: wolfe
	mkdir -p .work
	python3 tests/parity.py --fixtures tests/heldout.jsonl tests/final_holdout.jsonl tests/confirmation_holdout.jsonl tests/v2_engineering.jsonl tests/v2_blind.jsonl --reasoning full --report .work/parity-full.json
	python3 tests/parity.py --fixtures tests/heldout.jsonl tests/final_holdout.jsonl tests/confirmation_holdout.jsonl tests/v2_engineering.jsonl tests/v2_blind.jsonl --reasoning compact --report .work/parity-compact.json
	python3 tests/parity.py --fixtures tests/heldout.jsonl tests/final_holdout.jsonl tests/confirmation_holdout.jsonl tests/v2_engineering.jsonl tests/v2_blind.jsonl --reasoning off --report .work/parity-off.json

benchmark: wolfe
	mkdir -p .work
	python3 tests/benchmark.py --python-engine 'python3 wolfe.py' --report .work/benchmark.json

sanitize: wolfe.c
	$(CC) -O1 -g -std=c99 -Wall -Wextra -fsanitize=address,undefined -fno-omit-frame-pointer $< -o wolfe-sanitize $(LDLIBS)

clean:
	rm -f wolfe wolfe-sanitize
