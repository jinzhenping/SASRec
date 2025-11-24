import sys
import copy
import torch
import random
import numpy as np
from collections import defaultdict
from multiprocessing import Process, Queue

def build_index(dataset_name):

    ui_mat = np.loadtxt('data/%s.txt' % dataset_name, dtype=np.int32)

    n_users = ui_mat[:, 0].max()
    n_items = ui_mat[:, 1].max()

    u2i_index = [[] for _ in range(n_users + 1)]
    i2u_index = [[] for _ in range(n_items + 1)]

    for ui_pair in ui_mat:
        u2i_index[ui_pair[0]].append(ui_pair[1])
        i2u_index[ui_pair[1]].append(ui_pair[0])

    return u2i_index, i2u_index

# sampler for batch generation
def random_neq(l, r, s):
    t = np.random.randint(l, r)
    while t in s:
        t = np.random.randint(l, r)
    return t


def sample_function(user_train, usernum, itemnum, batch_size, maxlen, result_queue, SEED):
    def sample(uid):

        # uid가 user_train에 없거나 시퀀스 길이가 1 이하인 경우 재선택
        while uid not in user_train or len(user_train[uid]) <= 1:
            # 실제 존재하는 사용자 ID 중에서만 선택
            uid = np.random.choice(valid_user_ids)

        seq = np.zeros([maxlen], dtype=np.int32)
        pos = np.zeros([maxlen], dtype=np.int32)
        neg = np.zeros([maxlen], dtype=np.int32)
        nxt = user_train[uid][-1]
        idx = maxlen - 1

        ts = set(user_train[uid])
        for i in reversed(user_train[uid][:-1]):
            seq[idx] = i
            pos[idx] = nxt
            neg[idx] = random_neq(1, itemnum + 1, ts)          # Don't need "if nxt != 0"
            nxt = i
            idx -= 1
            if idx == -1: break

        return (uid, seq, pos, neg)

    np.random.seed(SEED)
    # 실제 존재하는 사용자 ID만 사용 (시퀀스 길이가 2 이상인 사용자만)
    valid_user_ids = np.array([uid for uid in user_train.keys() if len(user_train[uid]) > 1], dtype=np.int32)
    if len(valid_user_ids) == 0:
        raise ValueError("No valid users with sequence length > 1")
    
    uids = valid_user_ids.copy()
    counter = 0
    while True:
        if counter % len(uids) == 0:
            np.random.shuffle(uids)
        one_batch = []
        for i in range(batch_size):
            one_batch.append(sample(uids[counter % len(uids)]))
            counter += 1
        result_queue.put(zip(*one_batch))


class WarpSampler(object):
    def __init__(self, User, usernum, itemnum, batch_size=64, maxlen=10, n_workers=1):
        self.result_queue = Queue(maxsize=n_workers * 10)
        self.processors = []
        for i in range(n_workers):
            self.processors.append(
                Process(target=sample_function, args=(User,
                                                      usernum,
                                                      itemnum,
                                                      batch_size,
                                                      maxlen,
                                                      self.result_queue,
                                                      np.random.randint(2e9)
                                                      )))
            self.processors[-1].daemon = True
            self.processors[-1].start()

    def next_batch(self):
        return self.result_queue.get()

    def close(self):
        for p in self.processors:
            p.terminate()
            p.join()


# train/val/test data generation
def data_partition(fname):
    usernum = 0
    itemnum = 0
    User = defaultdict(list)
    user_train = {}
    user_valid = {}
    user_test = {}
    # assume user/item index starting from 1
    f = open('data/%s.txt' % fname, 'r')
    for line in f:
        u, i = line.rstrip().split(' ')
        u = int(u)
        i = int(i)
        usernum = max(u, usernum)
        itemnum = max(i, itemnum)
        User[u].append(i)

    for user in User:
        nfeedback = len(User[user])
        if nfeedback < 4:                          # To be rigorous, the training set needs at least two data points to learn
            user_train[user] = User[user]
            user_valid[user] = []
            user_test[user] = []
        else:
            user_train[user] = User[user][:-2]
            user_valid[user] = []
            user_valid[user].append(User[user][-2])
            user_test[user] = []
            user_test[user].append(User[user][-1])
    return [user_train, user_valid, user_test, usernum, itemnum]

# TODO: merge evaluate functions for test and val set
# evaluate on test set
def evaluate(model, dataset, args):
    [train, valid, test, usernum, itemnum] = copy.deepcopy(dataset)

    # Metrics for different K values
    NDCG_5 = 0.0
    NDCG_10 = 0.0
    HR_5 = 0.0
    HR_10 = 0.0
    MRR = 0.0
    valid_user = 0.0

    if usernum>10000:
        users = random.sample(range(1, usernum + 1), 10000)
    else:
        users = range(1, usernum + 1)
    for u in users:

        if len(train[u]) < 1 or len(test[u]) < 1: continue

        seq = np.zeros([args.maxlen], dtype=np.int32)
        idx = args.maxlen - 1
        seq[idx] = valid[u][0]
        idx -= 1
        for i in reversed(train[u]):
            seq[idx] = i
            idx -= 1
            if idx == -1: break
        rated = set(train[u])
        rated.add(0)
        item_idx = [test[u][0]]
        for _ in range(100):
            t = np.random.randint(1, itemnum + 1)
            while t in rated: t = np.random.randint(1, itemnum + 1)
            item_idx.append(t)

        predictions = -model.predict(*[np.array(l) for l in [[u], [seq], item_idx]])
        predictions = predictions[0] # - for 1st argsort DESC

        rank = predictions.argsort().argsort()[0].item()

        valid_user += 1

        # MRR: Mean Reciprocal Rank (1 / rank, 0 if rank >= K)
        if rank < 10:
            MRR += 1.0 / (rank + 1)
        
        # NDCG@5
        if rank < 5:
            NDCG_5 += 1 / np.log2(rank + 2)
            HR_5 += 1
        
        # NDCG@10 and HR@10
        if rank < 10:
            NDCG_10 += 1 / np.log2(rank + 2)
            HR_10 += 1
        
        if valid_user % 100 == 0:
            print('.', end="")
            sys.stdout.flush()

    return {
        'NDCG@5': NDCG_5 / valid_user,
        'NDCG@10': NDCG_10 / valid_user,
        'HR@5': HR_5 / valid_user,
        'HR@10': HR_10 / valid_user,
        'MRR': MRR / valid_user
    }


# evaluate on val set
def evaluate_valid(model, dataset, args):
    [train, valid, test, usernum, itemnum] = copy.deepcopy(dataset)

    # Metrics for different K values
    NDCG_5 = 0.0
    NDCG_10 = 0.0
    HR_5 = 0.0
    HR_10 = 0.0
    MRR = 0.0
    valid_user = 0.0
    if usernum>10000:
        users = random.sample(range(1, usernum + 1), 10000)
    else:
        users = range(1, usernum + 1)
    for u in users:
        if len(train[u]) < 1 or len(valid[u]) < 1: continue

        seq = np.zeros([args.maxlen], dtype=np.int32)
        idx = args.maxlen - 1
        for i in reversed(train[u]):
            seq[idx] = i
            idx -= 1
            if idx == -1: break

        rated = set(train[u])
        rated.add(0)
        item_idx = [valid[u][0]]
        for _ in range(100):
            t = np.random.randint(1, itemnum + 1)
            while t in rated: t = np.random.randint(1, itemnum + 1)
            item_idx.append(t)

        predictions = -model.predict(*[np.array(l) for l in [[u], [seq], item_idx]])
        predictions = predictions[0]

        rank = predictions.argsort().argsort()[0].item()

        valid_user += 1

        # MRR: Mean Reciprocal Rank (1 / rank, 0 if rank >= K)
        if rank < 10:
            MRR += 1.0 / (rank + 1)
        
        # NDCG@5
        if rank < 5:
            NDCG_5 += 1 / np.log2(rank + 2)
            HR_5 += 1
        
        # NDCG@10 and HR@10
        if rank < 10:
            NDCG_10 += 1 / np.log2(rank + 2)
            HR_10 += 1
        
        if valid_user % 100 == 0:
            print('.', end="")
            sys.stdout.flush()

    return {
        'NDCG@5': NDCG_5 / valid_user,
        'NDCG@10': NDCG_10 / valid_user,
        'HR@5': HR_5 / valid_user,
        'HR@10': HR_10 / valid_user,
        'MRR': MRR / valid_user
    }
