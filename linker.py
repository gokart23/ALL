import pickle
import re
import os
from array import *
from numpy import binary_repr 

#Keep OPTAB constant -> never change!
OPTAB = {
    'j':2,
    'ld':35,
    'st':43,
    'add':(0, 32),
    'sub':(0, 34),
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
    #no instr for'subi':,           
    }

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
            #print instr
            if len(instr) == 2 and (instr[0] == 'j' or instr[0] == 'jal'):
                self.iType,self.op,self.addr = 'J',OPTAB[instr[0]],instr[1]
                #print "jump",self.iType,self.op,self.addr
            elif len(instr) == 2 and instr[0] == 'jr':
                self.iType, self.op, self.funct, self.rs, self.shamt, self.rt, self.rd = 'R', OPTAB[instr[0]][0], OPTAB[instr[0]][1],int(instr[1][1:]), 0, 0, 0   
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
                    self.iType,self.op,self.rs,self.rt,self.addr = 'I',OPTAB[instr[0]],int(instr[2][1:]),int(instr[1][1:]), int(instr[3])
                    print self.iType,self.op,self.rs,self.rt,self.addr
            else:
                raise AssemblerError(msg="Cannot decode instruction...incorrect instruction format received")
        else:
            raise AssemblerError(msg="Cannot decode instruction...incorrect parsing parameter")            


if __name__ == "__main__":
    input_fn = raw_input().split(" ")
    #input_fn = ["B:\Acad\Course Material\Semester 4\SysEng Lab\sample.obj", "B:\Acad\Course Material\Semester 4\SysEng Lab\sample2.obj"]
    print "Please enter offset value:"
    offset = input()
    loc_offset = offset
    files = []
    funcs = {}
    instructions = []
    for f in input_fn:
        code = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f), "rb"))
        loc_instructions,loc_funcs = code['instructions'], code['funcs']
        print f,"FUNCS",loc_funcs
        for fn in loc_funcs.keys():
            funcs[fn] = loc_funcs[fn] + loc_offset
        tmp = loc_offset
        for instr in loc_instructions: # j jal
            instr.pc += loc_offset
            if (instr.iType == 'J' and str(instr.addr)[0] != '$') or (instr.iType == 'I' and (instr.op == 4 or instr.op == 5)):
                instr.addr += loc_offset
            tmp = max(instr.pc, tmp)        
        print "Finished linking " + f
        instructions = instructions + loc_instructions        
        loc_offset = tmp+4
    print funcs
    
    for instr in instructions:
        if (instr.iType == 'J' and str(instr.addr)[0] == '$'):
            print "setting",instr.addr,"to ",funcs[instr.addr[1:]]
            instr.addr = funcs[instr.addr[1:]]
    print "\n\n\n"
    bin_array = array('B')
    op = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"d.bin"), "wb")
    for instr in instructions:
        t = instr.toMachine()
        bin_array.append(int(t[0:8], 2))
        bin_array.append(int(t[8:16], 2))
        bin_array.append(int(t[16:24], 2))
        bin_array.append(int(t[24:32], 2))
        print instr.pc,":",(instr.toMachine())
    bin_array.tofile(op)
    op.write("#####")
    p = pickle.dumps({'instructions':instructions})#, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"a.cpl"), "wb"))    
    op.write(p)
    op.close()
    print "Successfully output file a.cpl"    