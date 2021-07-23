import joblib
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


def to_onnx(input_model, output_model, features):  # TODO: revisar posibles errores de  este método
    model = joblib.load(input_model)
    initial_type = [('float_input', FloatTensorType([None, features]))]
    onx = convert_sklearn(model, initial_types=initial_type)
    return open(output_model, "wb").write(onx.SerializeToString())
