#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
   This file belong to https://github.com/snolfi/evorobotpy
   and has been written by Stefano Nolfi and Paolo Pagliuca, stefano.nolfi@istc.cnr.it, paolo.pagliuca@istc.cnr.it
   es.py runs an evolutionary expriment or post-evaluate an evolved robot/s
   type python3 es.py for help
   Requires policy.py, evoalgo.py, and salimans.py
   Also requires the net.so library that can be obtained by compiling with cython the following files contained in the ./lib directory:
   evonet.cpp, evonet.h, utilities.cpp, utilities.h, net.pxd, net.pyx and setupevonet.py   
   with the commands: cd ./evorobotpy/lib; python3 setupevonet.py build_ext –inplace; cp net*.so ../bin 
"""

import numpy as np
import configparser
import argparse
import sys
import os
import subprocess
import stat
import regulation_task
import regulation_task_mutable
import regulation_task_scalable
#import balance_bot
#import gym
#import balance_bot


environment = None                      # the problem 
algoname = "OpenAI-ES"                  # evolutionary algorithm

# Parse the [ADAPT] section of the configuration file
def parseConfigFile(filename):
    global environment
    global algoname

    if os.path.isfile(filename):

        config = configparser.ConfigParser()
        config.read(filename)

        # Section EVAL
        options = config.options("EXP")
        for o in options:
            found = 0
            if o == "environment":
                environment = config.get("EXP","environment")
                found = 1
            if o == "algo":
                algoname = config.get("EXP","algo")
                found = 1
              
            if found == 0:
                print("\033[1mOption %s in section [EXP] of %s file is unknown\033[0m" % (o, filename))
                sys.exit()
    else:
        print("\033[1mERROR: configuration file %s does not exist\033[0m" % (filename))
        sys.exit()


def editEnvFromConfig(env, filename):
    if os.path.isfile(filename):

        config = configparser.ConfigParser()
        config.read(filename)

        options = config.options("ENV")
        for o in options:
            found = 0
            if o == "noiseamp":
                noiseamp = config.get("ENV","noiseamp")
                env.body.nutrient_stream.noise_amplitude = noiseamp
                found = 1
            if o == "nosieoffset":
                noiseoffset = config.get("ENV","noiseoffset")
                env.body.nutrient_stream.noise_offset = noiseoffset
                found = 1

            if found == 0:
                print("Using default env settings")

        a = input("ENTER")


def helper():
    print("Program Arguments: ")
    print("-f [fileini]              : the file containing the hyperparameters(mandatory)")
    print("-s [integer]              : the number used to initialize the seed")
    print("-n [integer]              : the number of replications to be run")
    print("-p                        : the flag to be used to postevaluate an agent (see parameter -g)")
    print("-g [filename]             : the name of teh file containing the parameters of the agent")
    print("-d                        : the flag that permit to show the activation of neurons during postevaluation")    
    print("-o [directory]            : the directory where all output files are stored (default current dir)")
    print("-w [integer]              : the number of workers used by parallel implementations")
    print("")
    print("The .ini file contains the following [EXP], [POLICY] and [ALGO] parameters:")
    print("[EXP]")
    print("environment [string]      : environment (default 'CartPole-v0'")
    print("algo [string]             : adaptive algorithm (default 'OpenAI-ES'), SSS, coevo, coevo2" )
    print("[POLICY]")
    print("nrobots [integer]         : number of robots (default 1)")
    print("heterogeneous [integer]   : whether robots are heterogeneous (default 0)")
    print("episodes [integer]        : number of evaluation episodes (default 1)")
    print("pepisodes [integer]       : number of post-evaluation episodes (default 0)")
    print("maxsteps [integer]        : number of evaluation steps [for EREnvs only] (default 1000)")
    print("nhiddens [integer]        : number of hidden x layer (default 50)")
    print("nlayers [integer]         : number of hidden layers (default 1)")
    print("bias [0/1]                : whether we have biases (default 0)")
    print("out_type [integer]        : type of output: 1=logistic, 2=tanh, 3=linear, 4=binary (default 2)")
    print("nbins [integer]           : number of bins 1=no-beans (default 1)")
    print("architecture [0/1/2/3]    : network architecture 0=feedforward 1=recurrent 2=fullrecurrent 3=lstm recurrent (default 0)")
    print("afunction [1/2/3]         : the activation function of neurons 1=logistic 2=tanh 3=linear (default 2)")
    print("winit [0/1/2]             : weight initialization 0=xavier 1=norm incoming 2=uniform (default 0)")
    print("action_noise [0/1/2]      : action noise 0=none, 1=gaussian 2=diagonal gaussian (default 0)")
    print("action_noise_range        : action noise range (default 0.01)")   
    print("normalized [0/1]          : whether or not the input observations are normalized (default 1)")
    print("clip [0/1]                : whether we clip observation in [-5,5] (default 0)")
    print("[ALGO]   parameters of the OpenAI-ES algorithm, the default algorithm")
    print("maxmsteps [integer]       : max number of (million) steps (default 1)")
    print("stepsize [float]          : learning stepsize (default 0.01)")
    print("samplesize [int]          : popsize/2 (default 20)")
    print("noiseStdDev [float]       : samples noise (default 0.02)")
    print("wdecay [0/2]              : weight decay (default 0), 1 = L1, 2 = L2")
    print("symseed [0/1]             : same environmental seed to evaluate symmetrical samples [default 1]")
    print("saveeach [integer]        : same data every N minutes [default 60]")
    print("maxmsteps [integer]       : max number of (million) steps (default 1)")
    print("")
    sys.exit()


def main(argv):
    global environment
    global algoname

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--fileini', help='name of ini file', type=str, default="")
    parser.add_argument('-s', '--seed', help='random generator seed', type=int, default=1)
    parser.add_argument('-n', '--nreplications', help='number of replications', type=int, default=1)
    parser.add_argument('-w', '--workers', help='number of workers', type=int, default=1)
    parser.add_argument('-p', '--postevaluate', help='postevaluate an agent', action='store_true', default=False)
    parser.add_argument('-g', '--genofile', help='name of the file containing the parameters of the agent', type=str, default=None)
    parser.add_argument('-d', '--displayneurons', help='show the activation of the neurons', action='store_true', default=False)
    parser.add_argument('-o', '--folder', help='file folder', type=str, default=".")    
    args = parser.parse_args()

    if (len(args.fileini) == 0):    # if the name of the inifile is not specified display help information
        print("\033[1mERROR: You need to specify an .ini file\033[0m")
        helper()
        sys.exit(-1)

    parseConfigFile(args.fileini)   # load hyperparameters from the ini file

    availableAlgos = ('OpenAI-ES','SSS', 'coevo2', 'coevo')   # check whether the user specified a valid algorithm
    if algoname not in availableAlgos:
        print("\033[1mAlgorithm %s is unknown\033[0m" % algoname)
        print("Please use one of the following algorithms:")
        for a in availableAlgos:
            print("%s" % a)
        sys.exit(-1)

    test = 0
    if args.postevaluate:
        if args.displayneurons:
            test = 2
        else:
            test = 1
    
    if args.workers > 1:            # create multiple threads
        from fork import FORK
        forc = FORK()
        typ, comm, rank = forc.mpi_fork(args.workers)
        if typ == "parent": 
            sys.exit(-1)
        print("process", rank, "out of total ", comm.Get_size(), "started")

    
    print("Experiment: Environment %s Algo %s nreplications %d " % (environment, algoname, args.nreplications))
    

    if "Scalable" in environment: #------------------------------------------------- SCALABLE POLICY --------------------------------------------
        print("SCALABLE TASK")
        import gym
        from gym import spaces
        env = gym.make(environment)
        from policy import GymPolicyScalable
        policy = GymPolicyScalable(env, args.fileini, args.seed, test) #--------------_________________-----------------------------------
    else:                                       # OpenAi Gym environment
        import gym
        from gym import spaces
        env = gym.make(environment)
        editEnvFromConfig(env=env, filename=args.fileini)               
        if (isinstance(env.action_space, gym.spaces.box.Box)):
            from policy import GymPolicy
            policy = GymPolicy(env, args.fileini, args.seed, test)      # with continuous action space
        else:
            print("NO Env created")
            sys.exit()
    
    policy.environment = environment # only for getting input space right I think
    
    # Create the algorithm class
    if (algoname =='OpenAI-ES'):
        if args.workers > 1:
            from openaiesp import Algo
        else:
            from openaies import Algo
    elif (algoname == 'SSS'):
        from sss import Algo
    elif (algoname == 'coevo'):
        from coevo import Algo
    elif (algoname == 'coevo2'):
        from coevo2 import Algo
        
    algo = Algo(env, policy, args.seed, args.fileini, args.folder)


    if args.workers > 1:
        algo.setProcess(args.workers, comm, rank)   # Initialize the variables

    if (test > 0):
        # test a policy
        print("Run Test: Environment %s " % (environment))
        algo.test(args.genofile)
    else:
        # run evolution
        if (args.seed != 0):
            print("Run Evolve: Environment %s Seed %d Nreplications %d" % (environment, args.seed, args.nreplications))
            for r in range(args.nreplications):
                algo.run()
                algo.seed += 1
                policy.seed += 1
                algo.reset()
                policy.reset()
                if args.workers > 1:
                    algo.setProcess(args.workers, comm, rank)
        else:
            print("\033[1mPlease indicate the seed to run evolution\033[0m")

if __name__ == "__main__":
    main(sys.argv)