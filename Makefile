CC = cc
CFLAGS = -O2 -std=c99 -Wall -Wextra -Wpedantic
LDLIBS = -lm

.PHONY: all clean test test-c test-python parity evaluate benchmark sanitize
all: wolfe

wolfe: wolfe.c
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

test: test-c test-python

test-c: wolfe
	python3 tests/contracts.py
	python3 tests/parser_contracts.py
	python3 tests/state_contracts.py
	python3 tests/custom_contracts.py
	python3 tests/fuzz_smoke.py

test-python:
	python3 tests/contracts.py --engine 'python3 wolfe.py'
	python3 tests/parser_contracts.py --engine 'python3 wolfe.py'
	python3 tests/state_contracts.py --engine 'python3 wolfe.py'
	python3 tests/custom_contracts.py --engine 'python3 wolfe.py'

evaluate: wolfe
	mkdir -p .work
	python3 tests/evaluate.py --python-engine 'python3 wolfe.py' --report .work/evaluation.json

parity: wolfe
	mkdir -p .work
	python3 tests/parity.py --fixtures tests/heldout.jsonl tests/final_holdout.jsonl tests/confirmation_holdout.jsonl --report .work/parity.json

benchmark: wolfe
	mkdir -p .work
	python3 tests/benchmark.py --python-engine 'python3 wolfe.py' --report .work/benchmark.json

sanitize: wolfe.c
	$(CC) -O1 -g -std=c99 -Wall -Wextra -fsanitize=address,undefined -fno-omit-frame-pointer $< -o wolfe-sanitize $(LDLIBS)

clean:
	rm -f wolfe wolfe-sanitize
