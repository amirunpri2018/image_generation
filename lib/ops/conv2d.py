import lib

import numpy as np
import theano
import theano.tensor as T

def Conv2D(name, input_dim, output_dim, filter_size, inputs, he_init=True, mask_type=None, stride=(1,1)):
    """
    inputs: tensor of shape (batch size, num channels, height, width)
    mask_type: one of None, 'a', 'b'

    returns: tensor of shape (batch size, num channels, height, width)
    """
    if mask_type is not None:
        mask_type, mask_n_channels = mask_type

    def uniform(stdev, size):
        return np.random.uniform(
            low=-stdev * np.sqrt(3),
            high=stdev * np.sqrt(3),
            size=size
        ).astype(theano.config.floatX)

    fan_in = input_dim * filter_size**2
    fan_out = output_dim * filter_size**2
    if mask_type is not None: # only approximately correct
        fan_in /= 2.
        fan_out /= 2.

    if he_init:
        filters_stdev = np.sqrt(2./fan_in)
    else: # Normalized init (Glorot & Bengio)
        filters_stdev = np.sqrt(2./(fan_in+fan_out))

    filters = lib.param(
        name+'.Filters',
        uniform(
            filters_stdev,
            (output_dim, input_dim, filter_size, filter_size)
        )
    )

    if mask_type is not None:
        mask = np.ones(
            (output_dim, input_dim, filter_size, filter_size), 
            dtype=theano.config.floatX
        )
        center = filter_size // 2

        # Mask out future locations
        # filter shape is (out_channels, in_channels, height, width)
        mask[:, :, center+1:, :] = 0.
        mask[:, :, center, center+1:] = 0.

        # Mask out future channels
        for i in xrange(mask_n_channels):
            for j in xrange(mask_n_channels):
                if (mask_type=='a' and i >= j) or (mask_type=='b' and i > j):
                    mask[
                        j::mask_n_channels,
                        i::mask_n_channels,
                        center,
                        center
                    ] = 0.

        filters = filters * mask

    biases = lib.param(
        name+'.Biases',
        np.zeros(output_dim, dtype=theano.config.floatX)
    )

    result = T.nnet.conv2d(
        inputs, 
        filters, 
        border_mode='half',
        filter_flip=False,
        subsample=stride
    )
    result = result + biases[None, :, None, None]
    return result