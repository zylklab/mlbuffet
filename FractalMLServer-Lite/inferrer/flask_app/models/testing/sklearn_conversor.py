from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import joblib


def sk_conversor(modelFile, modelOutput, features):
    model = joblib.load(modelFile)
    initial_type = [('float_input', FloatTensorType([None, features]))]
    onx = convert_sklearn(model, initial_types=initial_type)
    potato = open(modelOutput, "wb").write(onx.SerializeToString())
    return potato
