"""
Author: Helge Bergo
Date: February 2021
File: modelFunctions.py

This module contains utility functions used in model.py, mostly used in the
setup and finish of the simulation.
"""

import random
import copy
import numpy as np

from parameters import *
import classes


def readModel(parameters):
    '''Builds household/school/work structure from file'''
    ageFile = 'data/idAndAge_{}.txt'.format(parameters.cityName)
    cliqueFile = 'data/socialNetwork_{}.txt'.format(parameters.cityName)

    f = open(ageFile)
    nodeID = -1
    attrs = {}

    for line in f:
        line = line.rstrip().split(';')
        nodeID = line[0]
        age = int(line[1])

        node = classes.Person(nodeID, age)
        attrs[nodeID] = node

    f.close()

    layers = {'BH':{}, 'BS':{}, 'US':{}, 'VS':{}, 'W':{}, 'HH':{}, 'NH':{}, 'R':{}}
    translations = {'Kindergarten': 'BH', 'PrimarySchool': 'BS', 'Household':'HH', 'SecondarySchool': 'US',
                    'UpperSecondarySchool': 'VS', 'Workplace': 'W', 'NursingHome':'NH'}

    for layer in layers:
        layers[layer] = classes.Layer(layer)


    f = open(cliqueFile)
    for line in f:

        splitLine = line.rstrip().split(';')

        if (splitLine[1] != '') & (splitLine[0].split('_')[0] != 'Commuters'):
            clique = classes.Clique()

            for i in splitLine[1:]:
                if i.isdigit():
                    clique.nodes.append(attrs[i])

            cliqueName = translations[splitLine[0]]
            if cliqueName == 'NH':
                for node in clique:
                    if node.age > 70:
                        node.inNursing = True

            layers[cliqueName].addClique(clique)

    f.close()

    for clique in layers['W'].cliques:
        clique.openRating = random.random()

    layers['R'].cliques = [list(attrs.values())]

    return layers, attrs


def convertVector(inputVector):
    newVec = {}
    for layer in inputVector:
        if layer == 'S':
            newVec['BH'] = inputVector[layer]
            newVec['BS'] = inputVector[layer]
            newVec['US'] = inputVector[layer]
            newVec['VS'] = inputVector[layer]
        else:
            newVec[layer] = inputVector[layer]
    return newVec


def setInfectionProbabilities(inputVector, probs, parameters):
    """Calculate new infection probabilities based on
    quarantine factor and mutation chance.
    """
    newP = copy.deepcopy(probs)

    # Change from quarantine factor
    newP['inf']['dynR'] = inputVector['R'] * probs['inf']['dynR']
    # newP['inf']['R'] = inputVector['R'] * probs['inf']['R']

    # Change from mutation factor
    mutation = 1 + parameters.mutationChance
    for key in newP['inf'].keys():
        newP['inf'][key] = newP['inf'][key] * mutation

    return newP


def setStrategy(layers, attrs, parameters):
    if 'poolSelection' in parameters.inVec:
        if layers['poolSelection'] == 'largeHH':
            genTestPoolsHHaboveSize(layers, attrs, 50000, 3)

    layers['W'].open = bool(parameters.inputVector['W'])
    layers['R'].open = bool(parameters.inputVector['R'])

    for layer in ['BH', 'BS', 'US', 'VS']:
        layers[layer].open = bool(parameters.strategy['S'])

        for school in layers[layer].cliques:
            openAllGrades(school, attrs)
            closeGradesAbove(school, parameters.strategy['S'], attrs)

    workFrac(layers, float(parameters.inputVector['W']))

    layers['NH'].open = True
    layers['HH'].open = True
    layers['R'].open = True


def setTestRules(parameters, layers, attrs):
    testing = parameters.testing
    pools = []

    if testing:
        capacity = int(len(attrs) * testing['capacity']/100)
        if not capacity:
            capacity = testing['capacity']
        parameters.testRules['strat'] = testing['testStrat']
        if testing['testStrat'] in ['TPHT', 'TPHTA']:
            pools = genTestPoolsHHaboveSize(layers, attrs, capacity, testing['cutoff'])
            if 'Stud' in testing:
                pools = genTestPoolsStudents(layers, attrs, testing['Stud']['capacity'], testing['Stud']['cutoff'])
        if testing['testStrat'] in ['TPHT2']:
            if 'compliance' in testing:
                pools = genTestPoolsTopFraction(layers, attrs, capacity, testing['compliance'])
            else:
                pools = genTestPoolsTopFraction(layers, attrs, capacity)
            parameters.testRules['mode'] = 'FullHH'
        if testing['testStrat'] in ['TPHTA2']:
            pools = genTestPoolsTopFraction(layers, attrs, capacity)
            parameters.testRules['mode'] = 'Adults'
            parameters.testRules['age'] = testing['age']
        if testing['testStrat'] in ['RPHT']:
            pools = genTestPoolsRandomHH(layers, attrs, capacity)
            parameters.testRules['mode'] = 'FullHH'

        if testing['testStrat'] in ['NH']:
            pools = genTestPoolsNHPersonnel(layers, attrs)
            parameters.testRules['mode'] = 'FullHH'
        if testing['testStrat'] in ['NHTPHT']:
            pools = genTestPoolsNHPersonnel(layers, attrs)
            pools.extend(genTestPoolsHHaboveSize(layers, attrs, capacity, testing['cutoff']))
            parameters.testRules['mode'] = 'FullHH'

        if testing['testStrat'] in ['RIT']:
            pools = genTestPoolsRandom(layers, attrs, capacity)
            parameters.testRules['mode'] = 'FullHH'

        if testing['testStrat'] in ['TPHTA']:
            parameters.testRules['mode'] = 'Adults'
            parameters.testRules['age'] = testing['age']
        if testing['testStrat'] in ['TPHT', 'RPHT']:
            parameters.testRules['mode'] = 'FullHH'
        if 'freq' in testing:
            parameters.testRules['freq'] = testing['freq']
        else:
            parameters.testRules['freq'] = 7

        for pool in pools:
            pool.testDay = random.randint(0, parameters.testRules['freq']-1)

        if 'fnr' in testing:
            parameters.testRules['fnr'] = testing['fnr']
        else:
            parameters.testRules['fnr'] = 0
        if 'fpr' in testing:
            parameters.testRules['fpr'] = testing['fpr']
        else:
            parameters.testRules['fpr'] = 0

    return pools


def genTestPoolsRandomHH(layers, attrs, capacity):
    return random.sample(layers['HH'].cliques, capacity)


def genTestPoolsRandom(layers, attrs, capacity):
    # l = [{'nodes': [node]} for node in random.sample(list(attrs.keys()), capacity)]
    nodes = random.sample(list(attrs.values()), capacity)
    cliques = []
    for node in nodes:
        clique = classes.Clique([node])
        cliques.append(clique)
    return cliques


def genTestPoolsHHaboveSize(layers, attrs, capacity, size):
    i = 0
    validHHs = []
    for hh in layers['HH'].cliques:
        if len(hh.nodes) > size:
            validHHs.append(hh)
    return random.sample(validHHs, capacity)


def genTestPoolsStudents(layers, attrs, capacity, size):
    i = 0
    validHHs = []
    for hh in layers['HH'].cliques:
        if (len(hh.nodes) > size) & (hh.nodes[0][0] == 's'):
            validHHs.append(hh)
    return random.sample(validHHs, capacity)


def genTestPoolsNHPersonnel(layers, attrs):
    testPool = []
    for nh in layers['NH'].cliques:
        clique = {'nodes': []}
        for node in nh.nodes:
            if attrs[node].inNursing == False:
                clique.nodes.append(node)
        testPool.append(clique)
    return testPool


def genTestPoolsTopFraction(layers, attrs, capacity, compliance=1.0):
    sortedHHs = sorted(layers['HH']['cliques'], key = getHHsize, reverse = True)
    if (compliance == 1.0):
        return sortedHHs[:capacity]
    else:
        i = 0
        j = 0
        pools = []
        while i < capacity:
            if random.random() < compliance:
                pools.append(sortedHHs[j])
                i += 1
            j += 1
        return pools


def getHHsize(hh):
    return len(hh.nodes)

def genVaccPoolAllAboveAge(attrs, layers, age):
    pool = []
    for node in attrs:
        if attrs[node]['age'] > age:
            pool.append(node)
    random.shuffle(pool)
    return pool


def openAllGrades(school, attrs):
    for node in school:
        node.present['VS'] = True
        node.present['VS'] = True
        node.present['BS'] = True
        node.present['US'] = True
        node.present['BH'] = True


def closeGradesAbove(school, age, attrs):
    for node in school.nodes:
        if node.age > age:
            node.present['VS'] = False
            node.present['BS'] = False
            node.present['US'] = False
            node.present['BH'] = False
    for node in school:
        if node.age > 19:
            if age > 15:
                node.present['VS'] = True
            if age > 12:
                node.present['US'] = True
            if age > 5:
                node.present['BS'] = True
            if age > 0:
                node.present['BH'] = True


def workFrac(layers, frac):
    '''Opens all workplaces with a high enough openRating.'''
    for clique in layers['W'].cliques:
        clique.open = (clique.openRating < frac)


def countStates(attrs, stateList):
    '''Count through all persons and save states in a dict.'''
    count = {}
    for s in stateList:
        count[s] = 0
    for node in attrs.values():
        count[node.state] += 1

    return count


def getDailyR(attrs, runDays):
    """New version of daily R calculations, using actual descendants of recovered
    individuals instead."""
    
    infsCaused = []
    recDay = []
    startDay =[]
    for node in attrs.values():
        if node.state == 'R':
            infsCaused.append(len(node.infDesc))
            recDay.append(node.lastDay)
            startDay.append(node.infDay)
    lastDay = runDays
    infsByRecDay = [[] for i in range(lastDay)]
    for i in range(len(recDay)):
        for j in range(startDay[i], recDay[i]):
            infsByRecDay[j].append(infsCaused[i])
    avgRByDay = [np.nanmean(infsByRecDay[i]) for i in range(lastDay)]
    
    return avgRByDay


def createEdgeNetwork(attrs):
    """Creates a simple edge network of all infected nodes that has spread 
    the disease. Not used at the moment, but could be useful in the future."""
    
    edges = ['ancestor','descendant','day','layer','municipality']
    for node in attrs.values():
        if len(node.infDesc) > 0:
            for desc in node.infDesc:
                edges.append(node.id_number, desc[0].id_number, 
                             desc[2], desc[1], node.municipality)
                
    return edges
