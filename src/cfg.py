import angr
import sys
def get_all_function(binfile):
  p = angr.Project(binfile, load_options={'auto_load_libs': False})
  idfer = p.analyses.Identifier()
  funcs = {}
  for funcInfo in idfer.func_info:
    funcs[funcInfo.addr] = funcInfo.name
  return funcs

def get_funcaddr(binfile, funcname):
  p = angr.Project(binfile, load_options={'auto_load_libs': False})
  func_obj = p.loader.main_object.get_symbol(funcname)
  return func_obj.rebased_addr

def cfg_build(binfile):
  p = angr.Project(binfile, load_options={'auto_load_libs': False})
  # start_state = p.factory.blank_state(addr=funcaddr)
  cfg = p.analyses.CFGEmulated(keep_state=True)
  return cfg

def func_cfg_build(cfg, addr):
  from tools import asm_transition
  entry_func = cfg.kb.functions[addr]
  # graph = entry_func.transition_graph
  # for blk in entry_func.blocks:
    # print(blk.)
  #   # print(blk.capstone)
  #   # pp = blk.pp()
  #   pp = str(blk.capstone)
    # if pp:
    #   print(type(pp))
    #   print(asm_transition(pp))
  return entry_func

def edge_analyses(func):
  LOOP = 0
  IF = 1
  OTHER = 2
  graph = func.graph_ex(False)
  edges = graph.edges
  nodes = graph.nodes
  edge_sets = []
  maps = {}
  for s, e in edges:
    try:
      maps[s].append(e)
    except:
      maps[s] = [e]
  pars = {}
  for s, e in edges:
    try:
      pars[e].append(s)
    except:
      pars[e] = [s]
      pars[s] = []
  loop = []
  for s, e in edges:

    flag = "GOTO"
    if s.addr > e.addr:
      flag = "WHILE"
    else:
      successors = maps[s]
      tmp = []
      for n in successors:
        if type(n) == type(func):
          continue
        else:
          tmp.append(n)
      successors = tmp
      if len(successors) > 1:
        ps = pars[s]
        ch = maps[s]
        flag = 'IF'
        for p in ps:
          if p.addr > s.addr:
            flag = 'WHILE'
            break
        for c in ch:
          if c.addr < s.addr:
            flag = 'GOTO'
            break
    edge_sets.append(((s, e), flag))
  return edge_sets

# def src_cfg_build():

if __name__ == "__main__":
  addr = get_funcaddr(sys.argv[1], sys.argv[2])
  print(addr)
  cfg = cfg_build(sys.argv[1])
  func_cfg = func_cfg_build(cfg, addr)
  print(func_cfg.ret_sites)
  print(str(func_cfg))
  edges = edge_analyses(func_cfg)
  print(edges)