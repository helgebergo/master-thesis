"""
Author: Helge Bergo
Date: May 2021
File: run.py

Script for running the simulations in HUNT from the command line.
"""

import sys
import os
import pickle
import pandas as pd

from nationalModel import *

def isSimulated(filename):
    return os.path.isfile(filename)

def createFilename(mut, com, strat, prev, run, region, seed, name=''):
    if name == 'seeds':
        seed = f'seed{seed}'
    
    name = f'./results/simulations/States_Com{com}Mut{mut}P{prev}S{strat}-Run{run}-{region}{seed}.pkl'
    return name

def createSummaryFilename(name):
    filenameS = f'results/summaries/States_{name}.txt'
    filenameR = filenameS.replace('States','R')
    
    return filenameS, filenameR

def getSimulationCount(runParams, runs):
    n = len(runParams['commuters']) * len(runParams['mutations']) * len(
        runParams['strategies']) * len(runParams['prevalence']) * len(runParams['seed']) * len(runs)
    return n


def fullSim(runParams, run, name, overwrite=False):
    for mutation in runParams['mutations']:
        for commuter in runParams['commuters']:
            for strat in runParams['strategies']:
                for prevalence in runParams['prevalence']:
                    for seed in runParams['seed']:
                        filename = createFilename(mutation, commuter, strat, 
                                                  prevalence, run, 
                                                  runParams['region'], seed, name)
                        
                        parameters = Parameters(
                            runDays=60,
                            mutationChance=mutation,
                            commuterFraction=commuter,
                            strategy={'S': 12, 'W': 1, 'R': strat},
                            prevalence=prevalence,
                            region=runParams['region'],
                            seedMunicipality=seed,
                            infected=100 if name == 'seed' else 0
                        )
                        
                        if not overwrite and isSimulated(filename):
                            continue
                        try:
                            pickle.dump(0, open(filename, 'wb')) # create temp file
                            
                            municipalities, parameters = nationalModelSetup(
                                parameters, runParams['region'])
                            
                            states, r = fullRun(municipalities, parameters)
                            
                            pickle.dump(states, open(filename, 'wb'))
                            pickle.dump(r, open(filename.replace('States','R'), 'wb'))
                            
                        except KeyboardInterrupt: # delete temp file if simulation is interrupted
                            os.remove(filename)
                            sys.exit(0)


def createResultFile(runParams, name, runs):
    filenameS, filenameR = createSummaryFilename(name)
    
    open(filenameS, 'w').close() # overwrite file
    open(filenameR, 'w').close()
    fileS = open(filenameS, 'a')
    fileR = open(filenameR, 'a')

    n = getSimulationCount(runParams, runs)
    i = 1
    
    for mutation in runParams['mutations']:
        for commuter in runParams['commuters']:
            for strat in runParams['strategies']:
                for prevalence in runParams['prevalence']:
                    for seed in runParams['seed']:
                        for run in runs:
                            filename = createFilename(mutation, commuter, strat, prevalence, 
                                                      run, runParams['region'], seed)
                            states = pickle.load(open(filename, 'rb'))
                            r = pickle.load(open(filename.replace('States','R'), 'rb'))
                            rdf = pd.DataFrame(r).round(2)
                            rdf = rdf.assign(commuter_fraction=commuter, 
                                             mutation_chance=mutation, 
                                             run=run, strategy=strat, 
                                             prevalence=prevalence, seed=seed,
                                             day=range(1, len(rdf)+1))
                    
                            rdf.to_csv(fileR, mode='a', header=fileR.tell()==0, 
                                       index=False)
                            
                            for key, value in states.items():
                                states = pd.DataFrame(value)
                                states = states.assign(municipality=key, 
                                                       commuter_fraction=commuter,
                                                       mutation_chance=mutation, run=run, 
                                                       prevalence=prevalence, seed=seed, strategy=strat,
                                                       day=range(1, len(value)+1))
                                states.to_csv(fileS, mode='a', header=fileS.tell()==0, 
                                              index=False)
                            print(f' {i}/{n} ', end='\r')
                            i += 1


def getParams():
    params = {
        'default': {
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.005],
            'region':   'trondelag',
            'seed':             ['']
        },
        'commuters': {
            'commuters':    [0.0, 0.25, 0.50, 0.75, 1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.005],
            'region':   'trondelag',
            'seed':             ['']
        }, 
        'mutations': {
            'commuters':    [1.0],
            'mutations':    [0.0, 0.25, 0.50, 0.75, 1.0],
            'strategies':     [0.25],
            'prevalence':   [0.005],
            'region':   'trondelag',
            'seed':             ['']
        },
        'strategies': {
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':   [0.0, 0.05, 0.1, 0.20, 0.25],
            'prevalence':   [0.005],
            'region':   'trondelag',
            'seed':             ['']
        },
        'prevalence':{
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.05, 0.005, 0.0005, 0.00005],
            'region':   'trondelag',
            'seed':             ['']
        },
        'seeds':{
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.005],
            'region':   'trondelag',
            'seed':    ['Trondheim', 'Stjørdal', 'Namsos', 
                        'Oppdal', 'Frøya', 'Røyrvik','']
        },
        'seed_v_prevalence':{
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.05, 0.005, 0.0005, 0.00005],
            'region':   'trondelag',
            'seed':    ['Trondheim', 'Stjørdal', 'Namsos', 
                        'Oppdal', 'Frøya', 'Røyrvik','']
        },
        'fractional':{
            'commuters':    [0.0, 1.0],
            'mutations':    [0.0, 1.0],
            'strategies':     [0.1, 0.25],
            'prevalence':   [0.005, 0.0005],
            'region':   'trondelag',
            'seed':    ['']
        },
        'commuters_osloviken': {
            'commuters':    [0.0, 0.25, 0.50, 0.75, 1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.005],
            'region':   'osloviken',
            'seed':             ['']
        }, 
        'norge':{
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':     [0.25],
            'prevalence':   [0.005],
            'region':   'norge',
            'seed':             ['']
        },
        'norge_strategy':{
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':   [0.0, 0.05, 0.1, 0.20, 0.25],
            'prevalence':   [0.005],
            'region':   'norge',
            'seed':             ['']
        },
        'norge_commuters':{
            'commuters':    [0.0, 0.50, 1.0],
            'mutations':    [0.0],
            'strategies':   [0.25],
            'prevalence':   [0.005],
            'region':   'norge',
            'seed':             ['']
        },
        'norge_oslo':{
            'commuters':    [1.0],
            'mutations':    [0.0],
            'strategies':   [0.25],
            'prevalence':   [0.005],
            'region':   'norge',
            'seed':             ['oslo']
        }
    }
    
    return params


def run(run, simulate=True, overwrite=False, saveSummary=False):
    params = getParams()
    runs = range(1,101)
    
    for name, runParams in params.items():
        if simulate:
            fullSim(runParams, run, name, overwrite)
        if saveSummary:
            try:
                createResultFile(runParams, name, runs)
                print(f'Saved {name}')
            except FileNotFoundError:
                print(f'Failed to create {name} summary!')
                [os.remove(f) for f in createSummaryFilename(name)]


if len(sys.argv) > 1:
    run(sys.argv[1])
else:
    run(0, simulate=False, saveSummary=True)
