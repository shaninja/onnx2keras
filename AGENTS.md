# Agent Guide — shaninja/onnx2keras

This file is the shared knowledge base for all coding agents (Claude, Codex, etc.) working on this fork.
Keep it up to date whenever you learn something non-obvious about the project.

---

## Project Goal

Make the library complete — able to convert any ONNX model to Keras without failure.

**Two tracks of work:**
1. **Missing ops** — ONNX ops not yet in `AVAILABLE_CONVERTERS`. Fix = write a converter + register it.
2. **Incorrect converters** — Ops that exist but silently produce wrong output for certain inputs. Fix = run real-world ONNX models, compare numerically between ONNX Runtime and Keras, diagnose mismatches.

Start with missing ops (more systematic, finite list). Then move to incorrect conversions via fuzzing with models from ONNX Model Zoo / HuggingFace.

**Longer-term vision:** Multi-agent pipeline — agents create issues, implement fixes, run tests, code review, escalate to human when stuck.

---

## Fork Chain

```
gmalivenko/onnx2keras       ← original open-source library
    └── tensorleap/onnx2keras   ← direct upstream (all the real work)
            └── shaninja/onnx2keras  ← this fork
```

- **upstream** remote = `tensorleap/onnx2keras`
- **origin** remote = `shaninja/onnx2keras`

---

## Codebase Layout

```
onnx2kerastl/
  layers.py               ← AVAILABLE_CONVERTERS dict + all imports
  operation_layers.py     ← math/cast/reduce/bitwise/logical ops
  activation_layers.py    ← relu, elu, selu, gelu, mish, etc.
  convolution_layers.py   ← Conv, ConvTranspose
  elementwise_layers.py   ← add, sub, mul, div, where, scatter, etc.
  reshape_layers.py       ← transpose, reshape, gather, slice, tile, etc.
  normalization_layers.py ← batchnorm, layernorm, instancenorm, dropout, lrn
  pooling_layers.py       ← maxpool, avgpool, topk, roi_align
  linear_layers.py        ← gemm, det
  constant_layers.py      ← constant, constant_of_shape, one_hot
  padding_layers.py       ← pad
  upsampling_layers.py    ← upsample
  ltsm_layers.py          ← lstm, gru
  fft_layers.py           ← dft
  sampling_layers.py      ← gridsample, range, unique, random_uniform_like
  caffe2_layers.py        ← alias_with_name, resize_nearest

test/
  layers/
    operations/           ← unit tests for operation_layers.py converters
    activations/          ← unit tests for activation converters
    ...
  models/
    private_tests/        ← requires AWS credentials (skip in local runs)
```

---

## How Converters Work

Every converter has this signature:

```python
def convert_foo(node, params, layers, lambda_func, node_name, keras_name):
    ...
    layers[node_name] = <result tensor or numpy array>
```

- `node.input[i]` — name of the i-th input node
- `layers[name]` — resolved value (numpy array or Keras/TF tensor) for that name
- `is_numpy(x)` — True if x is a numpy array (constant); False if it's a live tensor
- `ensure_tf_type(x, name=...)` — wraps a numpy constant into a TF constant tensor
- `tf_cast(x, dtype, tf_name=...)` — casts tensor x to dtype, with a unique op name

**Adding a new op:**
1. Write `convert_foo` in the appropriate `*_layers.py` file
2. Import it in `layers.py`
3. Add `'FooOp': convert_foo` to `AVAILABLE_CONVERTERS` in `layers.py`
4. Write a test in `test/layers/<category>/test_foo.py`

**Reference:** https://onnx.ai/onnx/operators/ — official ONNX operator spec (opset ~21, ~180-200 ops total; library covers ~130)

---

## Known Gotchas

### Same-dtype cast creates a broken `placeholder:0` tensor
When casting a tensor to its own existing dtype (no-op cast), Keras creates a `placeholder:0` tensor that breaks the engine. Workaround: up-cast to `float64` first, then cast to target dtype. Example from `convert_cast`:

```python
if input_0.dtype == dtype and not isinstance(input_0, (tf.Tensor, np.ndarray)):
    if input_0.dtype != tf.double:
        input_0 = tf_cast(input_0, tf.double, tf_name=f"{params['cleaned_name']}_precast")
    else:
        raise NotImplementedError("Cast does not support tf.double casting into itself")
```

Apply the same pattern in any new cast-like converter.

### Dynamic input dtype defaults to float32
When calling `onnx_to_keras(model, input_names)` without `input_types`, integer-typed inputs get treated as float32. In tests: if a node input needs a non-float type, make it an ONNX **initializer** (constant), not a graph input. See `test_cast_like.py` for an example.

### Integer inputs in tests
When building ONNX test models with `onnx.helper`, use `numpy_helper.from_array(np_array, name="...")` to create initializers for constant tensors that must have a specific dtype.

---

## Git Workflow

### Branch naming
- `add/op-name` — new ONNX op
- `fix/description` — bug fix in existing converter

### Upstream sync (do this before starting every new branch)
```bash
git checkout master
git fetch upstream      # upstream = tensorleap/onnx2keras
git merge upstream/master
git push origin master
git checkout -b add/new-op
```

### PR / merge policy
- PRs target `shaninja/master` (NOT tensorleap) — always verify base repo before submitting
- When PRing within own fork: navigate to `github.com/shaninja/onnx2keras` directly — the GitHub banner after a push defaults to the upstream repo and will open a PR there by mistake
- **CI will always fail on the fork** — the CI workflow uses an AWS IAM role that belongs to tensorleap. Ignore the red CI mark. Run tests locally instead.

### When eventually contributing back to tensorleap
- Cherry-pick op commits only
- Exclude `.github/` infra changes

---

## Commit Message Rules

- Never mention Claude, AI, LLM, or how the code was generated
- Describe what the change does and why
- Keep it concise

---

## Project Memory Policy

- If the user asks to "remember", "save", or "keep" something that is specific to this repo, add it to this file.
- Prefer storing project workflow, review norms, testing conventions, fork/PR rules, and recurring gotchas here instead of only in tool-local memory.
- Keep additions short and operational. This file should help future agents act correctly, not serve as a full changelog.

---

## Code Review Workflow

When the user asks for a review, default to a multi-agent review and then consolidate the results into one final review.

### Review output style

- Findings first, ordered by severity
- Then open questions / assumptions if needed
- Then a short verdict
- If there are no findings, say so explicitly

### Standing review personas

Launch these reviewers in parallel:

1. **Correctness reviewer**
   - Focus: semantic correctness, parity with similar converters, realistic edge cases, test adequacy, regressions
   - Constraints:
     - Do not ask for redesigns unless required for correctness
     - Treat pre-existing limitations as out of scope unless the patch makes them worse

2. **Maintainability reviewer**
   - Focus: consistency with local converter/test patterns, future extension cost, duplication drift risk, naming/comments, repo fit
   - Constraints:
     - Prefer local consistency over idealized design
     - Do not push broad refactors unless the patch creates real maintenance risk

3. **Scope-and-regression reviewer**
   - Focus: whether the patch is narrowly scoped, avoids unintended behavior changes, and does not introduce unnecessary coupling
   - Constraints:
     - Be strict about scope creep
     - Do not ask for unrelated improvements

4. **Edge-cases reviewer**
   - Focus: boundary conditions, dtype/shape/empty/singleton cases, constant-vs-dynamic behavior, happy-path-only tests
   - Constraints:
     - Focus on realistic edge cases for this repo and the specific patch
     - Do not ask for speculative hardening unless there is concrete risk

### Review principles for this repo

- Minimize changes to existing code
- Assume existing code and tests are valid unless the new patch directly conflicts with them
- Prefer extending the library in the same style rather than refactoring toward a cleaner architecture
- Treat dynamic dtype/input limitations and similar known repo-wide constraints as out of scope unless the patch worsens them

---

## Op Coverage

See `support_map.md` for the full picture:
- First table: all ops with their current support status (✓ / E / -)
- Second table: official ONNX ops not yet supported at all

**Every agent that adds support for a new op must update `support_map.md` as part of the same change:**
- Move the op from the second table to the first table (or add it if absent from both)
- Mark it ✓ in the first table
- This is not optional — a PR that adds an op without updating `support_map.md` is incomplete
