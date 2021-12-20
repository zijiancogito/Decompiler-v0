

# def translate(func, data, ckpt, user, problem, hparams, model_name, tfe):
def translate(func, m, ckpt, encoders, tfe):
  outs = []
  import my_model
  for gadget in func:
    gadget = " ; ".join(gadget)
    if not gadget.endswith(';'):
      gadget = f"{gadget} ;"
    # output = my_model.model_exe(data_dir=data,
    #                          ckpt_dir=ckpt,
    #                          user_dir=user,
    #                          problem_name=problem,
    #                          hparams_name=hparams,
    #                          model_name=model_name, 
    #                          input_str=gadget,
    #                          tfe=tfe,
    #                          flag=2)
    output = my_model.model_exe(model=m,
                                ckpt_path=ckpt,
                                encoders=encoders,
                                input_str=gadget,
                                tfe=tfe,
                                flag=2)
    outs.append(output)
  return outs

def grammer_check(src, func):
  import re
  g1 = re.compile("v[0-9]+ = v[0-9]+ [\S]+ v[0-9]+ ;")
  g2 = re.compile("v[0-9]+ [\S]*= v[0-9]+ ;")
  g3 = re.compile("v[0-9]+ = [\S] v[0-9]+ ;")
  g4 = re.compile("uint32_t v[0-9]+ = imm ;")
  # g5 = re.compile("v[0-9]+ = v[0-9]+ [\S]+ v[0-9]+ \? v[0-9]+ : v[0-9]+ ;")
  g5 = re.compile("uint32_t \* v[0-9]+ = imm ;")
  g6 = re.compile("\* v[0-9]+ = \* v[0-9]+ [\S]+ \* v[0-9]+ ;")
  g7 = re.compile("\* v[0-9]+ [\S]*= \* v[0-9]+ ;")
  g8 = re.compile("\* v[0-9]+ = [\S]+ v[0-9]+ ;")
  g9 = re.compile("v[0-9]+ = \& v[0-9]+ ;")
  g10 = re.compile("\* v[0-9]+ = v[0-9]+ [\S] v[0-9]+ ;")
  g11 = re.compile("v[0-9]+ = v[0-9]+ [\S]+ imm ;")
  g12 = re.compile("v[0-9]+ [\S]*= imm ;")
  g13 = re.compile("v[0-9]+ = func[0-9]* \([\S\s]+\) ;")
  for i in range(1, 14):
    grammer_name = f"g{i}"
    if eval(grammer_name).fullmatch(src):
      return True, None
  r = {"add": "+", "sub": "-", "mul": "*", "xor": "^", "or": "|", "and": "&"}
  right_src = ""
  mov_flag = 0
  for ins in func:
    if ins.startswith('mov'):
      continue
    else:
      mov_flag = 1
      break
  if mov_flag == 0 and len(func) > 1:
    return False, "v1 = v2 ;"
  elif mov_flag == 0 and len(func) == 1:
    if re.fullmatch('[0-9a-e]{1,20}', func[0].split(' ')[-1]):
      return False, "uint32_t v1 = imm ;"
    else:
      return False, "v1 = v2 ;"
  else:
    pass
  for ins in func:
    op = ins.split(' ')[0]
    if op in r:
      right_src = f"v1 = v2 {r[op]} v3 ;"
      return right_src
    elif 'call' in op and (not g13.fullmatch(src)):
      right_src = f"v1 = func ( ) ;"
      return right_src
    else:
      continue
  return False, src

def meaning_check(src, func):
  import re
  mov_flag = 0
  for ins in func:
    if ins.startswith('mov'):
      continue
    else:
      mov_flag = 1
      break
  if mov_flag == 0 and len(func) == 1:
    if re.fullmatch('[0-9a-e]{1,20}', func[0].split(' ')[-1]):
      return False, "uint32_t v1 = imm ;"
    else:
      return False, "v1 = v2 ;"
  elif mov_flag == 0 and len(func) > 1:
    return False, "v1 = v2 ;"
  else:
    pass
  regx = re.compile("(rdi|rsi|rdx|rcx|r8d|r9d|edi|esi|edx|ecx)")
  params = dict()
  for ins in func:
    opc = ins.split(' ')[0]
    if opc.startswith('call'):
      ps = 0
      for res in params:
        if params[res] % 2 == 1:
          ps += 1
      pl = [f"v{i}" for i in range(2, ps+2)]
      return False, f"v1 = func ( {' , '.join(pl)} ) ;"
    else:
      match = regx.findall(ins)
      if match:
        for res in match:
          if res in params:
            params[res] += 1
          else:
            params[res] = 1
  import tools
  # if tools.is_special_div(func):
  #   if '/' in src or "%" in src:
  #     return True, None
  #   else:
  #     return False, f"v1 = v2 / v3 ;"
  m = {"+": "add", "-": "sub", "*": "mul",
      "<<": "shl", ">>": "shr", "^": "xor", "|": "or", "&": "and", "/": "div"}
  r = {"add": "+", "sub": "-", "mul": "*",
      "shl": "<<", "shr": ">>", "xor": "^", "or": "|", "and": "&", "div": '/'}
  # print(src)
  # import pdb
  # pdb.set_trace()
  pattern = re.compile("v[0-9]* = v[0-9]* ([^\(\)\[\]\s]+) [vimm0-9]+ ;")
  opc = pattern.findall(src)
  if len(opc) > 0:
    opc = opc[0]
    if opc in m:
      op = m[opc]
      for ins in func:
        if op in ins:
          return True, None
      for ins in func:
        ins_op = ins.split(' ')[0]
        if ins_op in r:
          real_op = r[ins_op]
          c = re.sub(f" {opc} ", f" {real_op} ", src, 1)
          return False, c
    else:
      for ins in func:
        ins_op = ins.split(' ')[0]
        if ins_op in r:
          real_op = r[ins_op]
          c = re.sub(f" {opc} ", f" {real_op} ", src, 1)
          return False, c
  else:
    if '*' in src:
      if len(func) > 2:
        return True, None
      else:
        src = re.sub('\*', '', src, 10)
        src = re.sub('[\s]+', ' ', src, 10)
        return False, src
  return False, src

def compare_check(func: list):
  jmp = {"jz": '==',"jnz": '!=', "jc": '==', "jnc": '!=', "jo": '==', "jno": '!=',
         "js": '==', "jns": '!=', "jp": '==', "jnp": '!=', "je": '==', "jne": '!=',
         "jcxz": '==', "jecxz": '==', "jrcxz": '==', "ja": '>', 'jnbe': '>', 'jae': '>=', 'jnb': '>=', 'jb': '<', 'jnae': '<', 'jbe':'<=', 'jna':'<=', 'jg':'>', 'jnle':'>', 'jge':'>=', 'jnl':'>=','jl':'<','jnge':'<','jle':'<=', 'jng':'<='}
  ins = func[-1].strip().split(' ')[0]
  # print(func)
  if ins in jmp:
    right_src = f"v1 = v2 {jmp[ins]} v3 ;"
    # print(right_src)
    return True, right_src
  return False, None

def trans_correction(func: list, src: list):
  right_pair = []
  for asm, c in zip(func, src):
    is_cmp, right_src = compare_check(asm)
    if is_cmp:
      right_pair.append((asm, right_src))
    else:
      is_grammer, right_src = grammer_check(c, asm)
      if is_grammer:
        is_meaning, tmp = meaning_check(c, asm)
        if is_meaning:
          right_pair.append((asm, c))
        else:
          if tmp is not None:
            right_pair.append((asm, tmp))
          else:
            right_pair.append((asm, c))
      else:
        right_pair.append((asm, right_src))
    # print(asm)
    # print(right_pair[-1])
    # print()
  return right_pair