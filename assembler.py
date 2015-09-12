import pickle
import re
import os
from numpy import binary_repr

#Global Items that are required: mnemonic opcodes and info table (OPTABLE), symbol table(SYMTAB)

#Keep OPTAB constant -> never change!
OPTAB = {
    'j':2,
    'ld':35,
    'st':43,
    'add':(0, 32),
    'sub':(0, 34),
    'mul':(0, 33),
    'div':(0,35),
    'and':(0, 36),
    'or':(0, 37),
    'nor':(0,39),
    'andi':12,
    'ori':13,
    'sll':(0,0),
    'srl':(0,2),
    'be':4,
    'bne':5,
    'slt':(0,42), 
    #these were added later
    'addi':8,
    'subi':9,
    'muli':10,
    'divi':11,
    'jr':(0, 8),
    'jal':3,
    'intr':44,       
    }
SYMTAB = {}

class AssemblerError(Exception):    
    def __init__(self, msg):
        self.msg = msg

class Instruction:
    iType ='' # can be R/I/J
    pc,op,rs,rt,rd,shamt,funct,addr = '','','','','','','',''
    
    def toMachine(self):
        if self.iType == 'R':
            mach_instr = binary_repr(num=self.op, width=6) + binary_repr(self.rs, 5) + binary_repr(self.rt, 5) + binary_repr(self.rd, 5) + binary_repr(self.shamt, 5) + binary_repr(self.funct, 6)
            return mach_instr
        elif self.iType == 'I':
            mach_instr = binary_repr(num=self.op, width=6) + binary_repr(self.rs, 5) + binary_repr(self.rt, 5) + binary_repr(self.addr, 16)            
            return mach_instr            
        else:
            if str(self.addr).isdigit() is False:
                return "incomplete instruction(missing label replaces maybe?)"
            mach_instr = binary_repr(num=self.op, width=6) + binary_repr(self.addr, 26)
            return mach_instr            
           
    def __init__(self, code, code_type):
        if code_type == 'm':
            pass
        elif code_type == 'a':
            print code
            instr = re.split(' |,', code)
            instr = [ n for n in instr if n != '' ]
            print instr,len(instr)
            if len(instr) == 2:
                if instr[0] == 'intr':
                    self.iType,self.rs,self.rt,self.op,self.addr = 'I',0,0,OPTAB[instr[0]],int(instr[1])
                elif (instr[0] == 'j' or instr[0] == 'jal'):
                    self.iType,self.op,self.addr = 'J',OPTAB[instr[0]],instr[1]
                elif len(instr) == 2 and instr[0] == 'jr':
                    self.iType, self.op, self.funct, self.rs, self.shamt, self.rt, self.rd = 'R', OPTAB[instr[0]][0], OPTAB[instr[0]][1],int(instr[1][1:]), 0, 0, 0   
                #print "jump",self.iType,self.op,self.addr            
            elif len(instr) == 3 and (instr[0] == 'ld' or instr[0] == 'st'):
                tmp = re.split('[(|)]', instr[2])
                self.iType,self.op,self.rs,self.rt,self.addr = 'I', OPTAB[instr[0]],int(instr[1][1:]),int(tmp[1][1:]),int(tmp[0])
                #print self.iType,self.op,self.rs,self.rt,self.addr
            elif len(instr) == 4:
                if isinstance(OPTAB[instr[0]], tuple) is True:
                    if OPTAB[instr[0]][1] >= 3:
                        self.iType,self.op,self.rs,self.rt,self.rd,self.shamt,self.funct = 'R',OPTAB[instr[0]][0],int(instr[2][1:]), int(instr[3][1:]), int(instr[1][1:]),0,OPTAB[instr[0]][1]
                        #print self.iType,self.op,self.rs,self.rt,self.rd,self.shamt,self.funct
                    else:
                        self.iType,self.op,self.rs,self.rt,self.rd,self.shamt,self.funct = 'R',OPTAB[instr[0]][0],0,int(instr[2][1:]), int(instr[1][1:]),int(instr[3][1:]),OPTAB[instr[0]][1]
                        #print self.iType,self.op,self.rs,self.rt,self.rd,self.shamt,self.funct
                else:
                    self.iType,self.op,self.rs,self.rt,self.addr = 'I',OPTAB[instr[0]],int(instr[2][1:]),int(instr[1][1:]), int(instr[3]) if (OPTAB[instr[0]] != 4 and OPTAB[instr[0]] != 5) else instr[3]
                    print self.iType,self.op,self.rs,self.rt,self.addr
            else:
                raise AssemblerError(msg="Cannot decode instruction...incorrect instruction format received")
        else:
            raise AssemblerError(msg="Cannot decode instruction...incorrect parsing parameter")            

if __name__ == "__main__":
    fname = raw_input()
    file_input = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), fname), "r")
    program = file_input.read().split('\n')
    instructions = []    
    loc_ctr = 0
    while loc_ctr < len(program):
        t = re.split(' |,', program[loc_ctr])
        t = [n for n in t if n != '']
        if len(t) == 1: # Identify label        
            print "FOUND LABEL",re.split(':',program[loc_ctr])[0],"at",loc_ctr
            SYMTAB[re.split(':',program[loc_ctr])[0]] = len(instructions)        
        elif len(t) == 0:
            loc_ctr += 1
            continue
        else:
            t = Instruction(program[loc_ctr], 'a')
            instructions.append(t)
        loc_ctr += 1    
    for num in range(len(instructions)):
        instructions[num].pc = (4*num)
        if instructions[num].iType == 'J':
            if instructions[num].addr in SYMTAB:
                print "setting",instructions[num].addr,"to ",4*SYMTAB[instructions[num].addr]
                instructions[num].addr = 4*SYMTAB[instructions[num].addr] # zero-based indexing of instruction addresses!       
            else:
                instructions[num].addr = "$" + instructions[num].addr
                print instructions[num].addr
        if instructions[num].iType == 'I' and (instructions[num].op == 4 or instructions[num].op == 5):
            print "setting",instructions[num].addr,"to ",4*(SYMTAB[instructions[num].addr])
            instructions[num].addr = 4*(SYMTAB[instructions[num].addr])
        print instructions[num].pc,":",(instructions[num].toMachine())
    funcs = [ name for name in SYMTAB.keys() if name[0] == '@']
    FUNCS = {}
    for f in funcs:
        FUNCS[f] = 4*SYMTAB[f]
    pickle.dump({"funcs":FUNCS, "instructions":instructions}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), fname[0:fname.find('.')] + ".obj"), "wb"))    
    print FUNCS