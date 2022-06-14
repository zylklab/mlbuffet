import tensorflow
import numpy
from utils.utils import unzip_models

# List with preloaded models to do the inference
model_sessions = {}


def _pb_load(tag, filename):  # tf model loading when .pb format is detected
    """
    Auxiliary method for loading TF model when .pb format is detected
    """
    tfmodel = tensorflow.saved_model.load(filename)
    inferlayer = tfmodel.signatures[
        "serving_default"]  # layer where inference happens passing the inputs as a tf.constant(inputs)
    input_name = list(inferlayer.structured_input_signature[1].keys())[0]
    input_dtype = inferlayer.structured_input_signature[1][input_name].dtype
    output_name = list(inferlayer.structured_outputs.keys())[0]
    dimensions = inferlayer.structured_input_signature[1][input_name].shape.as_list()
    label_name = list(inferlayer.structured_outputs.keys())[0]

    # Handle model name
    if filename == '':
        # if model was not in a directory give a default name
        filename = 'saved_model.pb'
    else:
        # else give directory name to the model, handling trailing '/'s
        filename = filename[:-1] if filename.endswith('/') else filename
    full_description = {'tag': tag,
                        'model_type': 'pb',  # check for inference tasks
                        'model_name': filename,
                        'infer_layer': inferlayer,
                        'input_name': input_name,
                        'input_dtype': input_dtype,
                        'output_name': output_name,
                        'dimensions': dimensions,
                        'label_name': label_name}

    return full_description


def _keras_load(tag, filename):
    """
    Auxiliary method for loading TF model when .h5 format is detected
    """
    model = tensorflow.keras.models.load_model(filename)
    input_name = model.input_names
    output_name = model.output_names
    dimensions = model.input.shape.as_list()
    label_name = model.output_names

    full_description = {'tag': tag,
                        'model_type': 'h5',  # check for inference tasks
                        'model_object': model,
                        'model_name': filename.split('/')[-1],
                        'input_name': input_name,
                        'output_name': output_name,
                        'dimensions': dimensions,
                        'label_name': label_name}

    return full_description


def load_model(tag, filename):
    """
    Method for loading a model
    :param tag: a tag to identify the model
    :param filename: the stored model file. Either a .zip with the folder, a .pb or a .h5 file
    """

    filetype = filename.split('.')[-1]
    if filetype == 'zip':
        filelist = unzip_models(filename)
        for file in filelist:
            splits = file.split('/')
            if splits[-1] == 'saved_model.pb':
                filename = ''
                for split in splits[:-1]:
                    filename += split + '/'
                filetype = 'pb'
                break
            elif splits[-1].split('.')[-1] == 'h5':
                filename = file
                filetype = 'h5'
                break

    if filetype == 'pb':
        try:
            model_sessions[tag] = _pb_load(tag, filename)
            return model_sessions[tag]
        except Exception as e:
            print(e)
            return e
    # .h5 model loaded -> keras library
    elif filetype == 'h5':
        try:
            model_sessions[tag] = _keras_load(tag, filename)
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
        input_dtype = model_sessions[tag]['input_dtype']

        return infer(tensorflow.constant(model_input, dtype=input_dtype))[output_name].numpy()
