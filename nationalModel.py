"""
Author: Helge Bergo
Date: March 2021
File: nationalModel.py

This script contains the national model, building on model.py. 
"""

import random
import time
import numpy as np

from parameters import *
import classes
import model
import modelFunctions
import modelUtilities
import nationalModelFunctions


def dailyCommuterSpread(attrs, day, parameters):
    for node in attrs.values():
        if hasattr(node, 'missingHome') and not node.sick:
            if random.random() < parameters.commuter_prevalence:
                infectCommuter(node, day, parameters)


def infectCommuter(node, day, parameters):
    node.state = 'E'
    node.lastDay = day
    node.infAnc = ['mun', 'mun', day]
    node.virus = SARS_CoV_2()
    node.nextDay = 1 + np.random.poisson(node.virus.duration['I-E'])


def municipalityDay(municipality, parameters, day):
    cont = 0

    infectedList = {}
    dailyInfected = 0
    for layer in municipality.layers:
        infectedList[layer] = 0

        if (municipality.layers[layer].open) and (municipality.layers[layer].name not in ['R','C']): 
            for clique in municipality.layers[layer]:
                if clique.open & clique.hasCases(): 
                    infs = model.cliqueDay(clique, layer, parameters, day)
                    infectedList[layer] += len(infs)
                    dailyInfected += len(infs)
    
    infectedList['R'] = model.randomLayerSpread(municipality.layers['R'].cliques[0], parameters, day)
    dailyInfected += infectedList['R']
    
    for node in municipality.attrs.values():
        if node.sick or (node.state=='E'):
            node.stateFunction()(node.virus.probability, day)
            cont = True
    
    return cont, infectedList, dailyInfected


def testing(municipality, parameters, day):
    tests = 0
    testRules = parameters.testRules
    if testRules['strat'] != 'Symptomatic':
            if testRules['mode'] == 'FullHH':
                for pool in municipality.pools:
                    if (day % testRules['freq']) == pool.testDay:
                        pool.testAndQuarantine(parameters, testRules['fnr'], testRules['fpr'])
                        tests += len(pool)
            if testRules['mode'] == 'Adults':
                for pool in municipality.pools:
                    if (day % testRules['freq']) == pool['testDay']:
                        pool.testAndQuarantineAdults(parameters, testRules['fnr'], testRules['fpr'], testRules['age'])
                        tests += len(pool)
    else:
        for node in municipality.attrs.values():
            if node.state=='Is' and node.lastDay==(day-2):
                node.individualTestAndQuarantine(layers, day, parameters)
                tests += 1
    return tests


def fullRun(municipalities, parameters):
    '''Full run of the national model'''
    stateLog = {}
    dailyR = {}
    timeUsed = []
    cont = 1
    day = 0
    
    for municipality in municipalities:
        stateLog[municipality.name] = []
    
    while cont and (day < parameters.runDays):
        day += 1
        cont = 0
        dayTime = time.time()
        for municipality in municipalities:
            cont_, linfs, dailyInfected = municipalityDay(municipality, parameters, day)

            if parameters.testRules:
                tests = testing(municipality, parameters, day)
            dailyCommuterSpread(municipality.attrs, day, parameters)

            stateLog[municipality.name].append(modelFunctions.countStates(municipality.attrs, stateList))
            
            if cont_:
                cont += 1
        timeUsed.append(time.time() - dayTime)
        if parameters.printResults:
            modelUtilities.printProgress(day, parameters.runDays, timeUsed, bar_length=50)
        
    for municipality in municipalities:
        try:
            dailyR[municipality.name] = modelFunctions.getDailyR(municipality.attrs, parameters.runDays)
        except (ValueError, TypeError) as e:
            dailyR[municipality.name] = np.full([parameters.runDays-1,1], np.nan)
    
    attrs = {}
    for municipality in municipalities:
        for key, node in municipality.attrs.items():
            attrs[key] = node
    
    dailyR[parameters.region] = modelFunctions.getDailyR(attrs, parameters.runDays)
    
    return stateLog, dailyR


def initRun(municipalities, parameters, treshold):
    '''Initial run of the national model, to be used with timedRun() afterwards.'''
    stateLog, infectedLog, infectedLogByLayer = {}, {}, {}

    cont = 1
    day = 0
    timeUsed = []

    for municipality in municipalities:
        stateLog[municipality.name] = []
        # infectedLog[municipality.name] = []
        # infectedLogByLayer[municipality.name] = []
    
    while cont:
        day += 1
        dayTime = time.time()
        for municipality in municipalities:
            cont_, linfs, dailyInfected = municipalityDay(municipality, parameters, day)

            if parameters.testRules:
                tests = testing(municipality, parameters, day)
            
            stateLog[municipality.name].append(modelFunctions.countStates(municipality.attrs, stateList))
            #infectedLog[municipality.name].append(dailyInfected)
            #infectedLogByLayer[municipality.name].append(linfs)
        
        Is = sum([s[-1]['Is'] for s in stateLog.values()])
        E = sum([s[-1]['E'] for s in stateLog.values()])
        if Is > treshold:
            cont = False
        elif E < Is and day > 20:
            raise Exception('Too few infected, simulation stopped.')
        
        timeUsed.append(time.time() - dayTime)
        if parameters.printResults:
            modelUtilities.printProgress(day, parameters.runDays, timeUsed, bar_length=20)

    return stateLog, infectedLog, infectedLogByLayer, day


def timedRun(municipalities, parameters, day, runDays):
    '''Timed run of the national model, to be used after initRun().'''
    stateLog = {}
    for municipality in municipalities:
        stateLog[municipality.name] = []
    
    timeUsed = []
    
    cont = 1
    endDay = runDays + day
    
    while cont and (day < endDay):
        day += 1
        cont = 0
        dayTime = time.time()
        for municipality in municipalities:
            
            cont_, linfs, dailyInfected = municipalityDay(municipality, parameters, day)
            
            if parameters.testRules:
                tests = testing(municipality, parameters, day)
            
            dailyCommuterSpread(municipality.attrs, day, parameters)

            stateLog[municipality.name].append(modelFunctions.countStates(municipality.attrs, stateList))
            
            if cont_:
                cont += 1

        timeUsed.append(time.time() - dayTime)
        if parameters.printResults:
            modelUtilities.printProgress(day, endDay, timeUsed, bar_length=30)

    return stateLog


def municipalitySetup(layers, attrs, parameters, municipality):
    [n.generateActivity(parameters) for n in attrs.values()]
    for node in attrs.values():
        node.activity = min(node.activity, 100)
    
    if not parameters.seedMunicipality or municipality == parameters.seedMunicipality:
        model.seedState(attrs, parameters)
    
    modelFunctions.setStrategy(layers, attrs, parameters)
        
    municipality = classes.Municipality(municipality, layers, attrs)

    return municipality


def nationalModelSetup(parameters, region='trondelag'):
    parameters.municipalityList = nationalModelFunctions.getMunicipalityList(region)
    nationalLayers, nationalAttrs = nationalModelFunctions.buildNationalLayers(parameters.municipalityList, parameters)

    parameters.inputVector = modelFunctions.convertVector(parameters.strategy)
    parameters.p = modelFunctions.setInfectionProbabilities(
        parameters.inputVector, SARS_CoV_2.probability, parameters)
    
    municipalities = []
    for (municipality, layers), attrs in zip(nationalLayers.items(), nationalAttrs.values()):
        municipality = municipalitySetup(layers, attrs, parameters, municipality)
        municipalities.append(municipality)
    
    return municipalities, parameters


def runNationalModel(parameters):
    municipalities, parameters = nationalModelSetup(parameters)
    stateLog, dailyR = fullRun(municipalities, parameters)
    modelUtilities.savePickle((stateLog, dailyR), 'latest_sim', folder='')
    
    return stateLog, dailyR


def main():
    parameters = Parameters(
        prevalence=0.005,
        seedMunicipality = '',
        runDays=20,
        printResults=True
    )
    parameters.municipalityList = nationalModelFunctions.getMunicipalityList()
    parameters.municipalityList = nationalModelFunctions.getMunicipalityList('trondelag')
    stateLog, infLog, infLogByLayer = runNationalModel(parameters)


if __name__ == '__main__':
    main()
