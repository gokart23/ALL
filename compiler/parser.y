/* Simple C-subset compiler  */

%{
	#include <math.h>
	#include <stdio.h>

	#include <string.h>
	#include <cstdlib>
	#include <unordered_map>
	#include <utility>

	int yylex (void);
	void yyerror (char const *);

	//for easy string manipulation
	char* createString( char *src, bool freeStr = true ){
		int len = strlen(src) + 1;
		char *dst = (char*)malloc(len*sizeof(char));
		strcpy(dst, src);
		if ( freeStr )
			free(src);
		return dst;
	}

	char* createString(const char *src){
		int len = strlen(src) + 1;
		char *dst = (char*)malloc(len*sizeof(char));
		strcpy(dst, src);
		return dst;
	}


	char* createString(int src){
		char *dst = (char*)malloc(16*sizeof(char));
		sprintf(dst, "%d", src);
		return dst;
	}

	char* createString(char* src1, char* src2){
		int len = strlen(src1) + strlen(src2) + 1;
		char *dst = (char*)malloc(len*sizeof(char));
		sprintf(dst, "%s%s", src1, src2);
		free(src1); free(src2);
		return dst;
	}

	//symbol table
	std::unordered_map<std::string, int> symbolTable; //int stores offset of variable from frame pointer
	int stackPos = 0; //used to track offset of a variable
	void declSymbol(const char* varName, int size){
		symbolTable.insert (std::make_pair<std::string, int>(varName, -stackPos*4));
		stackPos += size;
	}

	int getSymbolOffset(const char* varName){
		if( symbolTable.count(varName) == 0 ){
			printf("Error: Undeclared variable name '%s'\n", varName);
			exit(1);
		}
		return symbolTable[varName];
	}

	void clearSymbolTable(){
		symbolTable.clear();
	}

	//function names
	std::unordered_map<std::string, int> functionNames;
	void declFunction(const char* funcName){
		functionNames.insert (std::make_pair<std::string, int>(funcName, 0)); //the integer should be storing the number of arguments
	}

	void verifyFunction(const char* funcName){
		if( symbolTable.count(funcName) == 0 ){
			printf("Error: Undeclared function '%s'\n", funcName);
			exit(1);
		}
	}

	//label manager
	int noLabels = 0;
	char* getNewLabel(){
		++noLabels;
		return createString(createString("Label"), createString(noLabels));
	}

	//Some Assembly Code Generating Prmitives
	char strBuffer[2048];
	char* binOpVars(char* str1, char* str2){
		/***Given two strings that bring value into register $1, it returns a string that brings first operand to $1 and the other to $2***/
		sprintf(strBuffer, "%ssubi $29, $29, 4 \nst $1, 4($29) \n%sld $2, 4($29) \naddi $29, $29, 4 \n", str1, str2);
		return createString(strBuffer, false);
	}

	char *generatedAssembly = (char*)calloc(1, sizeof(char));

	bool func_decl_detector = false; //used to detect when a function begins in func_decl_arglist and func_decl non-terminals so that symbol table can be cleared
/*stmt { printf ("Returned assembly: %s\n", $1); }*/
%}

%union {
	int ival;
	float fval;
	char* sval;
}

%token <sval> LABEL
%token <ival> INTEGER
%token <ival> KWD_INT KWD_WHILE KWD_IF KWD_RETURN

%type <sval> expr stmt_list stmt decl_stmt decl_list var_decl if_stmt while_stmt func_decl func_decl_arglist func_decl_arglist_arg func_call_arglist func_call_arglist_arg return_stmt

%left '='
%left '+' '-'
%left '*' '/'

%%

program:
	%empty 
	| program func_decl { /* printf ("Returned assembly: %s\n", $2); */ generatedAssembly = createString(generatedAssembly, $2); }
	  ;

stmt_list:
	  stmt
	| stmt_list stmt { $$ = createString($1, $2); }
	  ;

stmt:
	  ';' { $$ = createString(""); }
	| expr ';' { $$ = $1; }
	| decl_stmt ';' { $$ = $1; }
	| if_stmt { $$ = $1; }
	| while_stmt { $$ = $1; }
	| return_stmt ';' {$$ = $1; }
	| '{' stmt_list '}' { $$ = $2; }
	  ;

expr:
	  expr '+' expr 	{ $$ = createString(binOpVars($1, $3), createString("addi $1, $1, $2\n")); }

	| expr '-' expr		{ $$ = createString(binOpVars($1, $3), createString("subi $1, $2, $1\n")); }

	| expr '*' expr		{ $$ = createString(binOpVars($1, $3), createString("muli $1, $1, $2\n")); }

	| expr '/' expr		{ $$ = createString(binOpVars($1, $3), createString("divi $1, $2, $1\n")); }

	| '(' expr ')'		{ $$ = $2; }

	| LABEL '=' expr	{ $$ = createString(createString( $3 ), createString(createString(createString("st $1, "), createString(getSymbolOffset($1))), createString("($30)\n")));}

	| INTEGER 			{ /* andi $1, $1, 0 \nori $1, $1, const*/ $$ = createString(createString(createString("andi $1, $1, 0 \nori $1, $1, "), createString($1)), createString("\n")); }

	| LABEL 			{ /* ld $1, offset($30) */ $$ = createString(createString(createString("ld $1, "), createString(getSymbolOffset($1))), createString("($30)\n")); }

	| LABEL '[' expr ']' { 
		char *ld = createString(createString(createString("ld $1, "), createString(getSymbolOffset($1))), createString("($30)\n"));
		//Warning - do not nest array references as the $3 will get overwritten
		sprintf(strBuffer, "%smuli $3, $1, 4 \nsub $30, $30, $3 \n%saddi $30, $30, $3 \n", $3, ld);
	  	$$ = createString(strBuffer, false); 
	}

	| LABEL '(' func_call_arglist ')' {
		//Warning: I am not checking whether the number of arguments match
		sprintf(strBuffer, "jal @%s \n", $1);
	  	$$ = createString(strBuffer, false); 
	}


	  ;

func_decl:
	  KWD_INT LABEL '(' func_decl_arglist ')' stmt { 
		  	sprintf( strBuffer, "\n@%s:\nsubi $29, $29, 4 \nst $30, 4($29) \nori $30, $29, 0 \nsubi $29, $29, 4 \nst $31, 4($29) \n%s%s\n", $2, $4, $6 );
			$$ = createString(strBuffer, false);
			func_decl_detector = false;
	  }

func_decl_arglist:
	  %empty										{ $$ = createString(""); }
	| func_decl_arglist_arg							{ $$ = $1; }
	| func_decl_arglist_arg ',' func_decl_arglist 	{ $$ = createString( $1, $3 ); }

func_decl_arglist_arg:
	  KWD_INT LABEL { 
		if(!func_decl_detector){ 
			clearSymbolTable(); 
			func_decl_detector=true; 
		}  
		declSymbol($2, 1); 
		$$ = createString("");
	  }

func_call_arglist:
	  %empty										{ $$ = createString(""); }
	| func_call_arglist_arg							{ $$ = $1; }
	| func_call_arglist_arg ',' func_call_arglist 	{ $$ = createString( $1, $3 ); }

func_call_arglist_arg:
	  LABEL { $$ = createString("subi $29, $29, 4 \n"); }

decl_stmt:
	  KWD_INT decl_list { $$ = $2; }
	  ;

decl_list:
	  var_decl					{ $$ = $1; }
	| var_decl ',' decl_list	{ $$ = createString( $1, $3 ); }
	  ;

var_decl:
	  LABEL 			{ $$ = createString("subi $29, $29, 4\n"); declSymbol($1, 1); }
	| LABEL '[' INTEGER ']' { 
	  		if ( $3 > 1024) yyerror("Array size is too large.");
	  		sprintf(strBuffer, "subi $29, $29, %d\n", 4*$3);
	  		$$ = createString(strBuffer, false); 
	  		declSymbol($1, $3); 
	  }

if_stmt:
	KWD_IF '(' expr ')' stmt { 
		char* ifExit = getNewLabel();
		sprintf(strBuffer, "%sandi $2, $2, 0 \nbe $1, $2, %s \n%s \n%s:\n", $3, ifExit, $5, ifExit);
		$$ = createString(strBuffer, false);
	}

while_stmt:
	KWD_WHILE '(' expr ')' stmt {
		char* loopExit = getNewLabel(), *loopEntry = getNewLabel();
		sprintf(strBuffer, "%s: \n%sandi $2, $2, 0 \nbe $1, $2, %s \n%sj %s \n%s:\n", loopEntry, $3, loopExit, $5, loopEntry, loopExit);
		$$ = createString(strBuffer, false);
	}

return_stmt:
	  KWD_RETURN { $$ = createString("ld $31, 4($29) \nld $4, 8($29) \nori $29, $30, 0 \nori $30, $4, 0\njr $31"); }
	| KWD_RETURN expr { $$ = createString($2, createString("ld $31, 4($29) \nld $4, 8($29) \nori $29, $30, 0 \nori $30, $4, 0\njr $31")); }
%%



int main (void)
{
  int ret = yyparse ();
  printf("Generated Assembly: \n%s", generatedAssembly);
  return ret;
}

/* Called by yyparse on error.  */
void yyerror(char const *s)
{
	extern int yylineno;	// defined and maintained in lex.c
	extern char *yytext;	// defined and maintained in lex.c
	printf("Error: %s at symbol \"%s\" in line %d \n", s, yytext, yylineno);
}
