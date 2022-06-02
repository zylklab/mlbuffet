from xml.dom import NotSupportedErr
import onnxruntime as rt
import numpy

# List with preloaded models to do the inference
model_sessions = {}


def check_model_exists(tag):
    # Check that the model exists
    if tag not in model_sessions.keys():
        return False
    else:
        return True


def perform_inference(tag, model_input):

    inference_session = model_sessions[tag]['inference_session']
    input_name = model_sessions[tag]['input_name']
    output_name = model_sessions[tag]['output_name']

    model_dimensions = model_sessions[tag]['dimensions'][1:]
    image_dimensions = list(numpy.shape(model_input))

    if model_dimensions == image_dimensions:
        try:
            prediction = inference_session.run(
                [output_name],
                {input_name: [model_input]}
            )[0]
            return prediction

            # Error provided by the model
        except Exception as error:
            return error

    elif model_dimensions != image_dimensions:
        npimage = numpy.asarray(model_input)
        model_input = numpy.rollaxis(npimage, 2, 0).tolist()
        image2_dimensions = list(numpy.shape(model_input))

        if image2_dimensions == model_dimensions:
            try:
                prediction = inference_session.run(
                    [output_name],
                    {input_name: [model_input]}
                )[0]
            except Exception as error:
                # Error provided by the model
                raise Exception(error)

            # Correct prediction
            return prediction
        else:
            error = '{tag} does not support this input. {image_dimensions} is '
            f'received, but {model_dimensions} is allowed. Please, check it and try '
            f'again. '

            raise NotImplementedError(error)


def load_new_model(tag, filename):

    try:
        # Totally uncommented
        # Take the model parameters
        model = open(filename, 'rb')

        inference_session = rt.InferenceSession(model.stream.read())
        dimensions = inference_session.get_inputs()[0].shape
        input_name = inference_session.get_inputs()[0].name
        output_name = inference_session.get_outputs()[0].name
        label_name = inference_session.get_outputs()[0].name

        full_description = {'tag': tag,
                            'model_name': filename,
                            'inference_session': inference_session,
                            'dimensions': dimensions,
                            'input_name': input_name,
                            'output_name': output_name,
                            'label_name': label_name}
        model_sessions[tag] = full_description

        return model_sessions[tag]

    except Exception as e:
        return e
