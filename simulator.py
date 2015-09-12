import subprocess
import pickle
import os

class Options:
	ram_size = 65536
	prog_offset = 0

	preproc_options = [
		("INTERACTIVE_STEPPING", False),
		("PRINT_SIMULATION_SPEED", True),
		("CACHE_SIMULATION", True),
		("BRANCH_PREDICTION_SIMULATION", True)
	]

	preproc_configs = [
		("RAM_SIZE", 65536),

		("CACHE_SIZE", 4096),
		("CACHE_LINE_SIZE", 4),
		("CACHE_ASSOCIATIVITY", 4),

		("PREDICTION_TABLE_SIZE", 8),
		("NO_BRANCH_PREDICTION_HISTORY_BITS", 3)
	]

	def getPreprocessorDirectives(self):
		res = ""
		
		#print preprocessor options
		for option in self.preproc_options:
			if option[1]:
				res += "#define " + option[0] + "\n"

		res += "\n"
		#print the data
		for option in  self.preproc_configs:
			res += "#define " + option[0] + " " + str(option[1]) +"\n"
		return res

labels = {}
noLabels = 0
def declareLabel(addr):
	global labels, noLabels
	if addr not in labels:
		labels[addr] = "Label" + str(noLabels)
	noLabels += 1

class Instruction:
	'''Data contains the following:
	-- iType either 'R', 'I' or 'J'
	-- pc the PC value at this instruction
	-- rs, rd, rt and shamt (represented in assembly in that order) it iType = 'R'
	-- funct represents the MIPS code of function (if iType = 'R')
	-- imm if iType = 'R' This may either contain an integer containing an address or a string with the label. External labels start with an @
	-- addr for jump instructions (same as imm), I do not know the precise details of this yet.
	'''

	def regStr(self, regId):
		return "register_file[" + str(regId) + "]"

	def memStr(self, memLoc, value=None):
		if value == None:
			return " memory_access( " + str(memLoc) + " ) " 
		else:
			return " memory_access( " + str(memLoc) + ", " + value + " ) "

	def populateTargetLabels(self, opts):
		if self.iType == 'I':
			if self.op == 4:
				declareLabel(self.addr)
			elif self.op == 5:
				declareLabel(self.addr)
		elif self.iType == 'J':
			if self.op == 2:
				declareLabel((self.pc & 0xf00000) | ((self.addr)))

	def generateCStatement(self, opts):
		global labels
		if self.iType == 'R':
			if self.funct == 32:
				return self.regStr(self.rd) + " = " + self.regStr(self.rs) + " + " + self.regStr(self.rt) + ";\n"
			elif self.funct == 33:
				return self.regStr(self.rd) + " = " + self.regStr(self.rs) + " * " + self.regStr(self.rt) + ";\n"
			elif self.funct == 34:
				return self.regStr(self.rd) + " = " + self.regStr(self.rs) + " - " + self.regStr(self.rt) + ";\n"
			if self.funct == 35:
				return self.regStr(self.rd) + " = " + self.regStr(self.rs) + " / " + self.regStr(self.rt) + ";\n"
			elif self.funct == 36:
				return self.regStr(self.rd) + " = " + self.regStr(self.rs) + " & " + self.regStr(self.rt) + ";\n"
			elif self.funct == 37:
				return self.regStr(self.rd) + " = " + self.regStr(self.rs) + " | " + self.regStr(self.rt) + ";\n"
			elif self.funct == 39:
				return self.regStr(self.rd) + " = ~(" + self.regStr(self.rs) + " | " + self.regStr(self.rt) + ");\n"
			elif self.funct == 0:
				return self.regStr(self.rd) + " = " + self.regStr(self.rt) + " <<  " + str(self.shamt) + ";\n"
			elif self.funct == 2:
				return self.regStr(self.rd) + " = " + self.regStr(self.rt) + " >>  " + str(self.shamt) + ";\n"
		elif self.iType == 'I':
			if self.op == 35:
				return self.regStr(self.rs) + " = " + self.memStr(str(self.addr) + ' + ' + self.regStr(self.rt)) + ";\n"
			elif self.op == 43:
				return self.memStr(str(self.addr) + ' + ' + self.regStr(self.rt), self.regStr(self.rs)) + ";\n"
			elif self.op == 8:
				return self.regStr(self.rt) + " = " + self.regStr(self.rs) + " + " + str(self.addr) + ";\n"	
			elif self.op == 9:
				return self.regStr(self.rt) + " = " + self.regStr(self.rs) + " - " + str(self.addr) + ";\n"
			elif self.op == 10:
				return self.regStr(self.rt) + " = " + self.regStr(self.rs) + " * " + str(self.addr) + ";\n"
			elif self.op == 11:
				return self.regStr(self.rt) + " = " + self.regStr(self.rs) + " / " + str(self.addr) + ";\n"
			elif self.op == 12:
				return self.regStr(self.rt) + " = " + self.regStr(self.rs) + " & " + str(self.addr) + ";\n"
			elif self.op == 13:
				return self.regStr(self.rt) + " = " + self.regStr(self.rs) + " | " + str(self.addr) + ";\n"
			elif self.op == 4:
				return "if( " + self.regStr(self.rs) + " == " + self.regStr(self.rt) + ") {\n\t\tbranch_predict( " + str(self.pc) + ", " + self.regStr(self.rs) + " == " + self.regStr(self.rt) + " );\n\t\tgoto " + labels[self.addr] + ";\n\t}\n"
			elif self.op == 5:
				return "if( " + self.regStr(self.rs) + " != " + self.regStr(self.rt) + ") {\n\t\tbranch_predict( " + str(self.pc) + ", " + self.regStr(self.rs) + " != " + self.regStr(self.rt) + " );\n\t\tgoto " + labels[self.addr] + ";\n\t}\n"
			elif self.op == 44:
				if self.addr not in [0, 1, 2]:
					print "Warning: the simulated OS does not support interrupts other than 0, 1 or 2"
				if self.addr == 0: return "return;\n"
				elif self.addr == 1: return "printf(\"%d\\n\", " + self.regStr(1) + ");\n\tfflush(stdout);\n"
				elif self.addr == 2: return "scanf(\"%d\\n\", &" + self.regStr(1) + ");\n"
		elif self.iType == 'J':
			if self.op == 2:
				return "goto " + labels[self.pc & 0xf00000 | ((self.addr)<<0)] + ";\n"
			if self.op == 3:
				return "\n"

		return "//Instruction type not yet supported"

	def generateCString(self, opts):
		global labels

		print labels, self.pc, self.iType, self.op
		if self.pc in labels:
			labelPrefix = labels[self.pc] + ": "
		else:
			labelPrefix = ""

		functionCallSuffix = "\tinteractive_stepping();\n"

		return labelPrefix + self.generateCStatement(opts) + functionCallSuffix

def generateCProgram(opts, instrs, templateFileName='template.c'):
	templateFile = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), templateFileName), 'r')
	res = templateFile.read()
	templateFile.close()

	for instr in instrs: instr.populateTargetLabels(opts)

	res = res.replace('%preproc_defs', opts.getPreprocessorDirectives())

	res = res.replace('%exec', ''.join(['\t' + instr.generateCString(opts) for instr in instrs]))

	return res

if __name__ == '__main__':
	opts = Options()
	fname = raw_input()
	f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), fname), "rb")
	tm = f.read()
	dg = pickle.loads(tm[tm.find("#####")+5:])
	instrs = dg['instructions']	
	templateFile = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tempC.c'), 'w')
	templateFile.write(generateCProgram(opts, instrs))
	templateFile.close()
	subprocess.call(['g++', 'tempC.c', '-std=c++11', '-O3'])
	subprocess.call(['./a.exe'])