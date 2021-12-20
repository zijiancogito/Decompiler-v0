import sys

def opseq_extract(func: list) -> list :
  ops = []
  for ins in func:
    opc = ins.split(' ')[0]
    ops.append(opc)
  return ops

def is_special_div(func: list) -> bool :
  div1 = ['shr', 'shl']
  div2 = ['mul','sub', 'add', 'imul']
  ops = opseq_extract(func)
  flag0 = 0
  flag1 = 0
  for op in ops:
    if op in div1:
      flag0 += 1
    if op in div2:
      flag1 += 1

  if flag0+flag1 > 4 :
    return True
  else:
    return False

def form_asm(func: str) -> list:
  sys.path.append('..')
  from utils.Parser import Rules
  func = Rules('asm', func).pcode.strip()
  return func.split('\n')

def asm_transition(gadget):
  import re
  offset_pattern = re.compile('\[[er]*bp [\-\+] [0]*[x]*[0-9a-f]+\]')
  matches = offset_pattern.findall(gadget)
  for match in matches:
    regx = match[1:-1].split(' ')[0]
    offset = int(match[1:-1].split(' ')[-1], 16)
    flag = match[1:-1].split(' ')[1]
    gadget = gadget.replace(match, f'{flag}{offset}[{regx}]', 1)
  hex_pattern = re.compile("0x[0-9a-f]+")
  matches = hex_pattern.findall(gadget)
  for match in matches:
    gadget = gadget.replace(match, str(int(match,16)), 1)
  return gadget

# def is_cmp(asm):
