
# r2 = re.compile("add")
#   r3 = re.compile("sub")
#   r4 = re.compile("imul")
#   r5 = re.compile("div")
#   r6 = re.compile("call")

def label_correction(labels, func) -> list:
  import re
  import tools
  r1 = re.compile("mov[\S]* [\S\s]{0,20}- [0-9]{1,10} \[ [e,r]{0,1}bp \] \, ")
  r2 = re.compile("mov[\S]* [\S\s]{1,20} , [\S\s]{0,20}- [0-9]{1,10} \[ [e,r]{0,1}bp \]")
  r3 = re.compile("mov[\S]* ([er]*di|[er]*si|[er]*dx|[er]*cx|r8d|r9d) , [\S]+")
  rs = ['add', 'sub', 'imul', 'div', 'call', 'mul', 'not', 'or', 'and']
  # is_div = tools.is_special_div(func)
  # if is_div:
  #   labels = [0]*(len(labels)-1) + [1]
  #   return labels
  for index, ins in enumerate(func):
    # import pdb
    # pdb.set_trace()
    ins = re.sub('[\s]+', ' ', ins, 10)
    if r1.match(ins):
      labels[index] = 1
    elif r2.match(ins):
      labels[index] = 0
    elif r3.match(ins):
      labels[index] = 0
    else:
      for op in rs:
        r = re.compile(op)
        if r.match(ins):
          labels[index] = 1
          break
  # tmp_blk = []
  # tmp_idx = []
  # for index, ins in enumerate(func):
  #   ins = re.sub('[\s]+', ' ', ins, 10)
  #   if r1.match(ins):
  #     is_div = tools.is_special_div(tmp_blk)
  #     if is_div:
  #       for idx in tmp_idx[:-1]:
  #         labels[idx] = 0
  #       labels[tmp_idx[-1]] = 1
  #     tmp_blk = []
  #     tmp_idx = []
  #   else:
  #     tmp_blk.append(ins)
  #     tmp_idx.append(index)
  labels[-1] = 1
  return labels

# def get_label(func: list, data, ckpt, user, problem, hparams, model_name, tfe) -> list:
def get_label(func: list, m, ckpt, encoders, tfe) -> list:
  import my_model
  labels = []
  for ins in func:
    # label = my_model.model_exe(data_dir=data,
    #                           ckpt_dir=ckpt, 
    #                           user_dir=user, 
    #                           problem_name=problem, 
    #                           hparams_name=hparams, 
    #                           model_name=model_name, 
    #                           input_str=ins,
    #                           tfe=tfe,
    #                           flag=1)
    try:
      label = my_model.model_exe(model=m,
                              ckpt_path=ckpt,
                              encoders=encoders,
                              input_str=ins,
                              tfe=tfe,
                              flag=1)
    except:
      label = 0
    labels.append(label)
  labels = label_correction(labels, func)
  # print(labels)
  return labels

# def get_gadgets(func: list, data, ckpt, user, problem, hparams, model, tfe):
def get_gadgets(func: list, m, ckpt, encoders, tfe):
  gadgets = []
  # import pdb
  # pdb.set_trace()
  labels = get_label(func, m, ckpt, encoders, tfe)
  tmp_gadgets = []
  import re
  for ins, label in zip(func, labels):
    if label == 1:
      tmp_gadgets.append(re.sub('[\s]+', ' ', ins.strip(), 10))
      gadgets.append(tmp_gadgets)
      tmp_gadgets = []
    else:
      tmp_gadgets.append(re.sub('[\s]+', ' ', ins.strip(), 10))
  return gadgets

