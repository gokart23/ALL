/*** Token Definitions - verbatim C Code ***/
%{
	//for the tokens
	#include "parser.tab.h"
	#include <string>
	#include <cstdlib>

	/*
+ {return PLUS;}
- {return MINUS;}
* {return MUL;}
/ {return DIV;}*/
%}

%option noyywrap

%%

[ \t\n]
"if" { return KWD_IF; }
"while" { return KWD_WHILE; }
"int" { return KWD_INT; }
"return" { return KWD_RETURN; }
[a-zA-Z_][a-zA-Z_0-9]* { yylval.sval = strdup(yytext); return LABEL; }
[0-9]+ { yylval.ival = atoi(yytext); return INTEGER; }

[\(\)\{\}\[\];=+-/*]    { /* printf ("token: %c\n", yytext[0]); */ return yytext[0]; }

%%