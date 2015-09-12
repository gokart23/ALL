@main:
andi $1,$1,0
addi $1,$1,10
andi $3,$3,0
addi $3,$3,1
j @func1

@func3:
muli $1,$1,10
andi $6,$6,0
addi $6,$6,1
intr 0