import numpy as np
import torch as th
from torch.autograd import Variable


def identity(x):
    return x


def entropy(p):
    return -th.sum(p * th.log(p), 1)


def kl_log_probs(log_p1, log_p2):
    return -th.sum(th.exp(log_p1) * (log_p2 - log_p1), 1)


def index_to_one_hot(index, dim):
    if isinstance(index, np.int) or isinstance(index, np.int64):
        one_hot = np.zeros(dim)
        one_hot[index] = 1.0
    else:
        one_hot = np.zeros((len(index), dim))
        one_hot[np.arange(len(index)), index] = 1.0
    return one_hot


def to_tensor_var(x, use_cuda=True, dtype="float"):
    FloatTensor = th.cuda.FloatTensor if use_cuda else th.FloatTensor
    LongTensor = th.cuda.LongTensor if use_cuda else th.LongTensor
    ByteTensor = th.cuda.ByteTensor if use_cuda else th.ByteTensor
    if dtype == "float":
        x = np.array(x, dtype=np.float64).tolist()
        return Variable(FloatTensor(x))
    elif dtype == "long":
        x = np.array(x, dtype=np.long).tolist()
        return Variable(LongTensor(x))
    elif dtype == "byte":
        x = np.array(x, dtype=np.byte).tolist()
        return Variable(ByteTensor(x))
    else:
        x = np.array(x, dtype=np.float64).tolist()
        return Variable(FloatTensor(x))


def agg_double_list(l):
    # l: [ [...], [...], [...] ]
    # l_i: result of each step in the i-th episode
    s = [np.sum(np.array(l_i), 0) for l_i in l]
    s_mu = np.mean(np.array(s), 0)
    s_std = np.std(np.array(s), 0)
    return s_mu, s_std


def ma_agg_double_list(l):
    # l: [ [...], [...], [...] ] where [...] = [[r11,r21, ...rij],[r12,r22,..rij]] ; agent i and step j
    # l_i: result of each step in the i-th episode
    s = np.array([np.sum(np.array(l_i), axis=0) for l_i in l])
    print(s)

    # [...] = [total_r1, total_r2, ..] ; agent i  of li episode
    s_mu = np.mean(np.array(s), axis=0)
    s_std = np.std(np.array(s), axis=0)
    return s_mu, s_std


def arr_dict_to_arr(arr, n):
    new_arr = []
    while len(arr):
        new_arr.append(dict_to_arr(arr.pop(0), n))
    return new_arr


def dict_to_arr(dct, n):
    arr = []
    for id in range(n):
        arr.append(dct[id])
    return arr
