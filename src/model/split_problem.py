from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import tarfile
from tensor2tensor.data_generators import generator_utils
from tensor2tensor.data_generators import problem
from tensor2tensor.data_generators import text_problems
from tensor2tensor.utils import registry

import tensorflow as tf
import pandas as pd
import numpy as np
import re

@registry.register_problem
class Classification(text_problems.Text2ClassProblem):
    @property
    def is_generate_per_split(self):
        return True

    @property
    def dataset_splits(self):
        return [{
            "split": problem.DatasetSplit.TRAIN,
            "shards": 10,
        }, {
            "split": problem.DatasetSplit.EVAL,
            "shards": 1,
        }]

    @property
    def approx_vocab_size(self):
        return 2**7

    @property
    def num_classes(self):
        return 2

    def class_labels(self, data_dir):
        del data_dir
        return [0, 1]

    def generate_samples(self, data_dir, tmp_dir, dataset_split):
        del data_dir, tmp_dir, dataset_split
        #neg_datas = pd.read_csv('neg.csv')
        #pos_datas = pd.read_csv('pos.csv')
        #neg_ins = neg_datas["ins"].tolist()
        #pos_ins = neg_datas["ins"].tolist()
        #neg_label = neg_datas["label"].tolist()
        #pos_label = pos_datas["label"].tolist()
        #max_len = min(len(neg_ins),len(pos_ins))

        #insl = np.array(neg_ins[0:max_len] + pos_ins[0:max_len])
        #labell = np.array(neg_label[0:max_len] + pos_label[0:max_len])
        #np.random.shuffle(insl)
        #np.random.shuffle(labell)
        tf = open('./split_datas/targets.txt', 'r')
        inf = open('./split_datas/inputs.txt', 'r')
        inputs = inf.readlines()
        tfs = tf.readlines()
        inf.close()
        tf.close()

        for inp, trg in zip(inputs, tfs):
            inp = inp.strip()
            trg = trg.strip()
            yield {
                    "inputs": inp,
                    "label": int(trg)
            }

