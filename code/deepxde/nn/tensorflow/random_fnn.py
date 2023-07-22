from .nn import NN
from .. import activations
from .. import initializers
from .. import regularizers
from ...backend import tf
import numpy as np

class random_FNN(NN):
    """Fully-connected neural network."""

    def __init__(
        self,
        layer_sizes,
        activation,
        kernel_initializer,
        Rm=1,
        b=0.0005,
        regularization=None,
        dropout_rate=0,
    ):
        super().__init__()
        self.regularizer = regularizers.get(regularization)
        self.dropout_rate = dropout_rate

        self.denses = []
        if isinstance(activation, list):
            if not (len(layer_sizes) - 1) == len(activation):
                raise ValueError(
                    "Total number of activation functions do not match with sum of hidden layers and output layer!"
                )
            activation = list(map(activations.get, activation))
        else:
            activation = activations.get(activation)
        initializer = initializers.get(kernel_initializer)
        for j, units in enumerate(layer_sizes[1:-1]):
            freeze = True
            init = initializer
            bias = "zeros"
            if j == 0:
                freeze = False
                init = tf.keras.initializers.RandomUniform(minval=-Rm, maxval=Rm)
                bias = tf.keras.initializers.RandomUniform(minval=-b, maxval=b)
            else:
                freeze = True
                init = initializer
                bias = "zeros"
            self.denses.append(
                tf.keras.layers.Dense(
                    units,
                    activation=(
                        activation[j]
                        if isinstance(activation, list)
                        else activation
                    ),
                    kernel_initializer=init,
                    kernel_regularizer=self.regularizer,
                    bias_initializer=bias, 
                    trainable=freeze,
                )
            )
            if self.dropout_rate > 0:
                self.denses.append(tf.keras.layers.Dropout(rate=self.dropout_rate))

        self.denses.append(
            tf.keras.layers.Dense(
                layer_sizes[-1],
                kernel_initializer=initializer,
                kernel_regularizer=self.regularizer,
            )
        )

    def call(self, inputs, training=False):
        y = inputs
        if self._input_transform is not None:
            y = self._input_transform(y)
        for f in self.denses:
            y = f(y, training=training)
        if self._output_transform is not None:
            y = self._output_transform(inputs, y)
        return y
    


class partioned_random_FNN(NN):
    """Fully-connected neural network."""

    def __init__(
        self,
        layer_sizes,
        activation,
        kernel_initializer,
        npart,
        indicatrici,  # funzione di tensorflow
        Rm=1,
        b=0.0005,
        regularization=None,
        dropout_rate=0,
    ):
        super().__init__()
        self.regularizer = regularizers.get(regularization)
        self.dropout_rate = dropout_rate
        
        #self.denses = np.empty(npart, dtype=object)

        self.nets = [random_FNN(layer_sizes,activation,kernel_initializer,Rm,b,regularization,dropout_rate) for i in range(npart)]

        self.denses = [self.nets[i].denses for i in range(npart)]

        self.indicatrici = indicatrici
        self.npart = npart

    def call(self, inputs, training=False):

        x = inputs
        res = 0
        #print(x)
        for i in range(self.npart):
            y = inputs
            if self._input_transform is not None:
                y = self._input_transform(y)
            ind = self.indicatrici[i](x)
            #y = tf.math.multiply(y, self.indicatrici[i](x))
            #print(ind)
            for f in self.denses[i]:
                #y = f(y, training=training)#*self.indicatrici[i](x)
                y = tf.math.multiply(f(y, training=training), self.indicatrici[i](x))
                #print(y)
                #y = tf.math.multiply(y, self.indicatrici[i](y))
                #print(y)
            #print(y)
            if self._output_transform is not None:
                y = self._output_transform(inputs, y)
            res += y

        return res

        '''for f, eta in zip(self.nets, self.indicatrici):
            res += f(y, training=training)*eta(y)
  
        return y'''