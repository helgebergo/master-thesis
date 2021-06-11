"""
Author: Helge Bergo
Date: March 2021
File: nationalModelFunctions.py

This file contains model functions for the national model. 
"""

import random
import re
from parameters import *
import classes


def readMunicipality(municipality):
    '''Builds clique and commuter structure from file'''
    folderPath = f'networkGeneration/output/{municipality}'
    ageFile = f'{folderPath}/idAndAge_{municipality}_1.txt'
    cliqueFile = f'{folderPath}/socialNetwork_{municipality}_1.txt'

    nodes = {}
    layers = {'BH':{}, 'BS':{}, 'US':{}, 'VS':{}, 'W':{}, 'HH':{}, 'NH':{}, 'R':{}, 'C':{}}
    for layer in layers:
        layers[layer] = classes.Layer(layer)

    translations = {'Kindergarten': 'BH', 'PrimarySchool': 'BS', 
                    'Household': 'HH', 'SecondarySchool': 'US',
                    'UpperSecondarySchool': 'VS', 'Workplace': 'W', 
                    'NursingHome': 'NH', 'Commuters': 'C'}

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
            municipalityCommute = splitLine[0].split('_',1)[1].capitalize()

            cliques = next((c for c in layers['C'] if (c.commuteDestination in municipalityCommute)), None)
            if cliques:
                clique = cliques
            else:
                clique = classes.Clique(municipality)
                clique.commuteDestination = municipalityCommute
                layers['C'].addClique(clique)
            for i in splitLine[1:]:
                nodes[i] = classes.Commuter(nodes[i], municipality, municipalityCommute)
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

    f.close()

    for clique in layers['W'].cliques:
        clique.openRating = random.random()

    layers['R'].cliques = [list(nodes.values())]

    return layers, nodes


def linkCommuters(nationalLayers, nationalAttrs, parameters):
    indexfails, destinationfails = set(), set()
    
    for municipality in nationalLayers:
        for layer in nationalLayers[municipality].values():
            if layer.name not in ['C','HH','R']:
                for clique in layer:
                    if hasattr(clique, 'cliqueCommuters'):
                        for commuter in clique.cliqueCommuters:
                            if random.random() < parameters.commuterFraction:
                                home, destination, i = commuter
                                if home in nationalLayers.keys():
                                    try:
                                        commuterClique = next(c for c in nationalLayers[home]['C'] if (
                                            c.commuteDestination in destination))
                                        commuterNode = commuterClique[int(i)]
                                    except StopIteration:
                                        destinationfails.add(destination)
                                    except IndexError:
                                        indexfails.add((municipality,home))
                                else:
                                    commuterNode = classes.Commuter(classes.Person(
                                        i, random.randint(20, 60)), home, destination)
                                    commuterNode.missingHome = True
                                clique.nodes.append(commuterNode)
                                nationalLayers[destination]['R'].cliques.append(commuterNode)
                        del clique.cliqueCommuters
    
    for municipality in nationalLayers:
        del nationalLayers[municipality]['C']
    
    return nationalLayers, nationalAttrs


def buildNationalLayers(municipalityList, parameters):
    nationalLayers, nationalNodes = {}, {}
    fails = []
    
    for municipality in municipalityList:
        try:
            layers, nodes = readMunicipality(municipality)
            nationalLayers[municipality] = layers
            nationalNodes[municipality] = nodes
        except Exception:
            fails.append(municipality)

    nationalLayers, nationalNodes = linkCommuters(nationalLayers, nationalNodes, parameters)

    return nationalLayers, nationalNodes


def getMunicipalityList(region=None):
    if region in ['osloviken', 'trondelag']:
        with open(f'./networkGeneration/{region}.txt', 'r') as f:
            municipalityList = [line.rstrip('\n') for line in f]
    
    elif region == 'Trondheim':
        municipalityList = ['Trondheim', 'Malvik', 'Melhus',
                            'Midtre_Gauldal', 'Skaun', 'Indre_Fosen', 'Stjørdal']
    
    elif region in ['Norge', 'norge']:
        with open("./networkGeneration/populationData/kommuneNavnFixed2019.txt", "r", encoding='utf-8') as f:
            municipalities = [line.replace('\n','').replace(' ','_') for line in f]
        with open("./networkGeneration/municipalitiesNotWorking.txt", "r", encoding='utf-8') as f:
            municipalitiesNotWorking = [line.replace('\n','') for line in f]
        municipalityList = [m for m in municipalities if m not in municipalitiesNotWorking]
    
    else:
        municipalityList = ['Trondheim']
    
    return municipalityList


def createEdgeNetwork(municipalities, filename):
    import pandas as pd
    
    edges = []
    for municipality in municipalities:
        for node in municipality.attrs.values():
            if len(node.infDesc) > 0:
                for desc in node.infDesc:
                    if isinstance(desc[0], classes.Commuter):
                        municipality_2 = desc[0].municipality_home
                    else:
                        municipality_2 = municipality.name
                    edges.append([node.id_number, desc[0].id_number, municipality.name, municipality_2,
                                 desc[2], desc[1]])
    
    filename = filename.replace('StateLog','edges').replace('.pkl','').split("/")[-1]
    df = pd.DataFrame(edges, index=None, columns=[
                      'ancestor', 'anc_home', 'descendant', 'desc_home', 'day', 'layer'])
    df.to_csv(f'./results/networks/{filename}.csv')
 

if __name__ == '__main__':
    nationalLayers, nationalNodes = buildNationalLayers(getMunicipalityList('trondelag'), Parameters())
    print(nationalLayers.keys())
    
