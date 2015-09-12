#include <stdio.h>
#include <stdint.h>
#include <time.h>

#include <cstdlib>
#include <unordered_map>
#include <utility>

#define PRINT_SIMULATION_SPEED
#define CACHE_SIMULATION
#define BRANCH_PREDICTION_SIMULATION

#define RAM_SIZE 65536
#define CACHE_SIZE 4096
#define CACHE_LINE_SIZE 4
#define CACHE_ASSOCIATIVITY 4
#define PREDICTION_TABLE_SIZE 8
#define NO_BRANCH_PREDICTION_HISTORY_BITS 3


uint32_t memory[RAM_SIZE];
uint32_t register_file[32];

void print_regs(){
	printf("REGISTER VALUES:\n");
	for(int i = 0;i < 32;i++){
		printf("\t$%d = %d\n", i, register_file[i]);
	}
}

unsigned int no_instructions = 0;
#ifdef INTERACTIVE_STEPPING
int noStepsToSkip = 0;
void interactive_stepping(){
	++ no_instructions;
	if ( noStepsToSkip > 0 )
		--noStepsToSkip;
	else{
		int temp = scanf("%d", &noStepsToSkip);
		print_regs();
	}
}
#else
void interactive_stepping(){
	++ no_instructions;
}
#endif

#ifdef CACHE_SIMULATION
/********************************************
The following constants need to be defined
	- CACHE_SIZE
	- CACHE_LINE_SIZE
	- CACHE_ASSOCIATIVITY

	The replacement policy implemented now is LRU

	They should all be powers of two for simulation efficiency (and realism)
********************************************/
uint32_t cache[CACHE_SIZE/CACHE_LINE_SIZE][CACHE_ASSOCIATIVITY][2]; //format: first field contains address, second field contains the timestamp
int no_cache_hits = 0, no_memory_accesses = 0;

uint32_t memory_access( int index ){
	int cache_line = index*(CACHE_SIZE/(RAM_SIZE*CACHE_LINE_SIZE));
	++ no_memory_accesses;

	int LRUId = 0, LRUTimestamp = cache[cache_line][0][1];
	for(int i = 0;i < CACHE_ASSOCIATIVITY; i++){
		if( cache[cache_line][i][0] == index ){
			++ no_cache_hits;
			cache[cache_line][i][1] = no_memory_accesses;
			return memory[index];
		}
		if( cache[cache_line][i][1] < LRUTimestamp ){
			LRUId = i;
			LRUTimestamp = cache[cache_line][i][1];
		}
	}

	//replace cache line
	cache[cache_line][LRUId][0] = index;
	cache[cache_line][LRUId][1] = no_memory_accesses;

	return memory[index];
}

void memory_access( int index, int value ){
	int cache_line = index*(CACHE_SIZE/(RAM_SIZE*CACHE_LINE_SIZE));
	++ no_memory_accesses;

	int LRUId = 0, LRUTimestamp = cache[cache_line][0][1];
	for(int i = 0;i < CACHE_ASSOCIATIVITY; i++){
		if( cache[cache_line][i][0] == index ){
			++ no_cache_hits;
			cache[cache_line][i][1] = no_memory_accesses;
			memory[index] = value;
		}
		if( cache[cache_line][i][1] < LRUTimestamp ){
			LRUId = i;
			LRUTimestamp = cache[cache_line][i][1];
		}
	}

	//replace cache line
	cache[cache_line][LRUId][0] = index;
	cache[cache_line][LRUId][1] = no_memory_accesses;

	memory[index] = value;
}
void print_cache_information(){
	printf("\nCache Configuration:\n\tRam size: \t\t%d\n\tCache size: \t\t%d words\n\tCache line Length: \t%d words\n\tAssociativity: \t\t%d way\n", RAM_SIZE, CACHE_SIZE, CACHE_LINE_SIZE, CACHE_ASSOCIATIVITY);
	if( no_memory_accesses == 0 )
		printf("No memory accesses were performed in the program.\n");
	else
		printf("Performance:\n\tNo. of accesses: \t%d\n\tNo. of hits: \t\t%d\n\tHit ratio: \t\t%d%%\n", no_memory_accesses, no_cache_hits, (int)((100.0*no_cache_hits)/no_memory_accesses+0.5));
}
#else
uint32_t memory_access( int index ){
	return memory[index];
}
void memory_access( int index, int value ){
	memory[index] = value;
}
#endif

#ifdef BRANCH_PREDICTION_SIMULATION
/********************************************
The following constants need to be defined
	- PREDICTION_TABLE_SIZE
	- NO_BRANCH_PREDICTION_HISTORY_BITS

	The policy currently implemented is a majority vote from history
********************************************/

std::unordered_map<int, int> branch_prediction_table;
int no_branches = 0, no_correct_branch_predictions = 0;
void branch_predict(int pc, bool truth_value){
	++ no_branches;
	if( branch_prediction_table.count(pc) > 0 ){
		bool prediction = branch_prediction_table[pc] > (1<<(NO_BRANCH_PREDICTION_HISTORY_BITS-1));
		no_correct_branch_predictions += (prediction == truth_value);
		branch_prediction_table[pc] = std::max(branch_prediction_table[pc] + (prediction == truth_value)*2 - 1, (1<<NO_BRANCH_PREDICTION_HISTORY_BITS)-1);
	}
	else{
		if( truth_value )
			branch_prediction_table[pc] = (1<<NO_BRANCH_PREDICTION_HISTORY_BITS-1) + 1;
		else
			branch_prediction_table[pc] = (1<<NO_BRANCH_PREDICTION_HISTORY_BITS-1);
	}
}

void print_branch_prediction_information(){
	printf("\nBranch Predictor Configuration\n\tPredictor table size: \t\t%d\n\tNo. History Bits: \t\t%d bits\n", PREDICTION_TABLE_SIZE, NO_BRANCH_PREDICTION_HISTORY_BITS);
	if( no_branches == 0)
		printf("No branches were executed in this program.\n");
	else
		printf("Branch Predictor Performance\n\tNo. Conditional Branches: \t%d\n\tNo. Correct Predictions: \t%d\n\tPercentage Accuracy: \t\t%d\n", no_branches, no_correct_branch_predictions, (int)(100.0*no_correct_branch_predictions/no_branches + 0.5));
}
#else
void branch_predict(int pc, bool truth_value){
	//don't care
}
#endif

void execute(){
	goto Label0;
	interactive_stepping();
	Label3: goto Label1;
	interactive_stepping();
	Label7: register_file[7] = register_file[7] & 0;
	interactive_stepping();
	register_file[7] = register_file[1] + 0;
	interactive_stepping();
	goto Label2;
	interactive_stepping();
	Label8: return;
	interactive_stepping();
	Label0: scanf("%d\n", &register_file[1]);
	interactive_stepping();
	register_file[5] = register_file[5] & 0;
	interactive_stepping();
	register_file[3] = register_file[3] & 0;
	interactive_stepping();
	register_file[5] = register_file[1] + 0;
	interactive_stepping();
	register_file[4] = register_file[4] & 0;
	interactive_stepping();
	register_file[4] = register_file[29] + 0;
	interactive_stepping();
	Label4: scanf("%d\n", &register_file[1]);
	interactive_stepping();
	register_file[4] = register_file[4] - register_file[3];
	interactive_stepping();
	 memory_access( 0 + register_file[4], register_file[1] ) ;
	interactive_stepping();
	register_file[3] = register_file[3] + 1;
	interactive_stepping();
	if( register_file[5] == register_file[3]) {
		branch_predict( 64, register_file[5] == register_file[3] );
		goto Label3;
	}
	interactive_stepping();
	goto Label4;
	interactive_stepping();
	Label1: register_file[3] = register_file[3] & 0;
	interactive_stepping();
	register_file[4] = register_file[4] & 0;
	interactive_stepping();
	register_file[4] = register_file[29] + 0;
	interactive_stepping();
	register_file[1] = register_file[1] & 0;
	interactive_stepping();
	Label6: register_file[4] = register_file[4] - register_file[3];
	interactive_stepping();
	register_file[6] =  memory_access( 0 + register_file[4] ) ;
	interactive_stepping();
	register_file[1] = register_file[1] + register_file[6];
	interactive_stepping();
	register_file[3] = register_file[3] + 1;
	interactive_stepping();
	if( register_file[5] == register_file[3]) {
		branch_predict( 104, register_file[5] == register_file[3] );
		goto Label5;
	}
	interactive_stepping();
	goto Label6;
	interactive_stepping();
	Label5: register_file[1] = register_file[1] / register_file[5];
	interactive_stepping();
	goto Label7;
	interactive_stepping();
	Label2: register_file[3] = register_file[3] & 0;
	interactive_stepping();
	register_file[4] = register_file[4] & 0;
	interactive_stepping();
	register_file[4] = register_file[29] + 0;
	interactive_stepping();
	register_file[1] = register_file[1] & 0;
	interactive_stepping();
	Label9: register_file[4] = register_file[4] - register_file[3];
	interactive_stepping();
	register_file[6] =  memory_access( 0 + register_file[4] ) ;
	interactive_stepping();
	register_file[6] = register_file[6] - register_file[7];
	interactive_stepping();
	register_file[6] = register_file[6] * register_file[6];
	interactive_stepping();
	register_file[1] = register_file[1] + register_file[6];
	interactive_stepping();
	register_file[3] = register_file[3] + 1;
	interactive_stepping();
	if( register_file[5] == register_file[3]) {
		branch_predict( 160, register_file[5] == register_file[3] );
		goto Label8;
	}
	interactive_stepping();
	goto Label9;
	interactive_stepping();

}

int main(){
	register_file[29] = RAM_SIZE-1; //load the stack pointer

	clock_t timer = clock();
	execute();
	timer = clock() - timer;
	
	print_regs();

	#ifdef CACHE_SIMULATION
	print_cache_information();
	#endif

	#ifdef BRANCH_PREDICTION_SIMULATION
	print_branch_prediction_information();
	#endif

	#ifdef PRINT_SIMULATION_SPEED
	float no_seconds = ((float)timer)/CLOCKS_PER_SEC;
	if( no_seconds <= 1.0e-3)
		printf("\nExecuted in %f seconds. Program executed too quickly to find instructions/second", no_seconds);
	else
		printf("\nExecuted in %f seconds at %ld instructions/second\n", no_seconds, (long)(no_instructions/no_seconds));
	#endif

	return 0;
}