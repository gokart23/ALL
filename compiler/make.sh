bison -d parser.y
flex lexer.l
g++ parser.tab.c lex.yy.c -Wwrite-strings -std=c++11