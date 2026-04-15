Legend:
- :heavy_check_mark: supported
- \- not supported yet
- E not supported but easy to support

| Op name | supported |
|---------|-----------|
|Abs|                          :heavy_check_mark:|
|Acos|                         :heavy_check_mark:|
|Acosh|                        :heavy_check_mark:|
|Add|                          :heavy_check_mark:|
|AffineGrid|                   -|
|And|                          :heavy_check_mark:|
|ArgMax|                       :heavy_check_mark:|
|ArgMin|                       :heavy_check_mark:|
|Asin|                         :heavy_check_mark:|
|Asinh|                        :heavy_check_mark:|
|Atan|                         :heavy_check_mark:|
|Atanh|                        :heavy_check_mark:|
|AveragePool|                  :heavy_check_mark:|
|BatchNormalization|           :heavy_check_mark:|
|Bernoulli|                    -|
|BitShift|                     :heavy_check_mark:|
|BitwiseAnd|                   :heavy_check_mark:|
|BitwiseNot|                   :heavy_check_mark:|
|BitwiseOr|                    :heavy_check_mark:|
|BitwiseXor|                   :heavy_check_mark:|
|BlackmanWindow|               -|
|Cast|                         :heavy_check_mark:|
|CastLike|                     -|
|Ceil|                         :heavy_check_mark:|
|Celu|                         E|
|CenterCropPad|                E|
|Clip|                         :heavy_check_mark:|
|Col2Im|                       :heavy_check_mark:|
|Concat|                       :heavy_check_mark:|
|Constant|                     :heavy_check_mark:|
|ConstantOfShape|              :heavy_check_mark:|
|Conv|                         :heavy_check_mark:|
|ConvTranspose|                :heavy_check_mark:|
|Cos|                          :heavy_check_mark:|
|Cosh|                         :heavy_check_mark:|
|CumSum|                       :heavy_check_mark:|
|DFT|                          :heavy_check_mark:|
|Det|                          :heavy_check_mark:|
|Div|                          :heavy_check_mark:|
|Dropout|                      :heavy_check_mark:|
|DynamicQuantizeLinear|        -|
|Einsum|                       :heavy_check_mark:|
|Elu|                          :heavy_check_mark:|
|Equal|                        :heavy_check_mark:|
|Erf|                          :heavy_check_mark:|
|Exp|                          :heavy_check_mark:|
|Expand|                       :heavy_check_mark:|
|Flatten|                      :heavy_check_mark:|
|Floor|                        :heavy_check_mark:|
|GRU|                          :heavy_check_mark:|
|Gather|                       :heavy_check_mark:|
|GatherElements|               :heavy_check_mark:|
|GatherND|                     :heavy_check_mark:|
|Gelu|                         :heavy_check_mark:|
|Gemm|                         :heavy_check_mark:|
|GlobalAveragePool|            :heavy_check_mark:|
|GlobalMaxPool|                :heavy_check_mark:|
|Greater|                      :heavy_check_mark:|
|GreaterOrEqual|               :heavy_check_mark:|
|GridSample|                   :heavy_check_mark:|
|GroupNormalization|           E|
|HammingWindow|                -|
|HannWindow|                   -|
|HardSigmoid|                  :heavy_check_mark:|
|HardSwish|                    :heavy_check_mark:|
|Identity|                     :heavy_check_mark:|
|If|                           :heavy_check_mark:|
|InstanceNormalization|        :heavy_check_mark:|
|IsInf|                        :heavy_check_mark:|
|IsNaN|                        :heavy_check_mark:|
|LRN|                          :heavy_check_mark:|
|LSTM|                         :heavy_check_mark:|
|LayerNormalization|           :heavy_check_mark:|
|LeakyRelu|                    :heavy_check_mark:|
|Less|                         :heavy_check_mark:|
|LessOrEqual|                  :heavy_check_mark:|
|Log|                          :heavy_check_mark:|
|LogSoftmax|                   E|
|MatMul|                       :heavy_check_mark:|
|Max|                          :heavy_check_mark:|
|MaxPool|                      :heavy_check_mark:|
|Mean|                         :heavy_check_mark:|
|MeanVarianceNormalization|    -|
|Min|                          :heavy_check_mark:|
|Mish|                         :heavy_check_mark:|
|Mod|                          :heavy_check_mark:|
|Mul|                          :heavy_check_mark:|
|Neg|                          :heavy_check_mark:|
|NegativeLogLikelihoodLoss|    -|
|NonMaxSuppression|            :heavy_check_mark:|
|NonZero|                      :heavy_check_mark:|
|Not|                          :heavy_check_mark:|
|OneHot|                       :heavy_check_mark:|
|Or|                           :heavy_check_mark:|
|PRelu|                        :heavy_check_mark:|
|Pad|                          :heavy_check_mark:|
|Pow|                          :heavy_check_mark:|
|RandomUniformLike|            :heavy_check_mark:|
|Range|                        :heavy_check_mark:|
|Reciprocal|                   :heavy_check_mark:|
|ReduceL1|                     E|
|ReduceL2|                     :heavy_check_mark:|
|ReduceLogSum|                 E|
|ReduceLogSumExp|              E|
|ReduceMax|                    :heavy_check_mark:|
|ReduceMean|                   :heavy_check_mark:|
|ReduceMin|                    :heavy_check_mark:|
|ReduceProd|                   :heavy_check_mark:|
|ReduceSum|                    :heavy_check_mark:|
|ReduceSumSquare|              E|
|Relu|                         :heavy_check_mark:|
|Reshape|                      :heavy_check_mark:|
|Resize|                       :heavy_check_mark:|
|RoiAlign|                     :heavy_check_mark:|
|Round|                        :heavy_check_mark:|
|ScatterND|                    :heavy_check_mark:|
|Selu|                         :heavy_check_mark:|
|SequenceMap|                  -|
|Shape|                        :heavy_check_mark:|
|Shrink|                       -|
|Sigmoid|                      :heavy_check_mark:|
|Sign|                         :heavy_check_mark:|
|Sin|                          :heavy_check_mark:|
|Sinh|                         :heavy_check_mark:|
|Size|                         :heavy_check_mark:|
|Slice|                        :heavy_check_mark:|
|Softmax|                      :heavy_check_mark:|
|SoftmaxCrossEntropyLoss|      E|
|Softplus|                     :heavy_check_mark:|
|Softsign|                     :heavy_check_mark:|
|Split|                        :heavy_check_mark:|
|Sqrt|                         :heavy_check_mark:|
|Squeeze|                      :heavy_check_mark:|
|Sub|                          :heavy_check_mark:|
|Sum|                          :heavy_check_mark:|
|Tan|                          :heavy_check_mark:|
|Tanh|                         :heavy_check_mark:|
|ThresholdedRelu|              E|
|Tile|                         :heavy_check_mark:|
|TopK|                         :heavy_check_mark:|
|Transpose|                    :heavy_check_mark:|
|Trilu|                        :heavy_check_mark:|
|Unique|                       :heavy_check_mark:|
|Unsqueeze|                    :heavy_check_mark:|
|Upsample|                     :heavy_check_mark:|
|Where|                        :heavy_check_mark:|
|Xor|                          :heavy_check_mark:|

---

## Official ONNX Operators Not Yet Supported

These are standard ONNX operators confirmed absent from `AVAILABLE_CONVERTERS` and are not listed above.
https://onnx.ai/onnx/operators/

| Op name |
|---------|
|Attention|
|BitCast|
|Compress|
|ConcatFromSequence|
|ConvInteger|
|CumProd|
|DeformConv|
|DepthToSpace|
|DequantizeLinear|
|EyeLike|
|GlobalLpPool|
|Hardmax|
|ImageDecoder|
|Loop|
|LpNormalization|
|LpPool|
|MatMulInteger|
|MaxRoiPool|
|MaxUnpool|
|MelWeightMatrix|
|Multinomial|
|Optional|
|OptionalGetElement|
|OptionalHasElement|
|QLinearConv|
|QLinearMatMul|
|QuantizeLinear|
|RMSNormalization|
|RNN|
|RandomNormal|
|RandomNormalLike|
|RandomUniform|
|RegexFullMatch|
|ReverseSequence|
|RotaryEmbedding|
|STFT|
|Scan|
|ScatterElements|
|SequenceAt|
|SequenceConstruct|
|SequenceEmpty|
|SequenceErase|
|SequenceInsert|
|SequenceLength|
|SpaceToDepth|
|SplitToSequence|
|StringConcat|
|StringNormalizer|
|StringSplit|
|Swish|
|TensorScatter|
|TfIdfVectorizer|
