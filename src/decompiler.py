import argparse
import angr
import cfg
import sys
import re
import tensorflow as tf
import time


# data ckpt user problem hparams model_name
MODEL1 = {
          "data": "./model1/data/",
          "ckpt": "./model1/",
          "user": "./model/",
          "problem": "classification",
          "hparams": "lstm_bahdanau_attention",
          "model_name": "lstm_encoder"
          }
MODEL2 = {
          "data": "./model2/data/",
          "ckpt": "./model2/",
          "user": "./model/",
          "problem": "decompile_problem",
          "hparams": "lstm_seq2seq",
          "model_name": "lstm_seq2seq"
          }

def decompile_block(block, tfe, m1, ckpt_path_1, encoders_1,
                    m2, ckpt_path_2, encoders_2):
  import slice
  import tools
  block = tools.form_asm(tools.asm_transition(block))
  block = block_pre_process(block)
  if len(block) == 0:
    return None
  # gadgets = slice.get_gadgets(block,
  #                             MODEL1["data"],
  #                             MODEL1["ckpt"],
  #                             MODEL1["user"],
  #                             MODEL1["problem"],
  #                             MODEL1["hparams"],
  #                             MODEL1["model_name"],
  #                             tfe)
  gadgets = slice.get_gadgets(block, m1, ckpt_path_1, encoders_1, tfe)
  # print("Gadgets: ", gadgets)
  import translate
  srcs = []
  # print(gadgets)
  # for gadget in gadgets:
    # src_t = translate.translate(gadget,
    #                             MODEL2["data"],
    #                             MODEL2["ckpt"],
    #                             MODEL2["user"],
    #                             MODEL2["problem"],
    #                             MODEL2["hparams"],
    #                             MODEL2["model_name"],
    #                             tfe)
  srcs = translate.translate(gadgets,
                              m2,
                              ckpt_path_2,
                              encoders_2,
                              tfe)
    # srcs.append(src_t)
  res = translate.trans_correction(gadgets, srcs)
  return res

def block_pre_process(block: list):
  #jmp
  if block[-1].startswith('jmp'):
    block = block[:-1]
  return block

def main(binfile, tfe):
  import my_model
  print("Loading Slice Model...")
  start = time.clock()
  m1, ckpt_path_1, encoders_1 = my_model.load_model(MODEL1["data"],
                              MODEL1["ckpt"],
                              MODEL1["user"],
                              MODEL1["problem"],
                              MODEL1["hparams"],
                              MODEL1["model_name"])
  load_model1 = time.clock()
  print("Model Loaded.")
  print("Loading Translate Model...")
  model2_start_time = time.clock()
  m2, ckpt_path_2, encoders_2 = my_model.load_model(MODEL2["data"],
                              MODEL2["ckpt"],
                              MODEL2["user"],
                              MODEL2["problem"],
                              MODEL2["hparams"],
                              MODEL2["model_name"])
  # funcs = cfg.get_all_function(binfile)
  model2_load_time = time.clock()
  print("Model Loaded.")
  # funcs = ["main","func1", "func2", "func3", "func4", "func5","func6","func7","func8","func9","func10"]
  funcs = ["main"]
  print("Analyses Binary file...")
  bincfg = cfg.cfg_build(binfile)
  decompile_start = time.clock()
  for name in funcs:
    # import pdb
    # pdb.set_trace()
    addr = cfg.get_funcaddr(binfile, name)
    func_cfg = cfg.func_cfg_build(bincfg, addr)
    # import pdb
    # pdb.set_trace()
    if func_cfg.is_syscall or func_cfg.name.startswith('_') or func_cfg.is_plt or func_cfg.is_simprocedure or "register_tm_clones" in func_cfg.name or "frame_dummy" in func_cfg.name:
      continue
    # print(func_cfg.name)
    blocks = func_cfg.blocks
    ret = func_cfg.ret_sites
    edges = cfg.edge_analyses(func_cfg)
    maps = []
    for block in blocks:
      blk_id = block
      # print(block.capstone)
      # print()
      block = str(block.capstone).split('\n')
      tmp = [':'.join(ins.split(':')[1:]).strip() for ins in block]
      tmp_blk = []
      for ins in tmp:
        if re.match(r"push[\s]+[er]*bp", ins):
          continue
        elif re.match(r"mov[\s]+[er]*bp,[\s][er]*sp", ins):
          continue
        elif re.match(r"sub[\s]+[re]*sp,[\s][0-9]+", ins):
          continue
        elif ins == "leave" or ins == "ret" or ins == "endbr64" or re.fullmatch("pop\srbp",ins):
          continue
        else:
          tmp_blk.append(ins)
      block = '\n'.join(tmp_blk)
      block_src_map = decompile_block(block, tfe,
                    m1, ckpt_path_1, encoders_1,
                    m2, ckpt_path_2, encoders_2)
      if block_src_map == None:
        pass
      else:
        maps.append((blk_id, block, block_src_map))
    import data_flow
    tmp_map = data_flow.rec_data_flow(maps)
    import func
    inss = []
    for blk in blocks:
      inss = inss + blk.strip().split('\n')
    args = func.argument(inss)
    print(f"Name: {func_cfg.name}")
    print(f"Arguments: {args}")
    print("Function body:")
    print(f"Edges: {edges}")
    count = 0
    func_body = func.build_code(edges, tmp_map, name, args)
    if len(ret) > 0:
      func_body.append('\treturn tmp;')
    if len(ret) > 0:
      print('uint32_t %s(%s) {' % (func_cfg.name, ', '.join(list(args))))
    print('\n'.join(func_body))
    print('}')
  end = time.clock()

  print(f"Model 1 Load Time: {load_model1 - start}s")
  print(f"Model 2 Load Time: {model2_load_time-model2_start_time}s")
  print(f"Decompile Time: {end-decompile_start}s")
  print(f"Time: {end-start}s")


if __name__ == "__main__":
  # parser = argparse.ArgumentParser(description='Some data processes')
  # subparsers = parser.add_subparsers(help='sub-command help')

  # parser_1 = subparsers.add_parser('decompiler', help='Decompiler.')
  # parser_1.add_argument('-i', "--binfile", help="Path to ELF file.")
  tfe = tf.contrib.eager
  tfe.enable_eager_execution()
  main(sys.argv[1], tfe)
