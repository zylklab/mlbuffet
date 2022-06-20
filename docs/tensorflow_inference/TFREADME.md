# Documentation for the usage of Tensorflow models with MLBuffet

## Types of Tensorflow models.
Tensorflow supports creating models in two ways: with the Keras API, and without it. 

When saving models created with the Keras API, Tensorflow stores the `__call__` function of the model as a `tf.function`
which allows MLBuffet to load and perform inference on them.

When saving custom models without Keras API, Tensorflow does NOT store any function unless the user specifies it. Thus,
in order to use this models with MLBuffet, some additional code must be added:

* The model class must inherit from `tf.Module`. So `class MyModel:` is converted to `class MyModel(tf.Module):`
  * It is recommended to add `super().__init__()` in the `__init__` method of the model class.
* The function to be used when performing inference needs the following decorator:
> @tf.function(input_signature=[tf.TensorSpec(shape=[input_shape], dtype=input_type)]) 


`customTFModelExample.py` provides and example of the preparation needed for non-Keras models. In this example, a CNN 
is built with custom layers and a custom training loop outside the Keras API, then the model is trained, saved and
loaded, performing inference before and after to show that the results are the same.

## More tf.functions and custom signatures
Tensorflow allows to have more than one `tf.function` decorator on the same `tf.module`, and allows giving custom names
to `tf.function` signatures. The behaviour of these models on MLBuffet is untested, MLBuffet relies on the signature 
`serving_default` that is created automatically by Tensorflow when saving Keras models or models without custom
signatures. Having several `tf.function` decorators can alter the way the signatures are stored and lead to unexpected
results.

If there is a need for several `tf.function` or custom signatures, proper functionality with MLBuffet can be ensured
saving the function to be used when performing inference with name `serving_default`.

```
tf.saved_model.save(
    model, pathToSave,
    signatures={
        'serving_default': model.inference_function.get_concrete_function(),
        'other_signature_name': model.other_tf_function.get_concrete_function()
    })
```