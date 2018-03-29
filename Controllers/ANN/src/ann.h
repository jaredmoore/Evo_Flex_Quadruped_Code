
#ifndef ANN_H
#define ANN_H

#include <vector>


// references
// - http://www.faqs.org/faqs/ai-faq/neural-nets/part1/
// - https://github.com/peter-ch/MultiNEAT

// ----------------------------------------------------------------------------
// 
// --- A single compuational neuron
// 

typedef enum NeuronType_E 
{
    INPUT_N,
    OUTPUT_N,
    HIDDEN_N,
    NUM_NEURON_TYPE
} NeuronType;

class Neuron
{
public:

    // Summation of input values
    double input_sum;

    // Value of input_sum passed through an activation
    double output;

    // Type of neuron {input, output, hidden}
    NeuronType type;

public:
    // Constructor
    Neuron(NeuronType ntype) : 
        type(ntype), 
        input_sum(0), 
        output(0) 
    {
    }
};



// ----------------------------------------------------------------------------
// 
// --- A communication channel between two Neurons
// 
class Connection
{
public:

    // Indices for the source and target neurons of this connection
    unsigned short int source_neuron_idx;
    unsigned short int target_neuron_idx;

    // connection data
    double weight;
    double data;

public:

    // Constructor
    Connection(int source, int target, double w) : 
        source_neuron_idx(source),
        target_neuron_idx(target),
        weight(w), 
        data(0)
    {
    }

};



// ----------------------------------------------------------------------------
// 
// --- An artificial neural network data structure for holding all of the
// neurons and connections
// 

class ANN
{
public:

    // Total number of neurons
    unsigned short int num_input;
    unsigned short int num_hidden;
    unsigned short int num_output;
    unsigned short int num_iPLUSh;
    unsigned short int total_num_neurons;

    // Vector of neurons
    std::vector<Neuron> neurons;
    //      input neurons  : 0..(num_input-1)
    //      hidden neurons : num_input..(num_input+num_hidden-1)
    //      output neurons : (num_input+num_hidden)..(total_num_neurons-1)
         
    // Total number of connections between neurons
    unsigned short int total_num_connections;

    // Vector of connections
    std::vector<Connection> connections;

public:

    // 
    // --- Constructors and destructor
    // 
    
    ANN(std::vector<int> &num_neurons, std::vector<int> &c_src, std::vector<int> &c_trg, 
        std::vector<double> &c_wts);
    ANN(const char *fname);
    ~ANN();

    // 
    // --- ANN initialization
    // 

    // Initialize ANN connections as a fully connected feed-forward network
    void fullyConnectFF();

    // Initialize network weights
    int randomizeW(double min, double max);
    int randomizeW();

    // 
    // --- Interact with an ANN
    // 

    // Set input values
    int setInput(std::vector<double> &inputs);

    // Get output values
    std::vector<double> getOutput();

    // Activate the network
    void activate();

    // 
    // --- Save/Load an ANN
    // 
    int serialize(const char *out_fname);
    int deserialize(const char *in_fname);

    // 
    // --- ANN data printing
    // 
    void stream(std::ostream &strm);

};


// ----------------------------------------------------------------------------
// 
// --- C interface
// declare a type to be used by C: typedef struct ANN_C ANN_C
// declare functions with: extern "C" ...
// 

// Moving inside extern, uncomment if error.
// typedef void ANN_C;
extern "C"
{
    typedef void ANN_C;

    ANN_C* new_ANN(int *num_neurons, int *c_src, int *c_trg, double *c_wts, int c_cnt);
    ANN_C* new_ANN_FromFile(const char *fname);
    void delete_ANN(ANN_C *net);

    void fullyConnectFF_ANN(ANN_C *net);

    int randomizeW_ANN(ANN_C *net, double min, double max);

    int setInput_ANN(ANN_C *net, double *inputs, int count);

    int getOutput_ANN(ANN_C *net, double *outputs, int count);

    void activate_ANN(ANN_C *net);

    int serialize_ANN(ANN_C *net, const char *out_fname);

    int deserialize_ANN(ANN_C *net, const char *in_fname);

    void print_ANN(ANN_C *net);
}



#endif

