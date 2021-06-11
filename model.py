"""
Author: Helge Bergo
Date: February 2021
File: model.py

This script contains the main agent based model, and loads in classes, utilities and parameters to run the simulation. 
"""

import random, time
import numpy as np
from classes import *
from parameters import *
import modelFunctions
import modelUtilities


def initialiseModel(parameters):
    '''Create the layers and agents("attrs"). '''
    layers, attrs = modelFunctions.readModel(parameters)
    
    [n.generateActivity(parameters) for n in attrs.values()]
    
    seedState(attrs, parameters)
    
    return layers, attrs


def seedState(attrs, parameters):
    '''Set the state of n persons to be exposed.'''
    if parameters.n:
        n = min(parameters.n, len(attrs))
    else:
        n = int(len(attrs)*parameters.prevalence)
    
    for node in random.sample(list(attrs.values()), n):
        node.state = 'E'
        node.lastDay = 0
        node.infAnc = ['init', 'init', 'init']
        node.virus = SARS_CoV_2()
        node.infDay = 0
        node.nextDay = 1 + np.random.poisson(node.virus.duration['I-E'])


def systemDay(layers, attrs, parameters, day):
    '''Daily pulse of the system.'''
    cont = 0

    infectedList = {}
    dailyInfected = 0
    for layer in layers:
        infectedList[layer] = 0

        if (layers[layer].open) and (layers[layer].name not in ['R','C']): 
            for clique in layers[layer]:
                if clique.open & clique.cases > 0: 
                    infs = cliqueDay(clique, layer, parameters, day)
                    infectedList[layer] += len(infs)
                    dailyInfected += len(infs)
    
    infectedList['R'] = randomLayerSpread(layers['R'].cliques[0], parameters, day)
    dailyInfected += infectedList['R']
    
    for node in attrs.values():
        if node.sick or (node.state=='E'):
            node.stateFunction()(node.virus.probability, day)
            cont = True

    tests = 0
    if parameters.testRules:
        tests = testing(layers, attrs, parameters, day)
    
    return cont, infectedList, dailyInfected


def cliqueDay(clique, layer, parameters, day):
    '''Runs infections over a day for a given clique'''
    susceptibleNodes, sickNodes = [], []

    for node in clique:
        if (node.state == 'S'):
            if (node.age > 10):
                susceptibleNodes.append(node)
            else:
                if random.random() < 0.3:
                    susceptibleNodes.append(node)
        if node.sick and node.present[layer]:
            sickNodes.append(node)
    effP = 1
    for node in sickNodes:
        effP = effP * pow((1-node.virus.probability['inf'][layer]), node.relInfectivity)
    effP = 1 - effP
    
    newlyInfected = random.sample(susceptibleNodes, np.random.binomial(len(susceptibleNodes), effP))
    for node in newlyInfected:
        ancestor = random.choices(sickNodes, weights=[node.relInfectivity for node in sickNodes], k=1)[0]
        node.infectNode(ancestor, layer, day, parameters)
    
    return newlyInfected


def randomLayerSpread(clique, parameters, day):           
    '''Random layer spread'''                                                                           
    effP = parameters.p['inf']['dynR']
    sickNodes = []                                                                                                                   
    prevalence = 0

    for node in clique:
        if node.sick and node.present['R']:
            act = min(random.randint(0, node.activity), len(clique))
            if hasattr(node, 'municipality_commute'):
                act = int(act/2)
            prevalence += act * node.relInfectivity
            sickNodes.append(node)
    
    prevalence = float(prevalence)/len(clique)                                                                                        
    infs = 0         
    
    for node in clique:
        if node.state=='S' and node.present['R']:
            act = min(random.randint(0, node.activity), len(clique))
            if hasattr(node, 'municipality_commute'):
                act = int(act/2)
            if random.random() < (1-pow(1-effP*prevalence, act)):
                ancestor = random.choice(sickNodes)
                node.infectNode(ancestor, 'R', day, parameters)                                                        
                infs += 1    
    return infs


def testing(layers, attrs, parameters, day):
    tests = 0
    testRules = parameters.testRules
    if testRules['strat'] != 'Symptomatic':
            if testRules['mode'] == 'FullHH':
                for pool in testRules['pools']:
                    if (day % testRules['freq']) == pool.testDay:
                        pool.testAndQuarantine(parameters, testRules['fnr'], testRules['fpr'])
                        tests += len(pool)
            if testRules['mode'] == 'Adults':
                for pool in testRules['pools']:
                    if (day % testRules['freq']) == pool['testDay']:
                        pool.testAndQuarantineAdults(parameters, testRules['fnr'], testRules['fpr'], testRules['age'])
                        tests += len(pool)
    else:
        for node in attrs.values():
            if node.state=='Is' and node.lastDay==(day-2):
                node.individualTestAndQuarantine(layers, day, parameters)
                tests += 1
    return tests


def timedRun(attrs, layers, parameters, day):
    '''Run of the model for a given number of days'''
    stateLog, infectedLog, infectedLogByLayer = [], [], []
    timeUsed = []

    cont = 1
    endDay = day + parameters.runDays
    
    while cont and (day < endDay):
        day+=1
        dayTime = time.time() 
    
        cont, linfs, dailyInfected = systemDay(layers, attrs, parameters, day)

        states_ = modelFunctions.countStates(attrs, stateList)
        # states_['T'] = tests
        stateLog.append(states_)
        infectedLog.append(dailyInfected)
        infectedLogByLayer.append(linfs)

        timeUsed.append(time.time() - dayTime)
        
        if parameters.printResults:
            modelUtilities.printProgress(day, parameters.runDays, timeUsed, bar_length=50)

    return stateLog, infectedLog, infectedLogByLayer


def initRun(attrs, layers, parameters, threshold):
    stateLog, infectedLog, infectedLogByLayer = [], [], []

    cont = 1
    day = 0

    while cont:
        day+=1
        # sys.stdout.flush()
        # sys.stdout.write(str(i)+'\r')
        
        cont, linfs, dailyInfected = systemDay(layers, attrs, parameters, day)

        stateLog.append(modelFunctions.countState(attrs, stateList))
        if stateLog[-1]['Is'] > threshold:
            cont = False
            
        infectedLog.append(dailyInfected)
        infectedLogByLayer.append(linfs)
        
    return stateLog, infectedLog, infectedLogByLayer, day


def modelSetup(parameters):
    layers, attrs = initialiseModel(parameters)

    parameters.inVec = modelFunctions.convertVector(parameters.strategy)
    parameters.testing = {'testStrat': 'TPHT', 'capacity':5000, 'cutoff': 3}
    
    parameters.p = modelFunctions.setStrategy(layers, attrs, parameters)
    parameters.testRules = modelFunctions.setTestRules(parameters.testing, layers, attrs)
    
    return layers, attrs, parameters


def modelSummary(stateLog, infLog, infLogByLayer, parameters, attrs):
    '''Print and save results (default: True)'''
    if parameters.saveResults:
        modelUtilities.saveModelResults(stateLog, infLogByLayer, parameters, attrs)


def runModel(parameters):
    layers, attrs, parameters = modelSetup(parameters)
    stateLog, infLog, infLogByLayer = timedRun(attrs, layers, parameters)
    modelSummary(stateLog, infLog, infLogByLayer, parameters, attrs)
    
    return stateLog, infLog, infLogByLayer


def main():
    parameters = Parameters(
        infected=100, 
        runDays=5,
        cityName='Trondheim',
        saveResults=True, 
        createNetwork=True,
        plotResults=True,
        mutations=True,
        mutationChance=0.2
    )
    stateLog, infLog, infLogByLayer = runModel(parameters)


if __name__ == '__main__':
    main()
