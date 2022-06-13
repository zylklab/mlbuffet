import tensorflow
import shutil
import os
import numpy
# List with preloaded models to do the inference
model_sessions = {}


def _pb_load(tag, filename, model_name): # tf model loading when .pb format is detected
    """
    Auxiliary method for loading TF model when .pb format is detected
    """
    tfmodel = tensorflow.saved_model.load(filename)
    inferlayer = tfmodel.signatures[
        "serving_default"]  # layer where inference happens passing the inputs as a tf.constant(inputs)
    input_name = list(inferlayer.structured_input_signature[1].keys())[0]
    output_name = list(inferlayer.structured_outputs.keys())[0]
    dimensions = inferlayer.structured_input_signature[1][input_name].shape.as_list()
    label_name = list(inferlayer.structured_outputs.keys())[0]

    full_description = {'tag': tag,
                        'model_type': 'pb', # check for inference tasks
                        'model_name': model_name,
                        'infer_layer': inferlayer,
                        'input_name': input_name,
                        'output_name': output_name,
                        'dimensions': dimensions,
                        'label_name': label_name}

    return full_description


def _keras_load(tag, filename):
    """
        Auxiliary method for loading TF model when .pb format is detected
    """
    model = tensorflow.keras.models.load_model(filename)
    input_name = model.input_names
    output_name = model.output_names
    dimensions = model.input.shape.as_list()
    label_name = model.output_names

    full_description = {'tag': tag,
                        'model_type': 'h5', # check for inference tasks
                        'model_object': model,
                        'model_name': filename,
                        'input_name': input_name,
                        'output_name': output_name,
                        'dimensions': dimensions,
                        'label_name': label_name}

    return full_description


def load_model(tag, filename):
    """
    Method for loading a model
    :param tag: a tag to identify the model
    :param filename: the stored model file. Either a .zip with the folder, a .pb or a.h5 file
    """
    if '.zip' in filename:  # check if zip -> unpack in a folder named with the tag
        shutil.unpack_archive(filename, os.getcwd())

    files = os.listdir(os.getcwd())
    if any(File.endswith(".pb") for File in files):
        mfile = [f for f in os.listdir(os.getcwd()) if f.endswith('.pb')][0]
        try:
            # when loading a pb model, using os.getcwd as the directory param required by the load function
            model_sessions[tag] = _pb_load(tag, os.getcwd(), mfile)
            return model_sessions[tag]
        except Exception as e:
            print(e)
            return e
    else:  # .h5 model loaded -> keras library
        mfile = [f for f in os.listdir(os.getcwd()) if f.endswith('.h5')][0]
        try:
            model_sessions[tag] = _keras_load(tag, mfile)
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
    """
    Method to perform inference on a loaded model.
    :param tag: Model identifier
    :param model_input: Input to be given to the model to perform the inference
    """
    if model_sessions[tag]['model_type'] == 'h5':
        model_input = numpy.expand_dims(numpy.asarray(model_input), axis=0)
        return model_sessions[tag]['model_object'].predict(model_input)

    else:
        infer = model_sessions[tag]['infer_layer']
        output_name = model_sessions[tag]['output_name']

        return infer(tensorflow.constant(numpy.array(model_input)))[output_name].numpy()
