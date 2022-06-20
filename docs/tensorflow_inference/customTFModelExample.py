import tensorflow as tf
import numpy as np

# Code adapted from:
# https://github.com/LAVI-USP/Machine-Learning/blob/master/Deep%20Learning/Classifiers/CNN_cifar10_TF2.ipynb

# This example builds a CNN from scratch, with custom layers and a custom training loop, without the Keras API.
# It also shows how to set up your custom tensorflow models to work with MLBuffet.


class CifarHelper:
    """
    Methods for setting up data from the Cifar10 datasets to work with tensorflow.
    """
    def __init__(self):
        self.i = 0

        # Initialize some empty variables for later on
        self.training_images = None
        self.training_labels = None

        self.test_images = None
        self.test_labels = None

    def set_up_images(self):
        print("Setting Up Training Images and Labels")

        self.training_images = train_images / 255.0
        self.training_labels = self.one_hot_encode(train_labels)

        print("Setting Up Test Images and Labels")

        self.test_images = test_images / 255.0
        self.test_labels = self.one_hot_encode(test_labels)

    @staticmethod
    def one_hot_encode(vec):
        length = len(vec)
        out = np.zeros((length, 10))
        for i in range(length):
            out[i, vec[i]] = 1
        return out

    def next_batch(self, size):
        x = self.training_images[self.i:self.i + size]
        y = self.training_labels[self.i:self.i + size]
        self.i = (self.i + size) % len(self.training_images)
        return x, y


# Convolutional layer
def conv_layer(input_x, w, b):
    # input_x -> [batch,H,W,Channels]
    # filter_shape -> [filters H, filters W, Channels In, Channels Out]

    y = tf.nn.conv2d(input=input_x, filters=w, strides=[1, 1, 1, 1], padding='SAME') + b
    y = tf.nn.relu(y)
    return y


# Pooling layer
def max_pool_layer(x, pool_size):
    # x -> [batch,H,W,Channels]
    return tf.nn.max_pool2d(input=x, ksize=[1, pool_size, pool_size, 1], strides=[1, pool_size, pool_size, 1],
                            padding="SAME")


# Fully connected layer
def fully_connected_layer(input_layer, w, b):
    y = tf.matmul(input_layer, w) + b
    return y


# Helper method
def get_tf_variable(shape, name):
    return tf.Variable(tf.random.truncated_normal(shape, stddev=0.1), name=name, trainable=True, dtype=tf.float32)


class MyModel(tf.Module):
    def __init__(self):

        super().__init__()
        self.pool_size = 2
        self.dropout = 0.5
        self.n_classes = 10

        self.shapes = [
            [5, 5, 3, 32],
            [5, 5, 32, 64],
            [8 * 8 * 64, 512],
            [512, self.n_classes]
        ]

        self.weights = []
        for i in range(len(self.shapes)):
            self.weights.append(get_tf_variable(self.shapes[i], 'weight{}'.format(i)))

        self.bias = []
        for i in range(len(self.shapes)):
            self.bias.append(get_tf_variable([1, self.shapes[i][-1]], 'bias{}'.format(i)))

    # This decorator is what makes the model usable on MLBuffet. It needs the TensorSpec shape and type
    # expected by the model to run. In this case, it expects any number of images with size 32x32 and 3 color channels,
    # hence [None, 32, 32, 3].
    @tf.function(input_signature=[tf.TensorSpec(shape=[None, 32, 32, 3], dtype=tf.float32)])
    def __call__(self, x_input):

        conv1 = conv_layer(x_input, self.weights[0], self.bias[0])
        pool1 = max_pool_layer(conv1, pool_size=self.pool_size)

        conv2 = conv_layer(pool1, self.weights[1], self.bias[1])
        pool2 = max_pool_layer(conv2, pool_size=self.pool_size)

        flat1 = tf.reshape(pool2, [-1, pool2.shape[1] * pool2.shape[2] * pool2.shape[3]])

        fully1 = tf.nn.relu(fully_connected_layer(flat1, self.weights[2], self.bias[2]))

        fully1_dropout = tf.nn.dropout(fully1, rate=self.dropout)

        y_pred = fully_connected_layer(fully1_dropout, self.weights[3], self.bias[3])

        # print(conv1.shape,pool1.shape,conv2.shape,pool2.shape,flat1.shape,fully1.shape,y_pred.shape)
        return y_pred

    def trainable_variables(self):
        return self.weights + self.bias


def loss_function(y_pred, y_true):
    return tf.nn.softmax_cross_entropy_with_logits(labels=tf.stop_gradient(y_true), logits=y_pred)


def train_step(m, x_input, y_true, opt, e, cifar):
    accuracy = None
    loss_avg = None

    with tf.GradientTape() as tape:
        # Get the predictions
        preds = m(x_input)

        # Calc the loss
        current_loss = loss_function(preds, y_true)

        # Get the gradients
        grads = tape.gradient(current_loss, m.trainable_variables())

        # Update the weights
        opt.apply_gradients(zip(grads, m.trainable_variables()))

        if e % 100 == 0:
            y_pred = m(cifar.test_images)
            matches = tf.equal(tf.math.argmax(y_pred, 1), tf.math.argmax(cifar.test_labels, 1))

            accuracy = tf.reduce_mean(tf.cast(matches, tf.float32))
            loss_avg = tf.reduce_mean(current_loss)

            print("--- On epoch {} ---".format(e))
            tf.print("Accuracy: ", accuracy, "| Loss: ", loss_avg)
            print("\n")

        return accuracy, loss_avg


if __name__ == '__main__':
    # Import dataset
    (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.cifar10.load_data()
    ch = CifarHelper()
    ch.set_up_images()

    model = MyModel()
    optimizer = tf.optimizers.Adam(learning_rate=0.001)

    num_epochs = 1
    batch_size = 100

    train_loss_results = []
    train_accuracy_results = []

    # Train loop
    for epoch in range(num_epochs):

        # Get next batch
        batch_x, batch_y = ch.next_batch(batch_size)

        # Train the model
        epoch_accuracy, epoch_loss_avg = train_step(model, batch_x, batch_y, optimizer, epoch, ch)

        if epoch_loss_avg is not None:
            train_loss_results.append(epoch_loss_avg)
            train_accuracy_results.append(epoch_accuracy)

    # Prediction
    n = 784
    pred = model(ch.test_images[n:n + 1])
    tf.print('Original label: ', tf.math.argmax(ch.test_labels[n:n + 1], 1))
    tf.print('Predicted label before saving: ', tf.math.argmax(pred, 1))

    # Save model
    tf.saved_model.save(model, 'cifar_model')

    # Load Model
    loaded = tf.saved_model.load('cifar_model')

    # Predict with loaded model (simplified version of MLBuffet procedure
    serving = loaded.signatures['serving_default']
    input_name = list(serving.structured_input_signature[1].keys())[0]
    output_name = list(serving.structured_outputs.keys())[0]
    args = {
        input_name: tf.constant(ch.test_images[n:n + 1], dtype=serving.structured_input_signature[1][input_name].dtype)}

    pred_load = serving(**args)[output_name].numpy()
    tf.print('Predicted label after save and load: ', tf.math.argmax(pred_load, 1))
