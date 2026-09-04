# Tests

Tests use Python's standard-library `unittest` discovery and are grouped by
purpose:

- `validation/` converts and validates simple programs and checks focused
  properties of their emitted QIR.
- `statevector/` compares unmeasured programs with Qrisp and Selene/QuEST.
- `semantics/` compares deterministic measurement behavior.
- `diagnostics/`, and `generation/` cover expected failures, and checked-in
  fixture freshness.

Each case owns a directory containing `test_case.py` and `input.mlir`. For
Qrisp-based cases, `test_case.py` also contains `qrisp_program` and its semantic
expectations; `input.mlir` is the checked-in generated form. Shared conversion
and simulator mechanics live in `support.py`.

Run the complete suite:

```sh
./venv/bin/python tests/run_tests.py
```

Run one category or case:

```sh
./venv/bin/python -m unittest discover -s tests/validation -t . -v
./venv/bin/python -m unittest tests.validation.reset_array.test_case -v
```

Regenerate every Qrisp-based `input.mlir` after changing a colocated
`qrisp_program`:

```sh
./venv/bin/python tests/generate_qrisp_fixtures.py
```
