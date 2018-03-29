
// ----------------------------------------------------------------------------
// --- Headers
// ----------------------------------------------------------------------------

// Standard libraries
#include <iostream>
#include <fstream>
#include <cmath>

// User defined libraries
#include "ann.h"


// ----------------------------------------------------------------------------
// --- Helper functions
// ----------------------------------------------------------------------------

static inline double sigmoid_AF(double x) { 
    double activation = 0.0;
    if (x < -15) {
        activation = 0.0;
    } else if (x > 15) {
        activation = 1.0;
    } else {
        activation = 1.0 / (1.0 + exp(-x));
    }

    return activation;
}


// ----------------------------------------------------------------------------
// --- Constructors and Destructors
// ----------------------------------------------------------------------------

// ------------------------------------ new -----------------------------------
// Create an artificial neural network
// 
// Arguments
// - num_neurons : a vector of size 2 or 3
//      num_input  = num_neurons[0]
//      num_hidden = (num_neurons.size()==2) ? 0 : num_neurons[1]
//      num_output = (num_neurons.size()==2) ? num_neurons[1] : num_neurons[2]
// - c_src, c_trg, c_wts : vectors must be the same size
//      if c_src.size() != c_trg.size() then error
//      if c_src.size() != c_wts.size() then error
//      if c_trg.size() != c_wts.size() then error
//      if c_src.size() == 0 then no connections are added
//      if c_src.size > 0 then create a connection for each c_src/trg pair
// 
// Return
// - ann : pointer to an allocated ANN object (must be deleted by user);
//   NULL if failure
//      
ANN::ANN(std::vector<int> &num_neurons, std::vector<int> &c_src, std::vector<int> &c_trg,
    std::vector<double> &c_wts)
{
    // 
    // Check input arguments
    // 
    if (!(num_neurons.size() == 2 || num_neurons.size() == 3)) {
        std::cerr << "ANN: num_neurons must be a vector with 2 or 3 elements.";
        std::cerr << "\n     - given vector of size: " << num_neurons.size();
        std::cerr << std::endl;
        exit(EXIT_FAILURE);
    }
    if (c_src.size() != c_trg.size() || c_src.size() != c_wts.size() || c_trg.size() != c_wts.size()) {
        std::cerr << "ANN: c_src.size() must be the same as c_trg.size() and c_wts.size()." << std::endl;
        std::cerr << "c_src.size(): " << c_src.size();
        std::cerr << " c_trg.size(): " << c_trg.size();
        std::cerr << " c_wts.size(): " << c_wts.size();
        std::cerr << std::endl;
        exit(EXIT_FAILURE);
    }

    // 
    // Set ANN parameters
    // 
    this->num_input  = num_neurons[0];
    this->num_hidden = (num_neurons.size()==2) ? 0 : num_neurons[1];
    this->num_output = (num_neurons.size()==2) ? num_neurons[1] : num_neurons[2];

    this->num_iPLUSh = this->num_input + this->num_hidden;    
    this->total_num_neurons = this->num_iPLUSh + this->num_output;

    this->total_num_connections = c_src.size();

    // 
    // Allocate space for, and create neurons
    // 
    this->neurons.reserve(this->total_num_neurons);
    for (int n = 0; n < this->total_num_neurons; ++n) {

        // Set neuron type based on index
        NeuronType ntype;
        if (n < this->num_input) ntype = INPUT_N;
        else if (n < this->num_iPLUSh) ntype = HIDDEN_N;
        else ntype = OUTPUT_N;

        // Add a new neuron to the vector
        this->neurons.push_back(Neuron(ntype));
    }

    // 
    // Allocate space for, and connections if required
    // 
    if (this->total_num_connections > 0) {
        this->connections.reserve(this->total_num_connections);
        for (int c = 0; c < this->total_num_connections; ++c) {
            
            // Check connection indices
            if (c_src[c] < 0 || c_src[c] > this->total_num_neurons ||
                c_trg[c] < 0 || c_trg[c] > this->total_num_neurons) 
            {
                std::cerr << "ANN: Neuron index out-of-bounds.";
                std::cerr << std::endl;
                exit(EXIT_FAILURE);
            }

            // Add new connection
            this->connections.push_back(Connection(c_src[c], c_trg[c], c_wts[c]));
        }
    }
}
ANN_C* new_ANN(int *num_neurons, int *c_src, int *c_trg, double *c_wts, int c_cnt)
{
    std::vector<int> num(num_neurons, num_neurons + NUM_NEURON_TYPE);
    std::vector<int> src;
    std::vector<int> trg;
    std::vector<double> wts;
    if (c_cnt > 0) {
        src.assign(c_src, c_src + c_cnt);
        trg.assign(c_trg, c_trg + c_cnt);
        wts.assign(c_wts, c_wts + c_cnt);
    }
    ANN_C *new_ann = static_cast<ANN_C*>(new ANN(num, src, trg, wts));    
    return new_ann;
}


// ------------------------------------ new -----------------------------------
// Create an artificial neural network from a serialized file
// 
// Arguments
// - fname : file name of the serialized data
// 
// Return
// - ann : pointer to an allocated ANN object (must be deleted by user);
//   NULL if failure
//      
ANN::ANN(const char *fname)
{
    this->deserialize(fname);
}
ANN_C* new_ANN_FromFile(const char *fname)
{
    ANN_C *new_ann = static_cast<ANN_C*>(new ANN(fname));
    return new_ann;
}


// ------------------------------------ delete --------------------------------
// --- Free any allocated memory
// 
// Argurments
// - net : ANN to delete (for C implementation)
// 
ANN::~ANN()
{
}
void delete_ANN(ANN_C *net)
{
    delete static_cast<ANN*>(net);
}



// ----------------------------------------------------------------------------
// --- Methods
// ----------------------------------------------------------------------------

// ------------------------------------ fullyConnectFF ------------------------
// --- Initialize connections as a fully-connected feedforward ANN (mainly 
// meant as a method for testing ANN functionality)
// 
// Note: this function will remove any connections previously made
// 
// Argurments
// - net : ANN to fully-connect (for C implementation)
// 
void ANN::fullyConnectFF() 
{
    int c = 0;

    // Clear current connections (if any) and resize
    this->connections.clear();
    this->total_num_connections = 
        this->num_hidden * (this->num_input + this->num_output);
    this->connections.reserve(this->total_num_connections);

    // 
    // Setup connections
    // 
    for (int i = 0; i < this->num_input; ++i) {
        for (int h = this->num_input; h < this->num_iPLUSh; ++h, ++c) {
            this->connections.push_back(Connection(i, h, 0));
        }
    }
    for (int h = this->num_input; h < this->num_iPLUSh; ++h) {
        for (int o = this->num_iPLUSh; o < this->total_num_neurons; ++o, ++c) {
            this->connections.push_back(Connection(h, o, 0));
        }
    }
}
void fullyConnectFF_ANN(ANN_C *net)
{
    ANN *a = static_cast<ANN*>(net);
    a->fullyConnectFF();
}



// ------------------------------------ randomizeW ----------------------------
// --- Initialize ANN weights uniformly at random
// 
// Arguments
// - net : ANN to alter (for C implementation)
// - min : minimum weight value (default -1)
// - max : maximum weight value (default +1)
// 
// Return
// - error = (failure) ? -1 : 0
// 
int ANN::randomizeW(double min, double max) 
{
    if (min >= max) {
        std::cerr << "ANN: min must be < max when randomly initializing";
        std::cerr << " network weights.";
        std::cerr << std::endl;
        return -1;
    }
    for (int c = 0; c < this->connections.size(); ++c) {
        double new_w = (max - min) * (double)rand() / (double)RAND_MAX + min;
        this->connections[c].weight = new_w;
    }
    return 0;
}
int ANN::randomizeW()
{
    return randomizeW(-1, 1);
}
int randomizeW_ANN(ANN_C *net, double min, double max)
{
    ANN *a = static_cast<ANN*>(net);
    return a->randomizeW(min, max);
}



// ------------------------------------ setInput ------------------------------
// --- Set input values for the ANN
// 
// Argurments
// - net    : ANN to update (for C implementation)
// - inputs : inputs to the ANN
// 
// Return
// - error = (failure) ? -1 : 0
// 
int ANN::setInput(std::vector<double> &inputs)
{
    // 
    // Check size of inputs
    // 
    if (inputs.size() != this->num_input) {
        std::cerr << "ANN: size of input vector must be the same as the ";
        std::cerr << "number of input neurons." << std::endl;
        return -1;
    }
    for (int n = 0; n < this->num_input; ++n) {
        this->neurons[n].output = inputs[n];
    }
    return 0;
}
int setInput_ANN(ANN_C *net, double *inputs, int count)
{
    std::vector<double> net_inputs(inputs, inputs + count);
    ANN *a = static_cast<ANN*>(net);
    return a->setInput(net_inputs);
}


// ------------------------------------ getOutput -----------------------------
// --- Get output values for the ANN
// 
// Argurments
// - net     : ANN to update (for C implementation)
// - outputs : vector in which the values should be placed
// 
// Return
// - error = (failure) ? -1 : 0
// 
std::vector<double> ANN::getOutput()
{
    std::vector<double> output;
    for (int n = this->num_iPLUSh; n < this->total_num_neurons; ++n) {
        output.push_back(this->neurons[n].output);
    }
    return output;
}
int getOutput_ANN(ANN_C *net, double *outputs, int count)
{
    ANN* a = static_cast<ANN*>(net);
    if (count != a->num_output) {
        std::cerr << "ANN: size of outputs array must be the same as the";
        std::cerr << " the number of output neurons." << std::endl;
        return -1;
    }
    std::vector<double> v = a->getOutput();
    for (int i = 0; i < count; ++i) {
        outputs[i] = v[i];
    }
    return 0;
}


// ------------------------------------ activate ------------------------------
// --- Activate the ANN using a sigmoid function
// 
// Argurments
// - net : ANN to activate (for C implementation)
// 
void ANN::activate() 
{
    Connection *conn;
    Neuron *source, *target;

    // 
    // Calculate the data value for each connection and feed to target neuron
    // 
    for (int c = 0; c < this->connections.size(); ++c) {
        conn = &this->connections[c];
        source = &this->neurons[conn->source_neuron_idx];
        target = &this->neurons[conn->target_neuron_idx];

        conn->data = conn->weight * source->output;

        target->input_sum += conn->data;
    }

    // 
    // Activate each neuron
    // 
    for (int n = this->num_input; n < this->total_num_neurons; ++n) {
        this->neurons[n].output = sigmoid_AF(this->neurons[n].input_sum);
        this->neurons[n].input_sum = 0;
    }
}
void activate_ANN(ANN_C *net)
{
    ANN* a = static_cast<ANN*>(net);
    a->activate();
}


// ------------------------------------ serialize -----------------------------
// --- Write the ANN to a file (not precise)
// 
// Argurments
// - net       : ANN to write (for C implementation)
// - out_fname : name of the output file
// 
// Return
// - error = (failure) ? -1 : 0
// 

int ANN::serialize(const char *out_fname)
{
    std::ofstream out_file(out_fname);
    if (!out_file.is_open()) {
        std::cerr << "ANN: the file could not be created: ";
        std::cerr << out_fname << std::endl;
        return -1;
    }

    // 
    // --- Write neuron data to file
    // 
    out_file << this->num_input << std::endl;
    out_file << this->num_hidden << std::endl;
    out_file << this->num_output << std::endl;
    out_file << this->num_iPLUSh << std::endl;
    out_file << this->total_num_neurons << std::endl;

    for (int n = 0; n < this->neurons.size(); ++n) {
        out_file << static_cast<int>(this->neurons[n].type) << std::endl;
    }

    // 
    // --- Write connection data to file
    // 
    out_file << this->total_num_connections << std::endl;

    for (int c = 0; c < this->connections.size(); ++c) {
        out_file << this->connections[c].source_neuron_idx << std::endl;
        out_file << this->connections[c].target_neuron_idx << std::endl;
        out_file << this->connections[c].weight << std::endl;
    }
    
    out_file.close();
    return 0;
}
int serialize_ANN(ANN_C *net, const char *out_fname)
{
    ANN* a = static_cast<ANN*>(net);
    return a->serialize(out_fname);
}



// ------------------------------------ deserialize ---------------------------
// --- Read an ANN from a file (not precise)
// 
// Argurments
// - net      : ANN to set (for C implementation)
// - in_fname : name of the output file
// 
// Return
// - error = (failure) ? -1 : 0
// 
int ANN::deserialize(const char *in_fname)
{
    std::ifstream in_file(in_fname);
    if (!in_file.is_open()) {
        std::cerr << "ANN: the file could not be opened: ";
        std::cerr << in_fname << std::endl;
        return -1;
    }

    // 
    // --- Read neuron data from file
    // 
    in_file >> this->num_input;
    in_file >> this->num_hidden;
    in_file >> this->num_output;
    in_file >> this->num_iPLUSh;
    in_file >> this->total_num_neurons;

    int ntype;
    this->neurons.clear();
    this->neurons.reserve(this->total_num_neurons);
    for (int n = 0; n < this->total_num_neurons; ++n) {
        in_file >> ntype;
        this->neurons.push_back(Neuron(static_cast<NeuronType>(ntype)));
    }

    // 
    // --- Write connection data to file
    // 
    in_file >> this->total_num_connections;

    unsigned short int src;
    unsigned short int trg;
    double w;
    this->connections.clear();
    this->connections.reserve(this->total_num_connections);
    for (int c = 0; c < this->total_num_connections; ++c) {
        in_file >> src;
        in_file >> trg;
        in_file >> w;
        this->connections.push_back(Connection(src, trg, w));
    }
    
    in_file.close();
    return 0;
}
int deserialize_ANN(ANN_C *net, const char *in_fname)
{
    ANN* a = static_cast<ANN*>(net);
    return a->deserialize(in_fname);
}



// ------------------------------------ stream --------------------------------
// --- Write ANN information to the given stream
// 
// Arguments
// - strm : stream to write to 
// 
void ANN::stream(std::ostream &strm)
{
    strm << "Total number of neurons : " << this->total_num_neurons;
    strm << std::endl;
    strm << "Number of input neurons : " << this->num_input << std::endl;
    strm << "Number of hidden neurons: " << this->num_hidden << std::endl;
    strm << "Number of outout neurons: " << this->num_output << std::endl;

    for (int n = 0; n < this->total_num_neurons; ++n) {
        strm << this->neurons[n].type << " ";
    }
    strm << std::endl;

    strm << "Total number of connections: " << this->total_num_connections;
    strm << std::endl;

    for (int c = 0; c < this->total_num_connections; ++c) {
        strm << this->connections[c].source_neuron_idx << " --> ";
        strm << this->connections[c].target_neuron_idx << " : ";
        strm << this->connections[c].weight << std::endl;
    }
}
void print_ANN(ANN_C *net)
{
    ANN* a = static_cast<ANN*>(net);
    a->stream(std::cout);
}




