@main:
Init:
j @input
Mean:
j @mean
StdDev:
andi $7,$7,0
addi $7,$1,0
j @stddev
Output:
intr 0

@input:
intr 2
andi $5,$5,0
andi $3,$3,0
addi $5,$1,0
andi $4,$4,0
addi $4,$29,0
InputLoop:
intr 2
sub $4,$4,$3
st $1,0($4)
addi $3,$3,1
be $3,$5,Mean
j InputLoop

@mean:
andi $3,$3,0
andi $4,$4,0
addi $4,$29,0
andi $1,$1,0
SumLoop:
sub $4,$4,$3
ld $6,0($4)
add $1,$1,$6
addi $3,$3,1
be $3,$5,L1
j SumLoop
L1:
div $1,$1,$5
j StdDev

@stddev:
andi $3,$3,0
andi $4,$4,0
addi $4,$29,0
andi $1,$1,0
DevLoop:
sub $4,$4,$3
ld $6,0($4)
sub $6,$6,$7
mul $6,$6,$6
add $1,$1,$6
addi $3,$3,1
be $3,$5,Output
j DevLoop