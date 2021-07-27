import onnxruntime as rt
import onnx
from os import path


def list_of_models(model_list, MODEL_FOLDER, session_list):
    for i in model_list:
        append_model(i, session_list, MODEL_FOLDER)


def append_model(model, session_list, MODEL_FOLDER):
    sess = rt.InferenceSession(path.join(MODEL_FOLDER, model))
    model = onnx.load(path.join(MODEL_FOLDER, model))
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    num_inputs = sess.get_inputs()[0].shape[1]
    outputs = sess.get_outputs()[0].type
    model_type = model.graph.node[0].name
    description = model.doc_string
    full_description = {"inputs_type": input_name, "num_imputs": num_inputs, "outputs": outputs,
                        "model_type": model_type,
                        "description": description}
    cosa = [model, sess, input_name, label_name, full_description]
    session_list.append(cosa)

