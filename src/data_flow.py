def form_ins(ins):
  ops = []
  import re
  ops.append(ins.split(' ')[0])
  opc = ' '.join(ins.split(' ')[1:])
  for op in opc.split(','):
    ops.append(op.strip())
  return ops

def build_var_dict(func: list):
  import re
  var_list = []
  pattern = re.compile('[\S\s]{0,20}- [0-9]{1,10} \[ [e,r]{0,1}bp \]')
  import tools
  blk = tools.asm_transition('\n'.join(func)).split('\n')
  for ins in blk:
    from utils.Parser import Rules
    ins = re.sub('[\s]+', ' ', ins, 20)
    ops = form_ins(Rules('asm', ins).pcode.strip())
    for op in ops:
      if pattern.match(op):
        var_list.append(op.strip())
  var_list = list(set(var_list))
  var_dict = {}
  for index, var in enumerate(var_list):
    var_dict[var] = f"v{index}"
  return var_dict

# f1 = r'uint32_t[\s]v[0-9]{1,10} = [0-9]{1,20} ;'
# f2 = r'v[0-9]{1,10} = [\S]{0,2} v[0-9]{1,20} ;'
# f3 = r'v[0-9]{1,10} = v[0-9]{1,20} ;'
# f4 = r'v[0-9]{1,10} = v[0-9]{1,20} [\S]{1,2} v[0-9]{1,20} ;'
# f5 = r'v[0-9]{1,10} = v[0-9]{1,20} [\S]{1,2} v[0-9]{1,20} \? v[0-9]{1,20} \: v[0-9]{1,20} ;'
# f6 = r'v[0-9]{1,10} = func[0-9]{1,10} \([\s\S]{1,50}\) ;'
# f7 = r'v'

f1 = r"uint32_t v[0-9]+ = imm ;"
f2 = r"v[0-9]+ = v[0-9]+ [\S]+ v[0-9]+ ;"
f3 = r"v[0-9]+ [\S]*= v[0-9]+ ;"
f4 = r"v[0-9]+ = [\S] v[0-9]+ ;"

# f5 = r"v[0-9]+ = v[0-9]+ : v[0-9] \? ;"

f6 = r"uint32_t \* v[0-9]+ = imm ;"
f7 = r"\* v[0-9]+ = \* v[0-9]+ [\S]* \* v[0-9]+ ;"
f8 = r"\* v[0-9]+ [\S]*= \* v[0-9]+ ;"
f9 = r"\* v[0-9]+ = [\S]+ v[0-9]+ ;"
f10 = r"v[0-9]+ = \& v[0-9]+ ;"
f11 = r"\* v[0-9]+ = v[0-9]+ [\S] v[0-9]+ ;"

f12 = r"v[0-9]+ = v[0-9]+ [\S]+ imm ;"
f13 = r"v[0-9]+ [\S]*= imm ;"

f14 = r"v[0-9]+ = func[0-9]* \([\S\s]+\) ;"

def form_ins_dot(ins):
  ops = []
  ops.append(ins.split(' ')[0])
  opc = ' '.join(ins.split(' ')[1:])
  for op in opc.split(',')[:-1]:
    ops.append(f"{op.strip()} ,")
  ops.append(opc.split(',')[-1].strip())
  return ops

def rec_data_flow(maps: list):
  src_pairs = {}
  funcs = []
  for id, s, pairs in maps:
    funcs += s.split('\n')
    src_pairs[id] = pairs
  var_dict = build_var_dict(funcs)
  import re
  src_mem_pattern = re.compile('[\S\s]{0,20}\- [0-9]{1,10} \[ [e,r]{0,1}bp \]')
  dst_mem_pattern = re.compile('[\S\s]{0,20}\- [0-9]{1,10} \[ [er]{0,1}bp \] [\,]{1}')
  imm_pattern = re.compile('[0-9a-e]{0,20}')
  var_mem_pattern = re.compile('v[0-9]{1,10}')
  mov_pattern = re.compile('mov[\S]*')
  call_pattern = re.compile('func[0-9]{1,10}')
  new_src = {}
  for id in src_pairs:
    pairs = src_pairs[id]
    tmp_src = []
    for asm, c in pairs:
      ins_feature = {"LD": [], "R": [], "LO": [], "IMM": [], "F": []}
      for ins in asm:
        ops = form_ins_dot(ins)
        for op in ops:
          if src_mem_pattern.fullmatch(op):
            ins_feature["R"].append((re.sub(',', '', op, 1).strip(), ops[0]))
          elif dst_mem_pattern.fullmatch(op) and mov_pattern.fullmatch(ops[0]):
            ins_feature["LD"].append((re.sub(',', '', op, 1).strip(), ops[0]))
          elif dst_mem_pattern.fullmatch(op) and not mov_pattern.fullmatch(ops[0]):
            ins_feature["LO"].append((re.sub(',', '', op, 1).strip(), ops[0]))
            ins_feature["LD"].append((re.sub(',', '', op, 1).strip(), ops[0]))
          elif imm_pattern.fullmatch(op):
            ins_feature["IMM"].append((op, ops[0]))
          elif call_pattern.fullmatch(op):
            ins_feature["F"].append((op, ops[1]))
          else:
            continue
      src_items = c.split(' ')
      if re.match(f1, c) or re.match(f6, c):  # r"uint32_t v[0-9]* = [0-9]* ;" r"uint32_t * v[0-9]+ = [0-9]+ ;"
        try:
          imm = ins_feature["IMM"][0][0]
          src_items[-2] = imm
        except:
          src_items[-2] = "NULL"
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[-4] = var_dict[offset0]
        except:
          src_items[-4] = 'tmp'
      elif re.match(f2, c):       # r"v[0-9]* = v[0-9]* [\S]* v[0-9]* ;"
        try:
          offset1 = ins_feature["R"][0][0]
          src_items[-2] = var_dict[offset1]
        except:
          src_items[-2] = 'tmp'
        try:
          offset2 = ins_feature["R"][1][0]
          src_items[-4] = var_dict[offset2]
        except:
          try:
            offset2 = ins_feature["LO"][0][0]
            src_items[-4] = var_dict[offset2]
          except:
            src_items[-4] = 'tmp'
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[0] = var_dict[offset0]
        except:
          src_items[0] = 'tmp'
      elif re.match(f3, c) or re.match(f4, c) or re.match(f10, c): #r"v[0-9]+ [\S]*= v[0-9]+ ;" 
        try:                                       #r"v[0-9]+ = \& v[0-9]+ ;"
          offset1 = ins_feature["R"][0][0]          #r"v[0-9]+ = [\S] v[0-9]+ ;"
          src_items[-2] = var_dict[offset1]
        except:
          src_items[-2] = 'tmp'
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[0] = var_dict[offset0]
        except:
          src_items[0] = 'tmp'
      elif re.match(f7, c):  #r"\* v[0-9]+ = \* v[0-9]+ [\S]* \* v[0-9]+ ;"
        try:
          offset1 = ins_feature["R"][0][0]
          src_items[-2] = var_dict[offset1]
        except:
          src_items[-2] = 'tmp'
        try:
          offset2 = ins_feature["R"][1][0]
          src_items[-5] = var_dict[offset2]
        except:
          try:
            offset2 = ins_feature["LO"][0][0]
            src_items[-5] = var_dict[offset2]
          except:
            src_items[-5] = 'tmp'
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[1] = var_dict[offset0]
        except:
          src_items[1] = 'tmp'
      elif re.match(f8, c) or re.match(f9, c): #r"\* v[0-9]+ [\S]*= \* v[0-9]+ ;" r"\* v[0-9]+ = [\S]+ v[0-9]+ ;"
        try:
          offset1 = ins_feature["R"][0][0]
          src_items[-2] = var_dict[offset1]
        except:
          src_items[-2] = 'tmp'
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[1] = var_dict[offset0]
        except:
          src_items[1] = 'tmp'
      elif re.match(f11, c):  #r"\* v[0-9]+ = v[0-9]+ [\S] v[0-9]+ ;"
        try:
          offset1 = ins_feature["R"][0][0]
          src_items[-2] = var_dict[offset1]
        except:
          src_items[-2] = 'tmp'
        try:
          offset2 = ins_feature["R"][1][0]
          src_items[-4] = var_dict[offset2]
        except:
          try:
            offset2 = ins_feature["LO"][0][0]
            src_items[-4] = var_dict[offset2]
          except:
            src_items[-4] = 'tmp'
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[1] = var_dict[offset0]
        except:
          src_items[1] = 'tmp'
      elif re.match(f12, c):  #r"v[0-9]+ = v[0-9]+ [\S]+ [0-9]+ ;"
        try:
          imm = ins_feature["IMM"][0][0]
          src_items[-2] = imm
        except:
          src_items[-2] = "NULL"
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[0] = var_dict[offset0]
        except:
          src_items[0] = 'tmp'
        try:
          offset1 = ins_feature["R"][0][0]
          src_items[-4] = var_dict[offset1]
        except:
          try:
            offset1 = ins_feature["LO"][0][0]
            src_items[-4] = var_dict[offset1]
          except:
            src_items[-4] = 'tmp'
      elif re.match(f13, c):  #r"v[0-9]+ [\S]*= [0-9]+ ;"
        try:
          imm = ins_feature["IMM"][0][0]
          src_items[-2] = imm
        except:
          src_items[-2] = "NULL"
        try:
          offset0 = ins_feature["LD"][0][0]
          src_items[0] = var_dict[offset0]
        except:
          src_items[0] = 'tmp'
      elif re.match(f14, c):  # r"v[0-9]+ = func[0-9]+\([\S\s]+\) ;"
        try:
          para_list = []
          for item in ins_feature["R"]:
            para_list.append(var_dict[item[0]])
          if ins_feature["LD"] == []:
            var_l = 'tmp'
          else:
            var_l = var_dict[ins_feature["LD"][0][0]]
          for imm in ins_feature["IMM"]:
            para_list.append(imm[0])
          f = ins_feature["F"][0][1]
          src_tmp = f"{var_l} = {f} ( {' , '.join(para_list)} ) ;"
          src_items = src_tmp.split(' ')
        except:
          if ins_feature["LD"] == []:
            var_l = 'tmp'
          else:
            var_l = var_dict[ins_feature["LD"][0][0]]
          src_items = f"{var_l} = func ( ) ;".split(' ')
      else:
        print("Translate ERROR")
        src_items = [""]
      tmp_src.append(' '.join(src_items))
    new_src[id] = tmp_src
  return new_src

