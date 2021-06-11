"""
Author: Helge Bergo
Date: June 2021
File: createRun.py

Script for running the simulations in Python.
"""

import sys
import copy
import time
import os
import pickle
import pandas as pd

from nationalModel import *


def createFilename(mutationChance, runID, frac, region, nameAppend=''):
    return f'./results/simulations/StateLogMutation{mutationChance}Commuter{frac}Run{runID}-{region}{nameAppend}.pkl'


def isSimulated(filename):
    return os.path.isfile(filename)


def initAndTimedSim(mutationChance, runID, commuterFracs, region='trondelag', overwrite=False, nameAppend=''):
    start_time = time.time()
    print(f'  Run {runID}; Initialising model... ', end='\r', flush=True)

    existingFiles = 0
    for frac in commuterFracs:
        filename = createFilename(mutationChance, runID, frac, region, nameAppend)
        existingFiles += int(isSimulated(filename))
    if existingFiles == len(commuterFracs):
        print(f'  Run {runID}; Finished in {(time.time()-start_time)/60:.1f} min.   ')
        return
    
    parameters = Parameters(
        n=100,
        seedMunicipality='Trondheim',
        printResults=False,
        mutationChance=mutationChance
    )
    municipalities, parameters = nationalModelSetup(parameters, region)
    
    stateLog1, infLog1, infLogByLayer1, i1 = initRun(municipalities, parameters, treshold=1000)
    print(f'  Run {runID}; Initial run finished in {i1} days...       ', end='\r', flush=True)

    for frac in commuterFracs:
        filename = createFilename(mutationChance, runID, frac, region, nameAppend)
        
        if not overwrite and os.path.isfile(filename):
            continue
        
        municipalitiesFork = copy.deepcopy(municipalities)
        print(f'  Run {runID}; Starting timed run, frac: {frac}...   ', end='\r', flush=True)

        [m.setTestRules(parameters) for m in municipalities]
        parameters.commuterFraction = frac
        
        testTime = 30
        stateLog = timedRun(municipalitiesFork, parameters, i1, testTime)
        pickle.dump(stateLog, open(filename, 'wb'))
        print(f'  Run {runID}; Completed frac: {frac}...              ', end='\r', flush=True)
    
    print(f'  Run {runID}; Finished in {(time.time()-start_time)/60:.1f} min.   ', flush=True)


def fullSim(mutationChance, runID, runParams, overwrite=False):
    start_time = time.time()
    print(f'  Mutation {mutationChance:.2f}; Initialising model...   ', end='\r', flush=True)

    parameters = Parameters(
        runDays=60,
        prevalence=runParams['prevalence'],
        seedMunicipality=runParams['seed'],
        printResults=False,
        mutationChance=mutationChance,
        region = runParams['region']
    )
    
    seed = f'Seed{runParams["seed"]}' if runParams['seed'] else ''
        
    for frac in runParams['commuterFracs']:
        filename = createFilename(mutationChance, runID, frac, runParams['region'], seed)
        if not runParams['overwrite'] and isSimulated(filename):
            continue
        try:
            pickle.dump(0, open(filename, 'wb')) # create temp file
            
            parameters.commuterFraction = frac
            municipalities, parameters = nationalModelSetup(parameters, runParams['region'])
            
            print(f'  Mutation {mutationChance:.2f}; Fraction {frac}; Full run...       ', end='\r', flush=True)
            
            stateLog, dailyR = fullRun(municipalities, parameters)
            
            if runParams['createNetwork']:
                nationalModelFunctions.createEdgeNetwork(municipalities, filename)
            
            pickle.dump(stateLog, open(filename, 'wb'))
            pickle.dump(dailyR, open(filename.replace('StateLog','R'), 'wb'))
            
            print(f'  Run {runID}; Fraction {frac}; Completed...              ', end='\r', flush=True)
            
        except KeyboardInterrupt: # delete temporary file if simulation is interrupted
            os.remove(filename)
            sys.exit(0)
    
    print(f'  Mutation {mutationChance:.2f}; Finished in {(time.time()-start_time)/60:.1f} min.        ', flush=True)


def runSimulations(func=fullSim):
    start_time = time.time()
    runParams = {
        'runIDs': range(102,103),
        'mutationChances':  [0.0, 0.25, 0.5, 0.75, 1.0],
        'commuterFracs':    [0.0, 0.25, 0.5, 0.75, 1.0],
        'region': 'trondelag',
        'seed':'',
        'prevalence':0.005,
        'overwrite':False,
        
        'createNetwork':False
    }
    n = len(runParams['runIDs']) * len(runParams['mutationChances']) * len(runParams['commuterFracs'])
    print(f'--- Starting {n} simulations; Expect to run ~{1.5*n/60:.1f} hours ---')
    
    for runID in runParams['runIDs']:
        print(f'Run: {runID}')
        for mutationChance in runParams['mutationChances']:
            func(mutationChance, runID, runParams)
    
    print(f'--- Simulations finished in {(time.time()-start_time)/60:.1f} min ---')
    createResultFile(runParams)


def runStandardSimulation():
    start_time = time.time()
    runParams = {
        'runIDs': range(1,11),
        'mutationChances':  [0.0],
        'commuterFracs':    [1.0],
        'region': 'trondelag',
        'seed':'',
        'prevalence':0.005,
        'overwrite':False,
        
        'createNetwork':True
    }
    for runID in runParams['runIDs']:
        print(f'Run: {runID}')
        for mutationChance in runParams['mutationChances']:
            fullSim(mutationChance, runID, runParams)
    
    print(f'--- Simulations finished in {(time.time()-start_time)/60:.1f} min ---')
    createResultFile(runParams)


def runAllSimulations():
    start_time = time.time()
    runParams = {
        'runIDs': range(1,21),
        'mutationChances':  [0.0, 0.25, 0.5, 0.75, 1.0],
        'commuterFracs':    [0.0, 0.25, 0.5, 0.75, 1.0],
        'region': 'trondelag',
        'seed': '',
        'prevalence': 0.005,
        'overwrite': False,
        'createNetwork': False
    }
    seeds = ['','Trondheim','Namsos','Malvik','Frøya','Stjørdal']
    
    for seed in seeds:
        runParams['seed'] = seed
        print(f'-- Seed: {seed} --')
        if seed in ['Namsos','Malvik','Frøya','Stjørdal']:
            runParams['commuterFracs'] = [1.0]
        else:
            runParams['commuterFracs'] = [0.0, 0.25, 0.5, 0.75, 1.0]
        for runID in runParams['runIDs']:
            print(f'Run: {runID}')
            for mutationChance in runParams['mutationChances']:
                fullSim(mutationChance, runID, runParams)
        try:
            createResultFile(runParams)
        except Exception:
            pass
    print(f'--- Simulations finished in {(time.time()-start_time)/60:.1f} min ---')


def createResultFile(runParams):
    '''Creates a txt-file with every daily variable
    for every run for each municipality.'''
    
    seed = f'Seed{runParams["seed"]}' if runParams['seed'] else ''
    filename =  (f'./results/summaries/'
                 f'States{len(runParams["runIDs"])}'
                 f'Prev{runParams["prevalence"]}'
                 f'{runParams["region"]}{seed}.txt'
                )
    filenameR = filename.replace('States','R')
    
    rFile = open(filenameR, 'w').close() # overwrite file
    stateFile = open(filename, 'w').close()
    rFile = open(filenameR, 'a')
    stateFile = open(filename, 'a')
    
    n = len(runParams['mutationChances']) * len(runParams['commuterFracs']) * len(runParams['runIDs'])
    i = 1
    
    for mutationChance in runParams['mutationChances']:
        for frac in runParams['commuterFracs']:
            for runID in runParams['runIDs']:
                stateLogFile = f'./results/simulations/StateLogMutation{mutationChance}Commuter{frac}Run{runID}-{runParams["region"]}{seed}.pkl'
                stateLog = pickle.load(open(stateLogFile, 'rb'))
                r = pickle.load(open(stateLogFile.replace('StateLog','R'), 'rb'))
                rdf = pd.DataFrame(r).round(2)
                rdf = rdf.assign(commuter_fraction=frac, mutation_chance=mutationChance, 
                                 run=runID, day=range(1, len(rdf)+1))
                
                rdf.to_csv(rFile, mode='a', header=rFile.tell()==0, index=False)
                
                for key, value in stateLog.items():
                    states = pd.DataFrame(value)
                    states = states.assign(municipality=key, commuter_fraction=frac,
                                           mutation_chance=mutationChance, run=runID, 
                                           day=range(1, len(value)+1))
                    states.to_csv(stateFile, mode='a', header=stateFile.tell()==0, index=False)
                print(f'\r{i}/{n}', end = '')
                i += 1
                
    rFile.close()
    stateFile.close()
    
    print(f'\rSaved summary files!')


if __name__ == '__main__':
    runStandardSimulation()
