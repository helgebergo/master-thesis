'''
Author: Helge Bergo
Date: February 2021
File: createNationalModel.py

This module contains utility functions used in model.py, mostly used in the 
setup and finish of the simulation.
'''

import random, time, re
import os, sys 
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import classes
from parameters import *
import numpy as np
import pandas as pd

commuters = []
commuters_incoming = []


def readModel(municipality):
    '''Builds household/school/work structure from file'''
    folder_path = f'networkGeneration/output/{municipality}'
    ageFile = f'{folder_path}/idAndAge_{municipality}_1.txt'
    cliqueFile = f'{folder_path}/socialNetwork_{municipality}_1.txt'
    
    global commuters
    global commuters_incoming
    nodes = {}
    layers = {'BH':{}, 'BS':{}, 'US':{}, 'VS':{}, 'W':{}, 'HH':{}, 'NH':{}, 'R':{}, 'C':{}}
    for layer in layers:
        layers[layer] = classes.Layer(layer)
    translations = {'Kindergarten': 'BH', 'PrimarySchool': 'BS', 'Household':'HH', 'SecondarySchool': 'US', 
                    'UpperSecondarySchool': 'VS', 'Workplace': 'W', 'NursingHome':'NH', 'Commuters':'C'}

    # Create nodes with ID and age
    f = open(ageFile)
    for line in f:
        line = line.rstrip().split(';')
        nodeID = line[0]
        age = int(line[1])
        nodes[nodeID] = classes.Person(nodeID, age)
    f.close()

    # Create cliques and fill them with nodes    
    f = open(cliqueFile)
    for line in f:
        splitLine = line.rstrip().split(';')
        
        # Create commuter clique
        if 'Commuters' in splitLine[0]:
            cliqueName = 'C'
            municipality_commute = splitLine[0].split('_',1)[1].capitalize()
            
            cliques = next((c for c in layers['C'] if (c.commuteDestination in municipality_commute)), None)
            if cliques:
                clique = cliques
            else:
                clique = classes.Clique(municipality)
                clique.commuteDestination = municipality_commute
                layers[cliqueName].addClique(clique)
            for i in splitLine[1:]:
                nodes[i] = classes.Commuter(nodes[i], municipality, municipality_commute)
                clique.nodes.append(nodes[i])

        # Create regular clique
        elif splitLine[1] != '':
            cliqueName = translations[splitLine[0]]
            clique = classes.Clique(municipality)

            cliqueCommuters = []

            for i in splitLine[1:]:
                if i.isdigit():
                    clique.nodes.append(nodes[i])
                else: # if the clique has commuters
                    splitCommute = re.split('(\d+)',i)
                    municipality_home = splitCommute[0].capitalize()
                    nodeID = splitCommute[1]
                    cliqueCommuters.append((municipality_home, municipality, nodeID))
            if cliqueCommuters:
                clique.cliqueCommuters = cliqueCommuters

            if cliqueName == 'NH':
                for node in clique:
                    if node.age > 70:
                        node.inNursing = True

            layers[cliqueName].addClique(clique)
        for node in clique: 
            node.cliques.append(clique)

    f.close()

    for clique in layers['W'].cliques:
        clique.openRating = random.random()

    layers['R'].cliques = [list(nodes.values())]

    return layers, nodes


def placeCommuters_v2(nationalLayers):
    unplacedCommuters = set()
    placed = 0
    indexfails = set()
    destinationfails = set()

    for municipality in nationalLayers:
        for layer in nationalLayers[municipality].values():
            if layer.name not in ['C','HH']:
                for clique in layer:
                    if hasattr(clique, 'cliqueCommuters'):
                        for commuter in clique.cliqueCommuters:
                            home, destination, i = commuter
                            if home in nationalLayers.keys():
                                try:
                                    commuterClique = next(c for c in nationalLayers[home]['C'] if (c.commuteDestination in destination))
                                    commuterNode = commuterClique[int(i)]
                                    clique.nodes.append(commuterNode)           

                                    placed += 1           

                                    nationalLayers[destination]['R'].cliques.append(commuterNode)

                                except StopIteration:
                                    destinationfails.add(destination)
                                except IndexError:
                                    indexfails.add((municipality,home))
                                    # print(f'altså...{i} > {len(commuterClique.nodes)}')
                                # TODO fix activity level

                            else:
                                unplacedCommuters.add(home)

                            # add node to correct random layer, and fix activity
    
    print(f'{len(unplacedCommuters)} missing municipalities, {placed} placed commuters')
    print(f'destination fails: {destinationfails}')
    print(f'index fails:{indexfails}')

    return nationalLayers


def buildNationalModel():
    municipalityNamesFile = open("networkGeneration/populationData/kommuneNavnFixed2019.txt", "r", encoding='utf-8')
    municipalityNames = municipalityNamesFile.readlines()
    municipalityNamesFile.close()

    municipalitiesTrondheim = ['Trondheim','Klæbu','Malvik','Melhus','Midtre Gauldal','Orkdal','Skaun','Indre Fosen','Stjørdal'] 

    municipalitiesNotWorkingFile = open("networkGeneration/municipalitiesNotWorking.txt", "r", encoding='utf-8')
    municipalitiesNotWorking = municipalitiesNotWorkingFile.readlines()
    municipalitiesNotWorking = [m.replace('\n','') for m in municipalitiesNotWorking]
    municipalitiesNotWorkingFile.close()

    nationalLayers = {}
    nationalNodes = {}
    nationalCount = 0
    fails = []
    
    start_time = time.time()

    # for municipality in municipalityNames[0:50]:
    for municipality in municipalitiesTrondheim:
        municipality = municipality.replace("\n","").replace(" ","_")
        if municipality not in municipalitiesNotWorking:
            try:
                layers, nodes = readModel(municipality)
                for node in nodes:
                    national_nodes[nationalCount] = node
                    nationalCount += 1
                nationalLayers[municipality] = layers
            except:
                print(f'failed to load {municipality}')
                fails.append(municipality)
    
    print(f'read in municipalities with {len(fails)} fails.')

    nationalLayers = placeCommuters_v2(nationalLayers)

    # run_time = time.time() - start_time
    # print(f'{run_time/60:.2f} minutes')
    

    return nationalLayers, nationalNodes


if __name__ == '__main__':
    buildNationalModel()

