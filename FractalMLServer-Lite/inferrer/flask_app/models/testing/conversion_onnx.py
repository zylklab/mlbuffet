import onnxruntime as rt
import numpy
sess = rt.InferenceSession("model.onnx")
input_name = sess.get_inputs()[0].name
label_name = sess.get_outputs()[0].name
testing = [6.4, 2.8, 5.6, 2.2]
testing = numpy.array(testing)
testing = [testing.astype(numpy.float32)]
pred_onx = sess.run([label_name], {input_name: testing})

print(pred_onx[0])

