typedef enum {KWD_IF=258, KWD_WHILE, KWD_INT, LABEL=259, LIT_INTEGER, OP_PLUS, OP_EQUAL, OP_EQEQUAL, OP_MINUS, OP_MULT, OP_DIV} tok_type;
typedef struct{
	tok_type type;
	union{
		int int_val;
		char* string;
	} value;
}token;