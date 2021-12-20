import sys
import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import os
import collections

from tensor2tensor import models
from tensor2tensor import problems
from tensor2tensor.layers import common_layers
from tensor2tensor.utils import trainer_lib
from tensor2tensor.utils import t2t_model
from tensor2tensor.utils import registry
from tensor2tensor.utils import metrics
from tensor2tensor.utils import usr_dir

import warnings
warnings.filterwarnings('ignore')

def load_model(data_dir, ckpt_dir, user_dir, problem_name, hparams_name, model_name):
  Modes = tf.estimator.ModeKeys
  usr_dir.import_usr_dir(user_dir)
  
  problem = problems.problem(problem_name)
  hparams = trainer_lib.create_hparams(hparams_name,
                                       data_dir=data_dir,
                                       problem_name=problem_name)
  model = registry.model(model_name)(hparams, Modes.EVAL)
  ckpt_path = tf.train.latest_checkpoint(os.path.join(ckpt_dir, model_name))
  encoders = problem.feature_encoders(data_dir)
  return model, ckpt_path, encoders

def encode(encoder, input_str, output_str=None):
  inputs = encoder["inputs"].encode(input_str)
  batch_inputs = tf.reshape(inputs, [1, -1, 1])
  return {"inputs": batch_inputs}

def decode(ckpt_path, model, encoder, inputs, tfe):
  encoded_inputs = encode(encoder, inputs)
  with tfe.restore_variables_on_create(ckpt_path):
    # print(encoded_inputs)
    output = model.infer(encoded_inputs)["outputs"]
  return output

def trans_decode(encoder, integers):
  integers = list(np.squeeze(integers))
  if 1 in integers:
    integers = integers[: integers.index(1)]
  return encoder["inputs"].decode(np.squeeze(integers))

def model_exe(model, ckpt_path, encoders, input_str, tfe, flag=1):
  # model, ckpt_path, encoders = load_model(data_dir, ckpt_dir, user_dir, problem_name, hparams_name, model_name)
  output = decode(ckpt_path, model, encoders, input_str, tfe)
  if flag == 1:
    output = tf.reshape(output, [1]).numpy()[0]
  else:
    output = trans_decode(encoders, output)
  return output
