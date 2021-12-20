

def argument(func: list):
  import re

  # register arguments
  regp = re.compile(r"mov[\S]* (rdi|rsi|rdx|rcx|r8d|r9d|edi|esi|edx|ecx) , [\S\s]+")

  params = set()
  for ins in func:
    match = regp.fullmatch(ins)
    if match:
      params.add(match[1])
  
  # stack argments
  stackp = re.compile(f"[\s\S]*(\[[er]*bp \+ 0x[0-9a-f]+\])[\s\S]*")  ## use befor ins form  [rbp -+ xxx]
  for ins in func:
    match = stackp.match(ins)
    if match:
      for offset in match.groups():
        params.add(offset)
  return params

def build_code(edges, blocks, name, args):
  blk_dic = {}
  for blk in blocks:
    addr = blk.addr
    blk_dic[hex(addr)] = blocks[blk]
  edge_dic = {}
  for edge in edges:
    s, e = edge[0]
    if s.addr > e.addr:
      continue
    tp = edge[1]
    try:
      edge_dic[hex(s.addr)].append((hex(e.addr), tp))
    except:
      edge_dic[hex(s.addr)] = [(hex(e.addr), tp)]
  for node in edge_dic:
    edge_dic[node] = sorted(edge_dic[node], key=lambda x : x[0])
  addrs = sorted(blk_dic.keys())
  edge_addrs = sorted(edge_dic.keys())
  use = []
  stmts = []
  if len(edge_addrs) > 0:
    stmts = ["\t%s" % '\n\t'.join(blk_dic[edge_addrs[0]])]
    for node in edge_addrs:
      if node in use:
        continue
      children = edge_dic[node]
      flag = 0
      for idx, child in enumerate(children):
        tp = child[1]
        addr = child[0]
        if tp == 'IF':
          flag = 1
          break
        elif tp == 'WHILE':
          flag = 2
          break
        else:
          continue
      # print(flag)
      if flag == 1:
        if_body_addr = children[0][0]
        use.append(if_body_addr)
        else_body_addr = 0
        min_addr = 0
        if if_body_addr in edge_dic:
          min_addr = edge_dic[if_body_addr][0][0]
        if min_addr != 0:
          if children[1][0] < min_addr:
            else_body_addr = children[1][0]
            use.append(else_body_addr)
        if else_body_addr == 0:
          stmt = "\tif(!tmp){\n\t\t%s\n\t}" % '\n\t'.join(blk_dic[if_body_addr][:-1])
          stmts.append(stmt)
          stmts.append("\t%s" % blk_dic[if_body_addr][-1])
        else:
          stmt = "\tif(!tmp){\n\t\t%s\n\t} else {\n\t\t%s\n\t}" % ('\n\t\t'.join(blk_dic[if_body_addr]), '\n\t\t'.join(blk_dic[else_body_addr][:-1]))
          stmts.append(stmt)
          stmts.append("\t%s" % blk_dic[else_body_addr][-1])
      elif flag == 2:
        while_body_addr = children[0][0]
        use.append(while_body_addr)
        stmt = "\twhile(!tmp){\n\t\t%s\n\t}" % '\n\t\t'.join(blk_dic[while_body_addr])
        stmts.append(stmt)
      else:
        stmt = blk_dic[children[0][0]]
        stmts.append("\t%s" % '\n\t'.join(stmt))
  else:
    stmts.append("\t%s" % '\n\t'.join(blk_dic[addrs[0]])) 
  # if addrs[-1] not in edge_addrs:
  #   stmts.append("\t%s" % '\n\t'.join(blk_dic[addrs[-1]]))
  return stmts
