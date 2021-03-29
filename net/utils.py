
import numpy as np


def generate_connections(N_tar, N_src, p, same=False):
    ''' 
    connect source to target with probability p
      - if populations SAME, avoid self-connection
      - if not SAME, connect any to any avoididing multiple
    return list of sources i and targets j
    '''
    nums = np.random.binomial(N_tar-1, p, N_src)
    i = np.repeat(np.arange(N_src), nums)
    j = []
    if same:
        for k,n in enumerate(nums):
            j+=list(np.random.choice([*range(k-1)]+[*range(k+1,N_tar)],
                                     size=n, replace=False))
    else:
        for k,n in enumerate(nums):
            j+=list(np.random.choice([*range(N_tar)],
                                     size=n, replace=False))

    return i, np.array(j)


def generate_N_connections(N_tar, N_src, N, same=False):
    ''' 
    connect source to target with N connections per target

    return list of sources i and targets N_tar*N
    '''
    if same:
        return NotImplementedError

    i = np.array([])
    j = np.repeat(range(N_tar), N)

    for k in range(N_tar):
        srcs = np.random.choice(range(N_src), size=N, replace=False)
        i = np.concatenate((i,srcs))

    i,j = i.astype(int), j.astype(int)
    assert len(i)==len(j)

    return i,j



def generate_full_connectivity(Nsrc, Ntar=0, same=True):

    if same:
        i = []
        j = []
        for k in range(Nsrc):
            i.extend([k]*(Nsrc-1))
            targets = list(range(Nsrc))
            del targets[k]
            j.extend(targets)

        assert len(i)==len(j)
        return np.array(i), np.array(j)

    else:
        i = []
        j = []
        for k in range(Nsrc):
            i.extend([k]*Ntar)
            targets = list(range(Ntar))
            j.extend(targets)

        assert len(i)==len(j)
        return np.array(i), np.array(j)


# distance dependent connectivity
# there are 2 methods for generating ddcon: generate_dd_connectivity2 is based on Miner(2016), 
# generate_dd_connectivity uses a bit different approach(see method desc).

def gaussian(x, u, s):
    g_ = (2 / np.sqrt(2 * np.pi * s * s)) * np.exp(-(x - u) * (x - u) / (2 * s * s))  # gaussian used in Miner paper
    g = g_ * 10 ** -4  # rescale to [0,1] range
    # g = np.exp(-(x - u) * (x - u) / (2 * s * s))  # simpler gaussian
    return g


def generate_dd_connectivity2(tar_x, tar_y, src_x, src_y, g_halfwidth, same=True, sparseness=1):
    """
        Generates distance-dependent connectivity.
        Self-connections and multiple connections between one target-source pair are omitted.
        Implementation is based on Miner(2016).

        :param tar_x: target pool x coordinates array (unitless)
        :param tar_y: target pool y coordinates array (unitless)
        :param src_x: source pool x coordinates array (unitless)
        :param src_y: source pool x coordinates array (unitless)
        :param g_halfwidth: gaussian half-width (microns)
        :param same: True is source and target pools are the same, False otherwise
        :param sparseness: connections sparseness, value from [0 1], 1 means full connectivity
        :return: ordered source and target indexes arrays.
        """
    # calculate gaussian
    n_tar = np.size(tar_x)
    n_src = np.size(src_x)
    p_ = np.zeros((n_src, n_tar))
    for i in range(n_src):
        for j in range(n_tar):
            if not same or (same and not (i == j)):
                dx = tar_x[j] - src_x[i]
                dy = tar_y[j] - src_y[i]
                p_[i, j] = gaussian(np.sqrt(dx ** 2 + dy ** 2), 0, np.array(g_halfwidth))

    # calculate connections matrix and indexes arrays

    # determine number of connections to create based on sparseness
    n_new = int(round(n_src * n_tar * sparseness))  # IP: todo this now includes self-connectiones

    conn = np.zeros((n_src, n_tar))  # connectivity matrix
    in_src = []  # list with source indexes
    in_trg = []  # list with target indexes
    for ii in range(n_new):
        addition_allowed = False
        new_i = np.random.randint(0, high=n_src)
        new_j = np.random.randint(0, high=n_tar)
        while not addition_allowed:
            new_i = np.random.randint(0, high=n_src)
            new_j = np.random.randint(0, high=n_tar)
            if np.random.rand() < p_[new_i, new_j]:
                if not new_i == new_j and conn[new_i, new_j] == 0:
                    addition_allowed = True
        conn[new_i, new_j] = 1
        in_src.append(new_i)
        in_trg.append(new_j)
    return in_src, in_trg


def generate_dd_connectivity(tar_x, tar_y, src_x, src_y, g_halfwidth, same=True, sparseness=1):
    """
    Generates distance-dependent connectivity.
    Self-connections and multiple connections between one target-source pair are omitted.

    Implementation is PARTLY based on Miner(2016). In this implementation (1) all connections are generated based on
    gaussian probability and (2) only subset of generated connections is made active, size of subset is determined by
    sparseness parameter.
    This method creates less connections compared to generate_dd_connectivity2

    :param tar_x: target pool x coordinates array (unitless)
    :param tar_y: target pool y coordinates array (unitless)
    :param src_x: source pool x coordinates array (unitless)
    :param src_y: source pool x coordinates array (unitless)
    :param g_halfwidth: gaussian half-width (microns)
    :param same: True is source and target pools are the same, False otherwise
    :param sparseness: connections sparseness, value from [0 1], 1 means full connectivity
    :return: ordered source and target indexes arrays.
    """
    # calculate gaussian
    n_tar = np.size(tar_x)
    n_src = np.size(src_x)
    p_ = np.zeros((n_src, n_tar))
    for i in range(n_src):
        for j in range(n_tar):
            if not same or (same and not (i == j)):
                dx = tar_x[j] - src_x[i]
                dy = tar_y[j] - src_y[i]
                p_[i, j] = gaussian(np.sqrt(dx ** 2 + dy ** 2), 0, np.array(g_halfwidth))

    # calculate connections matrix and indexes arrays
    conn = np.zeros((n_src, n_tar))  # connectivity matrix
    in_src = []  # list with source indexes
    in_trg = []  # list with target indexes
    nums = np.random.uniform(size=n_src*n_tar)
    for i in range(n_src):
        for j in range(n_tar):
            if nums[i*(n_tar-1) + j] < p_[i, j]:
                in_src.append(i)
                in_trg.append(j)
                conn[i, j] = 1  # just indicate a connection, no weight set

    # make only subset of connections active
    if sparseness == 1:
        print('sparseness is 1, all connections are active ')
        in_src_active = np.array(in_src)
        in_trg_active = np.array(in_trg)
    else:
        print('sparseness is ' + str(sparseness))
        n_conn = int(np.size(in_src) * sparseness)
        active_conn = np.random.choice([*range(np.size(in_src))], size=n_conn, replace=False)

        in_src_arr = np.array(in_src)
        in_trg_arr = np.array(in_trg)

        in_src_active = in_src_arr[active_conn]
        in_trg_active = in_trg_arr[active_conn]

    return in_src_active, in_trg_active
