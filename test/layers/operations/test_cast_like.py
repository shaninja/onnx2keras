import numpy as np
import pytest
import tensorflow as tf
from onnx import helper, TensorProto, numpy_helper
import onnxruntime as rt

from onnx2kerastl import onnx_to_keras

ONNX_STRING = TensorProto.STRING

ONNX_TO_NP = {
    TensorProto.FLOAT:  np.float32,
    TensorProto.DOUBLE: np.float64,
    TensorProto.INT32:  np.int32,
    TensorProto.INT64:  np.int64,
}

ONNX_TO_TF = {
    TensorProto.FLOAT:  tf.float32,
    TensorProto.DOUBLE: tf.float64,
    TensorProto.INT32:  tf.int32,
    TensorProto.INT64:  tf.int64,
}


def make_cast_like_model(input_type, target_type, target_np):
    """
    Build a minimal ONNX graph: output = CastLike(input, target)
    target is an initializer (constant), which is the typical real-world usage —
    the target tensor exists to carry a dtype, not dynamic data.
    """
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node(
        "CastLike",
        inputs=["input", "target"],
        outputs=["output"],
    )
    graph = helper.make_graph(
        nodes=[node],
        name="test-cast-like",
        inputs=[
            helper.make_tensor_value_info("input", input_type, [2, 4]),
        ],
        outputs=[
            helper.make_tensor_value_info("output", target_type, [2, 4]),
        ],
        initializer=[target_init],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])
    return model


@pytest.mark.parametrize("input_type,target_type", [
    (TensorProto.DOUBLE, TensorProto.FLOAT),   # float64 → float32
    (TensorProto.INT32,  TensorProto.FLOAT),   # int32   → float32
    (TensorProto.INT64,  TensorProto.FLOAT),   # int64   → float32
    (TensorProto.FLOAT,  TensorProto.FLOAT),   # float32 → float32 (same dtype)
    (TensorProto.INT64,  TensorProto.INT64),   # int64   → int64   (same dtype, previously corrupted by float64 upcast)
    (TensorProto.DOUBLE, TensorProto.DOUBLE),  # float64 → float64 (same dtype, previously raised)
])
def test_cast_like(input_type, target_type):
    input_dtype  = ONNX_TO_NP[input_type]
    target_dtype = ONNX_TO_NP[target_type]

    target_np = np.array([0], dtype=target_dtype)
    onnx_model = make_cast_like_model(input_type, target_type, target_np)

    input_np = np.random.uniform(0, 10, (2, 4)).astype(input_dtype)

    # Reference output from onnxruntime
    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": input_np})[0]

    # Converted Keras model output — pass input_types so non-float inputs keep their dtype
    keras_model = onnx_to_keras(onnx_model, ["input"], input_types=[ONNX_TO_TF[input_type]]).converted_model
    keras_output = np.array(keras_model(input_np))

    # Values must match
    assert np.allclose(ort_output, keras_output, atol=1e-5), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"

    # Output dtype must match the target dtype, not the input dtype
    assert keras_output.dtype == target_dtype, \
        f"Dtype mismatch: expected {target_dtype}, got {keras_output.dtype}"


def test_cast_like_dynamic_target():
    """
    Exercise the dynamic-target code path: target is a graph input (live tensor),
    not an initializer, so the converter must call ensure_tf_type(target, ...) and
    read the dtype from the resulting TF tensor rather than from a numpy array.
    """
    # Graph: float32 input + float64 target (both dynamic) → CastLike → float64 output
    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-cast-like-dynamic-target",
        inputs=[
            helper.make_tensor_value_info("input",  TensorProto.FLOAT,  [2, 3]),
            helper.make_tensor_value_info("target", TensorProto.DOUBLE, [1]),
        ],
        outputs=[helper.make_tensor_value_info("output", TensorProto.DOUBLE, [2, 3])],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    input_np  = np.random.uniform(0, 10, (2, 3)).astype(np.float32)
    target_np = np.array([0.0], dtype=np.float64)

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": input_np, "target": target_np})[0]

    keras_model = onnx_to_keras(
        onnx_model, ["input", "target"],
        input_types=[tf.float32, tf.float64],
    ).converted_model
    keras_output = np.array(keras_model([input_np, target_np]))

    assert np.allclose(ort_output, keras_output, atol=1e-5), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"
    assert keras_output.dtype == np.float64, \
        f"Dtype mismatch: expected float64, got {keras_output.dtype}"


def test_cast_like_string_to_numeric():
    """String numpy initializer cast to float32 — exercises the numpy string→numeric path."""
    str_vals = np.array(['1.0', '2.5', '3.0', '4.5',
                         '5.0', '6.5', '7.0', '8.5'], dtype=object).reshape(2, 4)
    target_np = np.array([0.0], dtype=np.float32)

    input_init  = numpy_helper.from_array(str_vals, name="input")
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-str-to-num",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 4])],
        outputs=[helper.make_tensor_value_info("output", TensorProto.FLOAT, [2, 4])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = np.array(keras_model(str_vals))

    assert np.allclose(ort_output, keras_output, atol=1e-5), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"
    assert keras_output.dtype == np.float32, \
        f"Dtype mismatch: expected float32, got {keras_output.dtype}"


def test_cast_like_numeric_to_string():
    """Float32 dynamic input cast to string — exercises the tensor numeric→string path."""
    target_np = np.array([b''], dtype=object)
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-num-to-str",
        inputs=[helper.make_tensor_value_info("input", TensorProto.FLOAT, [2, 3])],
        outputs=[helper.make_tensor_value_info("output", ONNX_STRING, [2, 3])],
        initializer=[target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    input_np = np.array([[1.0, 2.5, 3.0], [4.0, 5.5, 6.0]], dtype=np.float32)

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": input_np})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.float32]).converted_model
    keras_output = keras_model(input_np).numpy()

    assert ort_output.shape == keras_output.shape, \
        f"Shape mismatch: ort={ort_output.shape}, keras={keras_output.shape}"
    # The ONNX spec does not mandate an exact string format for float→string casts
    # (e.g. ORT produces '1' while TF produces '1.000000').  Verify round-trip numeric
    # equality: both strings must parse back to the same float value.
    for orig, ort_val, keras_val in zip(input_np.flat, ort_output.flat, keras_output.flat):
        ort_f = float(ort_val.decode() if isinstance(ort_val, bytes) else ort_val)
        keras_f = float(keras_val.decode() if isinstance(keras_val, bytes) else keras_val)
        assert np.isclose(ort_f, keras_f, atol=1e-5), \
            f"Numeric mismatch after string parse: orig={orig}, ort={ort_f}, keras={keras_f}"


# tf.strings.to_number only supports {float32, float64, int32, int64} natively;
# all other numeric target types require an intermediate cast.  Test the most
# representative ones: int8 (via int32), uint8 (via int32), uint32 (via int64).
@pytest.mark.parametrize("target_type,target_np_dtype,onnx_target_type", [
    (TensorProto.INT8,   np.int8,   TensorProto.INT8),
    (TensorProto.UINT8,  np.uint8,  TensorProto.UINT8),
    (TensorProto.UINT32, np.uint32, TensorProto.UINT32),
])
def test_cast_like_string_to_narrow_int(target_type, target_np_dtype, onnx_target_type):
    """String→narrow-int tensor path exercises _string_to_number_tensor intermediate cast."""
    str_vals = np.array([['1', '2'], ['3', '4']], dtype=object)
    target_np = np.array([0], dtype=target_np_dtype)

    input_init  = numpy_helper.from_array(str_vals, name="input")
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-str-narrow",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 2])],
        outputs=[helper.make_tensor_value_info("output", target_type, [2, 2])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = np.array(keras_model(str_vals))

    assert keras_output.dtype == target_np_dtype, \
        f"Dtype mismatch: expected {target_np_dtype}, got {keras_output.dtype}"
    assert np.array_equal(ort_output, keras_output), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"


def test_cast_like_string_decimal_to_int():
    """ORT accepts decimal strings for integer casts and truncates toward zero.
    Exercises the float64-intermediate path in _string_to_number_tensor."""
    str_vals = np.array([['100.5', '2.718'], ['-1.9', '42']], dtype=object)
    target_np = np.array([0], dtype=np.int32)

    input_init  = numpy_helper.from_array(str_vals, name="input")
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-str-decimal-to-int",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 2])],
        outputs=[helper.make_tensor_value_info("output", TensorProto.INT32, [2, 2])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = np.array(keras_model(str_vals))

    assert keras_output.dtype == np.int32
    assert np.array_equal(ort_output, keras_output), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"


def test_cast_like_string_to_bool():
    """String→bool: must match ORT's int-truncation semantics (e.g. '0.5' → False)."""
    str_vals = np.array([['0', '1'], ['0.5', '2']], dtype=object)
    target_np = np.array([False], dtype=np.bool_)

    input_init  = numpy_helper.from_array(str_vals, name="input")
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-str-to-bool",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 2])],
        outputs=[helper.make_tensor_value_info("output", TensorProto.BOOL, [2, 2])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = np.array(keras_model(str_vals))

    assert keras_output.dtype == np.bool_
    assert np.array_equal(ort_output, keras_output), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"


@pytest.mark.parametrize("target_type", [
    TensorProto.FLOAT16,
    TensorProto.BFLOAT16,
    TensorProto.UINT64,
])
def test_cast_like_string_to_extra_numeric(target_type):
    """Exercises the remaining opset-15 numeric targets: float16, bfloat16, uint64.
    ORT cannot return bfloat16/uint64 cleanly as numpy, so the graph casts the
    CastLike output to float32 before returning; that is enough to validate the
    CastLike branch itself."""
    str_vals = np.array([['1.5', '2.5'], ['10', '100']], dtype=object)

    if target_type == TensorProto.BFLOAT16:
        target_init = helper.make_tensor("target", TensorProto.BFLOAT16, [1], [0])
    elif target_type == TensorProto.FLOAT16:
        target_init = numpy_helper.from_array(np.array([0], dtype=np.float16), name="target")
    else:  # UINT64
        target_init = numpy_helper.from_array(np.array([0], dtype=np.uint64), name="target")

    input_init = numpy_helper.from_array(str_vals, name="input")

    cast_like = helper.make_node("CastLike", inputs=["input", "target"], outputs=["cast_out"])
    # Cast back to float32 so ORT can return the value to Python
    tail = helper.make_node("Cast", inputs=["cast_out"], outputs=["output"],
                            to=TensorProto.FLOAT)

    graph = helper.make_graph(
        [cast_like, tail], "test-castlike-str-extra",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 2])],
        outputs=[helper.make_tensor_value_info("output", TensorProto.FLOAT, [2, 2])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = np.array(keras_model(str_vals))

    # float16/bfloat16 lose precision (atol 0.1 covers bfloat16's ~1% error);
    # uint64 has full integer precision so the same tolerance is safe.
    atol = 0.1 if target_type == TensorProto.BFLOAT16 else 1e-3
    assert np.allclose(ort_output, keras_output, atol=atol), \
        f"Value mismatch ({target_type}): ort={ort_output}, keras={keras_output}"


@pytest.mark.parametrize("target_type,np_dtype,values", [
    (TensorProto.UINT64, np.uint64, [
        # 2^53 + 1 — float64 would round to 2^53, losing the +1
        '9007199254740993',
        # 2^60 + 1 — another float64-imprecise value
        '1152921504606846977',
        # max uint64 — outside int64 range entirely
        '18446744073709551615',
        '0',
    ]),
    (TensorProto.INT64, np.int64, [
        '9007199254740993',       # 2^53 + 1
        '-9007199254740993',      # negative above-2^53
        '4611686018427387903',    # 2^62 - 1
        '9223372036854775807',    # max int64
    ]),
])
def test_cast_like_string_to_wide_int_precision(target_type, np_dtype, values):
    """Pins the full legal integer range: values above 2^53 must parse exactly,
    which float64 parsing cannot do.  Exercises the tf.numpy_function
    Python-int path for int64 and uint64."""
    str_vals = np.array(values, dtype=object).reshape(2, 2)
    target_np = np.array([0], dtype=np_dtype)
    expected = np.array([int(v) for v in values], dtype=np_dtype).reshape(2, 2)

    input_init  = numpy_helper.from_array(str_vals, name="input")
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-wide-int",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 2])],
        outputs=[helper.make_tensor_value_info("output", target_type, [2, 2])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]
    assert np.array_equal(ort_output, expected), \
        f"ORT disagrees with expected: ort={ort_output}, expected={expected}"

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = np.array(keras_model(str_vals))

    assert keras_output.dtype == np_dtype, \
        f"Dtype mismatch: expected {np_dtype}, got {keras_output.dtype}"
    assert np.array_equal(keras_output, expected), \
        f"Value mismatch: keras={keras_output}, expected={expected}"


def test_cast_like_live_string_target():
    """Target is a live tf.string graph input — exercises the non-numpy target path
    when the inferred dtype is tf.string."""
    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-live-str-target",
        inputs=[
            helper.make_tensor_value_info("input",  TensorProto.FLOAT, [2, 3]),
            helper.make_tensor_value_info("target", ONNX_STRING,       [1]),
        ],
        outputs=[helper.make_tensor_value_info("output", ONNX_STRING, [2, 3])],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    input_np  = np.array([[1.0, 2.5, 3.0], [4.0, 5.5, 6.0]], dtype=np.float32)
    target_np = np.array([b''], dtype=object)

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": input_np, "target": target_np})[0]

    keras_model = onnx_to_keras(
        onnx_model, ["input", "target"],
        input_types=[tf.float32, tf.string],
    ).converted_model
    keras_output = keras_model([input_np, target_np]).numpy()

    assert ort_output.shape == keras_output.shape
    for ort_val, keras_val in zip(ort_output.flat, keras_output.flat):
        ort_f   = float(ort_val.decode()   if isinstance(ort_val, bytes)   else ort_val)
        keras_f = float(keras_val.decode() if isinstance(keras_val, bytes) else keras_val)
        assert np.isclose(ort_f, keras_f, atol=1e-5), \
            f"Value mismatch: ort={ort_f}, keras={keras_f}"


def test_cast_like_string_to_string():
    """String tensor cast to string (same-dtype no-op) — exercises tf.identity path."""
    str_vals = np.array([['hello', 'world'], ['foo', 'bar']], dtype=object)
    target_np = np.array([b''], dtype=object)

    input_init  = numpy_helper.from_array(str_vals, name="input")
    target_init = numpy_helper.from_array(target_np, name="target")

    node = helper.make_node("CastLike", inputs=["input", "target"], outputs=["output"])
    graph = helper.make_graph(
        [node], "test-castlike-str-to-str",
        inputs=[helper.make_tensor_value_info("input", ONNX_STRING, [2, 2])],
        outputs=[helper.make_tensor_value_info("output", ONNX_STRING, [2, 2])],
        initializer=[input_init, target_init],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 15)])

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_output = sess.run(["output"], {"input": str_vals})[0]

    keras_model = onnx_to_keras(onnx_model, ["input"],
                                input_types=[tf.string]).converted_model
    keras_output = keras_model(str_vals).numpy()

    for ort_val, keras_val in zip(ort_output.flat, keras_output.flat):
        ort_s   = ort_val.decode()   if isinstance(ort_val, bytes)   else str(ort_val)
        keras_s = keras_val.decode() if isinstance(keras_val, bytes) else str(keras_val)
        assert ort_s == keras_s, f"String mismatch: ort={ort_s!r}, keras={keras_s!r}"
