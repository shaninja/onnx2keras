import torch.nn as nn
import numpy as np
import pytest
from onnx import helper, TensorProto
import onnxruntime as rt

from test.utils import convert_and_test
from onnx2kerastl import onnx_to_keras


class LayerSoftmax(nn.Module):
    """
    Test for nn.layers based types
    """
    def __init__(self, dim):
        super(LayerSoftmax, self).__init__()
        self.dim = dim
        self.softmax = nn.Softmax(dim=dim)

    def forward(self, x):
        x = self.softmax(x)
        return x


class FSoftmax(nn.Module):
    """
    Test for nn.functional types
    """
    def __init__(self, dim):
        super(FSoftmax, self).__init__()
        self.dim = dim

    def forward(self, x):
        from torch.nn import functional as F
        return F.softmax(x, self.dim)


@pytest.mark.parametrize('change_ordering', [False])
@pytest.mark.parametrize('dim', [0, 1, 2, 3])
def test_layer_softmax(change_ordering, dim):
    model = LayerSoftmax(dim)
    model.eval()
    input_np = np.random.uniform(0, 1, (1, 3, 224, 224))
    error = convert_and_test(model, input_np, verbose=False, change_ordering=change_ordering)


@pytest.mark.parametrize('change_ordering', [False])
@pytest.mark.parametrize('dim', [0, 1, 2, 3])
def test_f_softmax(change_ordering, dim):
    model = FSoftmax(dim)
    model.eval()
    input_np = np.random.uniform(0, 1, (1, 3, 224, 224))
    error = convert_and_test(model, input_np, verbose=False, change_ordering=change_ordering)


def test_softmax_high_rank():
    """Softmax on rank-6 input: keras.layers.Softmax is limited to rank<=5 and would crash."""
    shape = [1, 2, 3, 4, 5, 6]
    node = helper.make_node("Softmax", inputs=["x"], outputs=["y"], axis=-1)
    graph = helper.make_graph(
        [node], "test-softmax-6d",
        inputs=[helper.make_tensor_value_info("x", TensorProto.FLOAT, shape)],
        outputs=[helper.make_tensor_value_info("y", TensorProto.FLOAT, shape)],
    )
    onnx_model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])

    input_np = np.random.uniform(0, 1, shape).astype(np.float32)

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    ort_out = sess.run(["y"], {"x": input_np})[0]

    keras_model = onnx_to_keras(onnx_model, ["x"]).converted_model
    keras_out = np.array(keras_model(input_np))

    assert np.allclose(ort_out, keras_out, atol=1e-5)
