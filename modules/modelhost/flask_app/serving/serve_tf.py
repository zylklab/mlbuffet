import tensorflow
import numpy
from modules.modelhost.flask_app.utils import utils
import os

# List with preloaded models to do the inference
model_sessions = {}


def pb_load(tag, filename, model_name):  # tf model loading when .pb format is detected
    tfmodel = tensorflow.saved_model.load(filename)
    inferlayer = tfmodel.signatures[
        "serving_default"]  # layer where inference happens passing the inputs as a tf.constant(inputs)
    input_name = list(inferlayer.structured_input_signature[1].keys())[0]
    output_name = list(inferlayer.structured_outputs.keys())[0]
    dimensions = inferlayer.structured_input_signature[1][input_name].shape.as_list()
    label_name = list(inferlayer.structured_outputs.keys())[0]

    full_description = {'tag': tag,
                        'model_type': 'pb',  # check for inference tasks
                        'model_name': model_name,
                        'infer_layer': inferlayer,
                        'input_name': input_name,
                        'output_name': output_name,
                        'dimensions': dimensions,
                        'label_name': label_name}

    return full_description


def keras_load(tag, filename):
    model = tensorflow.keras.models.load_model(filename)
    input_name = model.input_names
    output_name = model.output_names
    dimensions = model.input.shape.as_list()
    label_name = model.output_names

    full_description = {'tag': tag,
                        'model_type': 'h5',  # check for inference tasks
                        'model_object': model,
                        'model_name': filename,
                        'input_name': input_name,
                        'output_name': output_name,
                        'dimensions': dimensions,
                        'label_name': label_name}

    return full_description


def load_model(tag, filename):

    if '.zip' in filename:  # check if zip
        utils.unzip_models(filename)

    files = os.listdir(os.getcwd())
    if any(File.endswith(".pb") for File in files):
        mfile = [f for f in os.listdir(os.getcwd()) if f.endswith('.pb')][0]
        try:
            # when loading a pb model, using os.getcwd as the directory param required by the load function
            model_sessions[tag] = pb_load(tag, os.getcwd(), mfile)
            return model_sessions[tag]
        except Exception as e:
            print(e)
            return e
    else:  # .h5 model loaded -> keras library
        mfile = [f for f in os.listdir(os.getcwd()) if f.endswith('.h5')][0]
        try:
            model_sessions[tag] = keras_load(tag, mfile)
            return model_sessions[tag]
        except Exception as e:
            print(e)
            return e


def check_model_exists(tag):
    # Check that the model exists
    if tag not in model_sessions.keys():
        return False
    else:
        return True


def perform_inference(tag, model_input):

    if model_sessions[tag]['model_type'] == 'h5':
        return model_sessions[tag]['model_object'](model_input)

    else:
        infer = model_sessions[tag]['infer_layer']
        output_name = model_sessions[tag]['output_name']

        return infer(tensorflow.constant(numpy.array(model_input)))[output_name].numpy()

