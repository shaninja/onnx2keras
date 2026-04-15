import numpy as np
import pytest
from onnx import helper, TensorProto, numpy_helper
import onnxruntime as rt

from onnx2kerastl import onnx_to_keras

ONNX_TO_NP = {
    TensorProto.FLOAT:  np.float32,
    TensorProto.DOUBLE: np.float64,
    TensorProto.INT32:  np.int32,
    TensorProto.INT64:  np.int64,
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
    (TensorProto.FLOAT,  TensorProto.FLOAT),   # float32 → float32 (same dtype, the tricky case)
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

    # Converted Keras model output
    keras_model = onnx_to_keras(onnx_model, ["input"]).converted_model
    keras_output = np.array(keras_model(input_np))

    # Values must match
    assert np.allclose(ort_output, keras_output, atol=1e-5), \
        f"Value mismatch: ort={ort_output}, keras={keras_output}"

    # Output dtype must match the target dtype, not the input dtype
    assert keras_output.dtype == target_dtype, \
        f"Dtype mismatch: expected {target_dtype}, got {keras_output.dtype}"
