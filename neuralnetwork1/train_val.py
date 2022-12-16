
""" Functions to be used to train and validate a Fully-Connected NN.
"""

# import packages
from typing import Callable
from typing import Tuple 
from itertools import product # for grid and random search
import math
import numpy as np
import matplotlib.pyplot as plt

# import classes
from topologyNN import OutputLayer, HiddenLayer


# defining activation functions that will be used
def sigmoid(net_ : float) -> float:

    """ Sigmoidal activation function.

    Parameters
    ----------
        net_ : float
            the weighted sum of the inputs to a given unit.

    Returns
    ----------
        out_ : float
            the sigmoidal activation function evaluated on the net_.
    """
    out_ = 1 / (1 + math.exp(- net_))

    return out_


def linear(net_ : float) -> float:

    """ Linear activation function.

    Parameters
    -----------
        net_ : float
            the weighted sum of the inputs to a given unit.

    Returns
    ----------
        out_ : float
            the linear activation function evaluated on the net_.
    """
    out_ = net_

    return out_

def network_initialization(num_layers : int, units_per_layer : list, num_inputs : int, seed : int, 
                           eta_0 : float, alpha : float, lamb : float, lamb0 : float, 
                           activation_output : Callable[[float], float],
                           activation_hidden : Callable[[float], float]) -> list:

    """ Function to initialize the network.

    Parameters
    ----------
        num_inputs : int
            number of inputs for each pattern.

        num_layers : int
            number of hidden layers + output layer to initialize.

        units_per_layer : list
            list of integers specifying for each layer how many units
            to instantiate.

        seed : int
            seed for the random generation of the weights.

        eta_0 : float
            maximum learning rate for the alghoritm speed control.

        alpha : NoneType or float
            coefficient for the momentum implementation, with value None
            if not implemented or a number passed from the user.

        lamb : float
            lambda in the penalty term for regularization (word lambda
            is not used because it is a reserved word in Python).

        lamb0 : float
            the same as for lamb but for the bias term.

        activation_hidden : function
            activation function to be applied to the net of
            the hidden unit.

        activation_output : function
            activation function to be applied to the net of
            the output unit.

    Returns
    ----------
        layers_list : list
            list of initialized hidden layers + output layer.
    """
    if len(units_per_layer) != num_layers:
        raise ValueError('Lenght of units_per_layer should be equal to num_layers')
    if num_layers < 2:
        raise ValueError('Lenght of num_layers should be >=2, no hidden layers have been created')

    layers_list = []
    # putting all the inputs equal to zero
    to_pass = np.zeros(num_inputs)

    for i in range(num_layers):
        if i != num_layers - 1 :
            if i == 0:
                hidden_layer = HiddenLayer(activation_hidden, units_per_layer[i], to_pass, seed, eta_0,
                                           alpha, lamb, lamb0)
                layers_list += [hidden_layer]
            else:
                hidden_layer = HiddenLayer(activation_hidden, units_per_layer[i],
                                       np.zeros(units_per_layer[i-1]), seed, eta_0, alpha, lamb, lamb0)
                layers_list += [hidden_layer]
        else:
            output_layer = OutputLayer(activation_output, units_per_layer[i], np.zeros(units_per_layer[i-1]),
                                       seed, eta_0, alpha, lamb, lamb0)
            layers_list += [output_layer]

    return layers_list # list of initialized hidden layers + output layer


def feedforward_network(layers_list : list, to_pass : np.ndarray) -> np.ndarray:

    """Function for the feedforward propagation of all the
       hidden layers and the output layer for a single pattern.

    Parameters
    ----------
        layers_list : list
            list of layers (hidden layers + output layer).

        to_pass : np.ndarray
            array with inputs (row from the Dataset).

    Returns
    ----------
        to_pass : np.ndarray
            array with outputs of the output layer.
    """
    for layer_index in range(len(layers_list)):
        # updating inputs with the outputs of the first inner layer
        layers_list[layer_index].inputs = to_pass

        # computing the feedforward propagation of the current layer and saving its
        # output in order to update the inputs of the next layer of the network
        to_pass = layers_list[layer_index].feedforward_layer()

    return to_pass # outputs of the output layer


def backprop_network(layers_list : list, target_layer : np.ndarray, minibatch_size : int,
                     task : str, thr : float) -> float:

    """ Function for the standard back-propagation of the output layer
        and all the hidden layers for a single pattern.

    Parameters
    ----------
        layers_list : list
            list of layers (hidden layers + output layer).

        target_layer : np.ndarray
            target array of the current input row used for the
            previous feedforward step.

        minibatch_size : int
            mini-batch's size considered for the weights update.

        task : str
            specify if the task is a regression or a binary classification.
            
        thr : str
            used in the binary classification's output unit to assign 1/0 as label:
            when output >= thr, 1 is assigned, 0 otherwise.

    Returns
    ----------
        error : float
            the training error for a single pattern computed as:
            (0.5 * the sum over output layers of the square of errors).
    """
    # computing the error for the output layer (total error of the network on a TR pattern)
    pattern_error = 0.5*sum((target_layer - layers_list[-1].layer_outputs)**2)

    # computing the backpropagation for the output layer
    delta = layers_list[-1].backprop_layer(target_layer, minibatch_size)

    # looping over all the hidden layers in reverse
    for layer_index in range(len(layers_list)-2,-1,-1):

        # taking the weights matrix of first outer layer
        weights_next = layers_list[layer_index + 1].weights_matrix
        # taking the bias array of first outer layer
        bias_next = layers_list[layer_index + 1].bias_array

        # computing the backpropagation and updating the delta for the inner hidden layer
        # of the network for which the backprop will be computed
        delta = layers_list[layer_index].backprop_layer(delta, weights_next, bias_next, minibatch_size)

    if task == 'binary_classification':
        #evaluate if there is a mathch between the predicted label and the actual label of the pattern
        if layers_list[-1].layer_outputs[0] >= thr:
            label = 1
        else:
            label = 0
            
        if label == target_layer[0]:
            acc_increase = 1
        else:
            acc_increase = 0
            
        return pattern_error, acc_increase #return the error and the matching result

    if task == 'regression':
        return pattern_error, 0 #return the error and a 0 for consistency with variable assignment in train function


def reset_mini_batch(layers_list):

    """ Function to reset counter and gradient_sum for each unit and for each layer
    at the beginning of each epoch.

    Parameters
    ----------
        layers_list : list
            list of layers (hidden layers + output layer).
    """
    for layer in layers_list[:-1]:
        for hidden_unit in layer.hidden_units:
            hidden_unit.counter = 0
            hidden_unit.gradients_sum = 0
            
    for output_unit in layers_list[-1].output_units:
        output_unit.counter = 0
        output_unit.gradients_sum = 0


def train(data_train : np.ndarray, layers_list : list, num_inputs : int, 
          minibatch_size : int, task : str, thr : float) -> Tuple[list, float]:

    """ Function to train the network over a single epoch.

    Parameters
    ----------
        data_train : np.ndarray
            array of inputs + targets to be used for the training process.

        num_inputs : int
            number of inputs for each pattern.

        minibatch_size : int
            mini-batch's size considered for the weights update.

        layers_list : list
            list of hidden layers + output layer.

        task : str
            specify if the task is a regression or a binary classification.
            
        thr : str
            used in the binary classification's output unit to assign 1/0 as label:
            when output >= thr, 1 is assigned, 0 otherwise.

    Returns
    ----------
        layers_list : list
            list of trained hidden layers + output layer.

        epoch_error : float
            training error computed over an epoch.
    """
    # reset mini-batch at the beginning of each epoch
    reset_mini_batch(layers_list)
    # reset epoch_error every time the training phase is computed
    # over a new epoch
    epoch_error = 0
    accuracy = 0

    # performing the training for one epoch
    for index in range(len(data_train[:, 0])):
        # inputs to be passed
        to_pass = data_train[index, :num_inputs]
        # computing the feedforward propagation for every layer in the network
        output = feedforward_network(layers_list, to_pass)
        # computing the backpropagation for every layer in the network
        pattern_error, acc_increase = backprop_network(layers_list, data_train[index, num_inputs:], minibatch_size,
                                                        task = task, thr = thr)

        # computing the training error over an epoch
        epoch_error += pattern_error

        if task == 'binary_classification':
            accuracy += acc_increase

    if task == 'regression':
        epoch_error = epoch_error/len(data_train[:, 0])
    
        return layers_list, epoch_error, 0     #return model, epoch_error and 0 for consistency with cross-val function
    
    if task == 'binary_classification':
        
        epoch_error = epoch_error/len(data_train[:, 0])
        accuracy = accuracy/len(data_train[:, 0])
    
        return layers_list, epoch_error, accuracy


def gridsearch(dictionary : dict, num_targets : int) -> np.ndarray:

    ''' Function for a sequential search in a space of hyperparameters under
        the form of a dictionary: it must have a key 'layers' indicating
        possible numbers of hidden layers, a key 'units' indicating
        possible values for the number of units in every layer.

    Parameters
    ----------
        dictionary : dict
            dictionary with possible values for the network hyperparameters.

        num_targets : int
            dimension of the output layer (number of output units).

    Returns
    -----------
        output_array : np.ndarray
            array of dictionaries with all the possible configurations of
            hyperparameters.
    '''
    output_array = np.empty(0, dtype = dict)

    keys = list(dictionary.keys())
    keys.remove('units')
    for param_set in product(*[dictionary[key] for key in keys]):
        param_dict = {key : params for key, params in zip(keys, param_set)}
        for units in product(dictionary['units'], repeat = int(param_dict['layers'])):
            units = np.array(units)
            output_dict = {'units' : np.append(units, num_targets)}
            output_dict.update(param_dict)
            output_dict['layers'] = output_dict['layers'] + 1
            output_array = np.append(output_array, output_dict)

    return output_array


def randomsearch(dictionary : dict, num_targets : int, configurations : int) -> np.ndarray:

    ''' Function for a stochastic search in a space of hyperparameters under
        the form of a dictionary: it must have a key 'layers' indicating
        possible numbers of hidden layers, a key 'units' indicating
        possible values for number of units in every layer.

    Parameters
    ----------
        dictionary : dict
            dictionary with possible values for the network hyperparameters.

        num_targets : int
            dimension of the output layer (number of output units).

        configurations : int
            number of different configurations to be generated.

    Returns
    -----------
        output_array : np.ndarray
            array of dictionaries with stochastic configurations of
            hyperparameters.
    '''
    output_array = np.empty(0, dtype = dict)

    keys = list(dictionary.keys())
    keys.remove('units')
    for index in range(configurations):
        param_dict = dict()
        for key in keys:
            param_dict[key] = np.random.choice(dictionary[key])
        param_dict['units'] = np.random.choice(dictionary['units'], param_dict['layers'])
        param_dict['units'] = np.append(param_dict['units'], num_targets)
        param_dict['layers'] = param_dict['layers'] + 1
        output_array = np.append(output_array, param_dict)

    return output_array


def split_tvs_kfCV(tvs_array : np.ndarray, k : int) -> list:

    """ Function to split the Dataset.

    Parameters
    ----------
        tvs_array : np.ndarray
            array of inputs + targets to be splitted.

        k : int
            number of folds in which the original array has
            be splitted.

    Returns
    ----------
        folds_data : list
            list of numpy arrays in which the original array has
            been splitted.
    """
    # first thing first shuffle the Dataset every time
    # the original Dataset is resplitted
    np.random.shuffle(tvs_array)

    # dividing the shuffled Dataset into k dinstinct
    # and equal subparts (except for the last one)
    rest_ = len(tvs_array) % k
    length_fold = int(len(tvs_array) / k)
    folds_data = [np.zeros(1) for i in range(k)]
    for i in range(k):
        if i != k-1:
            folds_data[i] = tvs_array[length_fold*i:length_fold*(i+1), :]
        else:
            folds_data[i] = tvs_array[length_fold*i:length_fold*(i+1)+rest_, :]

    return folds_data


def stopping_criteria(epochs_error_train : list, epochs_error_val : list,
                      layers_model : list, stop_class : str,
                      stop_param = 1) -> Tuple[bool, list, list, list]:
    """ Function to define when to stop in the training and validation phases.
    
    Arguments
    ----------
    epochs_error_train : list
        List of errors over training set for each epoch.

    epochs_error_val : list
        List of errors over validation set for each epoch.

    layers_model : list
        List containing trained layers (istances of classes HiddenLayer
        and OutputLayer with fixed weights).

    stop_class : str
        Select a particular algorithm for ealry stopping implementation
        and there are three possible choices:
        UP ............ Stop after a deafult number of validation error
                        increasing epochs.
        GL ............ Stop as soon the generalization loss exceeds a
                        certain threshold.
        PQ ............ Stop as soon the ratio between generalization loss 
                        and progress exceeds a certain threshold.
    """

    if stop_class not in ['ST', 'UP', 'GL', 'PQ']:
        raise ValueError('Unknown stopping algorithm')

    if stop_class == 'ST':
        # first consider early stopping: if the validation error 
        # continues to increase w.r.t. the previous 20 epochs come back of 20 epochs
        epochs = 20
        counter = 0
        for i in range(epochs):
            if i != epochs-1:
                if epochs_error_val[-i-1] > epochs_error_val[-i-2]:
                    counter += 1
        if counter == epochs-1:
            val_ = True
        else:
            val_ = False

        # checking if the learning curve for the training was at an asymptote
        # 20 epochs before the current one
        train_ = False
        if val_ == True:
            counter = 0
            for i in range(epochs):
                if epochs_error_train[-i-1] >= epochs_error_train[-i-2] - (10**(-3))*epochs_error_train[-i-2]:
                        counter += 1
            if counter == epochs-1:
                train_ = True
            else:
                train_ = False

        if train_ == True:
            # coming back of 20 epochs and return True
            epochs_error_train[-1:-20] = []
            epochs_error_val[-1:-20] = []
            layers_model[-1:-20] = []

            return True, epochs_error_train, epochs_error_val, layers_model

        else:
            return False, epochs_error_train, epochs_error_val, layers_model

    if stop_class == 'UP':

        # number of strips and their length
        strips = stop_param
        k = 5

        # checking if epochs are enought
        if len(epochs_error_val) > k * strips:

            # initialize a counter for stop check
            counter = 0

            # optimal validation error up to now
            optimal = min(epochs_error_val)
            min_index = epochs_error_val.index(optimal)

            # count how mant time 
            for index in range(strips):
                if epochs_error_val[-1-index*k] > epochs_error_val[-1-(index+1)*k]:
                    counter += 1
                    print(counter)
            if counter == strips:
                epochs_error_train = epochs_error_train[:min_index+1]
                epochs_error_val = epochs_error_val[:min_index+1]
                layers_model =  layers_model[:min_index+1]
                return True, epochs_error_train, epochs_error_val, layers_model
            else:
                return False, epochs_error_train, epochs_error_val, layers_model
        else:
            return False, epochs_error_train, epochs_error_val, layers_model

    if stop_class == 'GL':

        # threshold for generalization loss (percentage)
        # and optimal validation error up to now
        threshold = stop_param
        optimal = min(epochs_error_val)
        min_index = epochs_error_val.index(optimal)

        # generalization loss
        gen_loss = 100 * ((epochs_error_val[-1] / optimal) - 1)
        print(f'Loss: {gen_loss}')

        # condition check
        if gen_loss > threshold:
            epochs_error_train = epochs_error_train[:min_index+1]
            epochs_error_val = epochs_error_val[:min_index+1]
            layers_model =  layers_model[:min_index+1]
            return True, epochs_error_train, epochs_error_val, layers_model
        else:
            return False, epochs_error_train, epochs_error_val, layers_model

    if stop_class == 'PQ':

        # threshold for the loss progress ratio (percentage)
        # and optimal validation error up to now
        threshold = stop_param
        optimal = min(epochs_error_val)
        min_index = epochs_error_val.index(optimal)

        # generalization loss
        gen_loss = 100 * ((epochs_error_val[-1] / optimal) - 1)

        # progress up to now
        min_train = min(epochs_error_train[-20:])
        sum_train = sum(epochs_error_train[-20:])
        progress = 1000 * ((sum_train / 20 * min_train) - 1)

        # loss progress ratio
        ratio = gen_loss / progress
        print(f'Ratio: {ratio}')

        # condition check
        if ratio > threshold:
            epochs_error_train = epochs_error_train[:min_index+1]
            epochs_error_val = epochs_error_val[:min_index+1]
            layers_model =  layers_model[:min_index+1]
            return True, epochs_error_train, epochs_error_val, layers_model
        else:
            return False, epochs_error_train, epochs_error_val, layers_model

def search_space_dict(num_targets : int, configurations : int,
                      layers_range : np.ndarray, units_range : np.ndarray,
                      eta_0_range : np.ndarray, alpha_range : np.ndarray,
                      lamb_range : np.ndarray, lamb0_range : np.ndarray,
                      minibatch_size_range : np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

    """ Function to define the hyperparameter space where to search.

    Parameters
    ----------
        num_targets : int
            dimension of the output layer (number of output units).

        configurations : int
            number of different configurations to be generated.

        layers_range : np.ndarray
            array with possible numbers of hidden layers.

        units_range : np.ndarray
            array with 

        eta_0_range : np.ndarray
            array with possible values for eta_0.

        alpha_range : np.ndarray
            array with possible values for alpha.

        lamb_range : np.ndarray
            array with possible values for lamb.

        lamb0_range : np.ndarray
            array with possible values for lamb0.

        minibatch_size_range : np.ndarray
            array with possible values for the minibatch_size.

    Returns
    ----------
        grid_search_array : np.ndarray
            array of dictionaries with all the possible configurations of
            hyperparameters.

        random_search_array : np.ndarray
            array of dictionaries with stochastic configurations of
            hyperparameters.
    """
    search_dict = {
    'layers' : layers_range,
    'units' : units_range,
    'eta_0' : eta_0_range,
    'alpha' : alpha_range,
    'lamb' : lamb_range,
    'lamb0' : lamb0_range,
    'minibatch_size' : minibatch_size_range }

    # calls the gridsearch function
    grid_search_array = gridsearch(search_dict, num_targets)
    # calls the randomsearch function
    random_search_array = randomsearch(search_dict, num_targets, configurations)

    return grid_search_array, random_search_array


def performing_tv(layers_range : np.ndarray, units_range : np.ndarray, num_inputs : int,
                  num_targets : int, tvs_array : np.ndarray, k_range : np.ndarray, eta_0_range : np.ndarray,
                  alpha_range : np.ndarray, lamb_range : np.ndarray, lamb0_range : np.ndarray,
                  configurations : int, minibatch_size_range : int, activation_output : Callable[[float], float],
                  activation_hidden : Callable[[float], float], stop_class : str, stop_param : float,
                  task : str, thr : float) -> list:

    """ Function for performing training and validation phases.
    """
    # defining/initializing the hyperparameter space where to search
    grid_search_array, random_search_array = search_space_dict(num_targets, configurations, layers_range, units_range,
                                     eta_0_range, alpha_range, lamb_range, lamb0_range, minibatch_size_range)

    # iterate 10 times for weights initializations changing the seed
    for seed in range(10):

        # iterate on different k for splitting the Dataset
        trained_optimal_model = [] # list to store the trained optimal model for each splitting

        for index, k in enumerate(k_range):

            # shuffling and splitting the original dataset
            folds_data = split_tvs_kfCV(tvs_array, k)

            # looping over every hyperparameter (in grid_search_array) and every fold 
            for hyperparams in grid_search_array:

                folds_error_val = [] # list to store the validation errors for every model obtained with
                                     # every fold
                mean_val_error = []  # list to store the mean of the empirical errors using the validation sets
                                     # computed over the folds for every splitting cycle
                storing_hyperparams = [] # list to store 

                for index_fold in range(len(folds_data)):

                    epochs_error_train = [] # list to store training errors that has to be empty every time we
                                            # do it on a different fold
                    epochs_error_val = []   # list to store validation errors
                    layers_model = []       # list to store the model obtained at each epoch, used to implement
                                            # early stopping

                    print(f'Parameters {hyperparams}, fold {index_fold}\n:')

                    # initializing the network (initialize the network every time we have a different fold
                    # with the same seed -> in this way we have the same weights initializations in this loop)
                    layers_list = network_initialization(num_layers = hyperparams['layers'], 
                                                 units_per_layer = hyperparams['units'], num_inputs = num_inputs, seed = seed,
                                                 eta_0 = hyperparams['eta_0'], alpha = hyperparams['alpha'],
                                                 lamb = hyperparams['lamb'], lamb0 = hyperparams['lamb0'],
                                                 activation_output = activation_output, activation_hidden = activation_hidden)

                    # data array for the validation phase
                    data_val = folds_data[index_fold]
                    # data array for the training phase
                    data_train_list = []
                    for i in range(len(folds_data)):
                        if i != index_fold:
                            data_train_list += [folds_data[i]]
                    data_train = data_train_list[0]
                    for i in range(len(data_train_list)):
                        if i != 0:
                            data_train = np.append(data_train, data_train_list[i], axis = 0)

                    # until stopping condition is verified perform the training and validation phases for new epochs
                    condition = False
                    counter = 0
                    epochs = 20
                    max_epochs = 1000

                    while (condition != True and counter <= max_epochs):

                        # update the counter
                        counter += 1
                        # shuffle training and validation sets for every epoch
                        np.random.shuffle(data_train)
                        np.random.shuffle(data_val)

                        # perform the training phase and store the model and the epoch's error
                        layers_list, epoch_error, accuracy = train(data_train, layers_list, num_inputs,
                                                         minibatch_size = hyperparams['minibatch_size'],
                                                         task = task, thr = thr)

                        epochs_error_train += [epoch_error]
                        layers_model += [layers_list]

                        # estimating the empirical error using the validation set computed over the
                        # current epoch and storing it
                        epoch_error_val = 0
                        for i in range(len(data_val[:, 0])):
                            epoch_error_val += (1 / len(data_val[:,0])) * \
                                sum((feedforward_network(layers_list, data_val[i, :num_inputs]) - data_val[i, num_inputs:])**2)

                        epochs_error_val += [epoch_error_val]

                        # printing out training and validation errors over the epochs
                        print(f'training error {epochs_error_train[-1]}, validation error {epochs_error_val[-1]}')

                        # see if the stopping condition is verified: if yes leaves the loop
                        if counter >= epochs:
                            condition, epochs_error_train, epochs_error_val, layers_model = stopping_criteria(
                                                epochs_error_train, epochs_error_val, layers_model,
                                                stop_class, stop_param)

                    # plotting the learning curve for the current fold and the current hyperparameters set
                    plt.plot(range(len(epochs_error_train)), epochs_error_train, marker = ".", color = 'blue')
                    plt.plot(range(len(epochs_error_val)), epochs_error_val, marker = ".", color = 'green')
                    plt.title(f'Learning curve (fold {index_fold})')
                    plt.xlabel('Epochs')
                    plt.ylabel('Error')
                    plt.legend(['Training Error', 'Validation Error'])
                    plt.show()

                    folds_error_val += [epochs_error_val[-1]]

                # estimating the mean of the empirical errors using the validation sets computed over the folds
                mean_val_error += [(1/k)*sum(folds_error_val)]

                # storing hyperparameters for selecting the optimal ones
                storing_hyperparams += [hyperparams]

            # selecting the best model hyperparameters comparing the mean_val_error
            min_index = mean_val_error.index(min(mean_val_error)) # index corresponding to the minimum value
            optimal_hyperparams = storing_hyperparams[min_index]

            # now retrain the model using all the dataset (before initialize it)
            layers_list = network_initialization(num_layers = optimal_hyperparams['layers'], 
                                                 units_per_layer = optimal_hyperparams['units'], num_inputs = num_inputs,
                                                 eta_0 = optimal_hyperparams['eta_0'], alpha = optimal_hyperparams['alpha'],
                                                 lamb = optimal_hyperparams['lamb'], lamb0 = optimal_hyperparams['lamb0'],
                                                 activation_output = activation_output, activation_hidden = activation_hidden)
            layers_list, epoch_error, accuracy = train(tvs_array, layers_list, num_inputs, optimal_hyperparams['minibatch_size'],
                                             task =  task, thr = thr)

            # storing the trained optimal model
            trained_optimal_model += [layers_list]

        # selecting the mean model
        layers_list = (1 / len(k_range)) * sum(trained_optimal_model)
        # storing the trained optimal model
        trained_optimal_model += [layers_list]

    # selecting the mean model
    layers_list = (1 / len(k_range)) * sum(trained_optimal_model)


    return layers_list # the trained model with optimal hyperparameters