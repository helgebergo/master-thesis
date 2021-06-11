"""
Author: Helge Bergo
Date: June 2021
File: classes.py

This module contains defines the classes used in model.py. 
Includes the Person and Commuter classes, Clique, Layer and Municipality. 
"""

import random
import numpy as np
import modelFunctions
from parameters import *

class Person:

    def __init__(self, id_number, age, **kwargs):
        self.id_number = id_number
        self.age = age
        self.decade = min(age-age%10, 80)
        self.inNursing = False
        
        self.state = 'S'
        self.sick = False
        
        self.infAnc = -1
        self.infDesc = []

        self.present = {}
        for layer in layers:
            self.present[layer] = True

        if age < 19:
            self.ageGroup = 'B'
        elif age < 55:
            self.ageGroup = 'A1'
        elif age < 65:
            self.ageGroup = 'A2'
        elif age < 80:
            self.ageGroup = 'E1'
        else:
            self.ageGroup = 'E2'

    def __repr__(self):
        return f'ID:{self.id_number}-{self.age}-{self.state}'


    def generateActivity(self, parameters):
        mode, var, exp = parameters.activity.values()
        if self.ageGroup in ['A1', 'A2', 'E1']:
            self.activity = min(int(max(np.random.normal(mode, var), 1) + pow(random.random(), exp)),100)
        else:
            self.activity = min(int(max(np.random.normal(mode, var), 1)),100)

    def infectNode(self, anc, layer, day, parameters):
        self.state = 'E'
        self.lastDay = day
        self.infAnc = [anc, layer, day]
        anc.infDesc.append([self, layer, day])
        self.virus = anc.virus
        self.infDay = day
        
        self.nextDay = day+1+np.random.poisson(self.virus.duration['I-E'])

    
    '''Testing and quarantine functions'''
    def test(self, fpr=0, fnr=0):
        if self.state in {'Ip', 'Ia'}:
            return random.random() > fnr
        elif self.state == 'Is':
            return random.random() > fnr        
        else:
            return random.random() < fpr
    
    def quarantineNode(self):
        for layer in {'W', 'US', 'VS', 'BS', 'BH', 'R'}:
            self.present[layer] = False 
        self.quarantine = True
    
    def dequarantineNode(self):
        for layer in {'W', 'US', 'VS', 'BS', 'BH', 'R'}:
            self.present[layer] = True 
        self.quarantine = False

    def individualTestAndQuarantine(self, layers, day, parameters):
        if self.test():
            if self.inNursing == False:
                for clique in self.cliques:
                    if clique.name == 'HH':
                        clique.quarantineClique()


    '''State change functions'''
    def recover(self, params, day):
        self.state = 'R'
        self.lastDay = day
        self.sick = False
        
        for clique in self.cliques:
            clique.cases -= 1

        for layer in self.present:
            self.present[layer] = True
            
        if random.random() < params['NI']:
            self.nextState = 'S'

    def stateFunction(self):
        funcs = {
            'E': self.incubate,
            'Ia': self.asymptomatic,
            'Ip': self.preSymptomatic,
            'Is': self.symptomatic,
            'H': self.hospital,
            'ICU': self.ICU
        }
        return funcs[self.state]
    
    '''Daily state progress check and branching functions'''
    def incubate(self, p, day):
        if day == self.nextDay:
            if random.random() < p['S'][self.decade]:
                self.turnPresymp(p, day)
            else:
                self.turnAsymp(p, day)
        
    def asymptomatic(self, p, day):
        if day == self.nextDay:
            self.recover(p, day)
        
    def preSymptomatic(self, p, day):
        if day == self.nextDay:
            self.activateSymptoms(p, day)
            
    def symptomatic(self, p, day):
        if day == self.nextDay:
            if self.nextState == 'D':
                self.die(p, day)
            elif self.nextState == 'H':
                self.hospitalize(p, day)
            else:
                self.recover(p, day)

    def hospital(self, p, day):
        if day == self.nextDay:
            if self.nextState == 'ICU':
                self.enterICU(p, day)
            elif self.nextState == 'R':
                self.recover(p, day)
            elif self.nextState == 'D':
                self.die(p, day)

    def ICU(self, p, day):
        if day == self.nextDay:
            if self.nextState == 'D':
                self.die(p, day)
            elif self.nextState == 'R':
                self.recover(p, day)
          
                
    '''State change functions'''
    def recover(self, p, day):
        self.state = 'R'
        self.lastDay = day
        self.sick = False
        self.relInfectivity = 0.0

        for layer in self.present:
            self.present[layer] = True
            
        if random.random() < p['NI']:
            self.nextState = 'S'

    def turnAsymp(self, p, day):
        self.state = 'Ia'
        self.nextState = 'R'
        self.nextDay = day+1+np.random.poisson(self.virus.duration['AS-R'])
        self.sick = True

        self.relInfectivity = 0.3
    
    def turnPresymp(self, p, day):
        self.state = 'Ip'
        self.nextState = 'Is'
        self.nextDay = day+1+np.random.poisson(self.virus.duration['PS-I'])
        self.sick = True
        self.relInfectivity = 3.0
        if self.age < 13:
            self.relInfectivity = 0.3
    
    def activateSymptoms(self, p, day):
        self.state = 'Is'
        self.lastDay = day
        for layer in ['BH', 'BS', 'US', 'VS', 'W', 'NH', 'R']:
            self.present[layer] = False
        
        if self.inNursing:
            if random.random() < self.virus.probability['NHDage'][self.decade]:
                self.nextState = 'D'
                self.nextDay = day+1+np.random.poisson(self.virus.duration['I-D'])
            else:
                self.nextState = 'R'
                self.nextDay = day+1+np.random.poisson(self.virus.duration['I-R'])
                
        elif random.random() < self.virus.probability['HRage'][self.decade]:
            self.nextState = 'H'
            self.nextDay = day+1+np.random.poisson(self.virus.duration['I-H'])
        else:
            self.nextState = 'R'
            self.nextDay = day+1+np.random.poisson(self.virus.duration['I-R'])
        self.relInfectivity = 1
        if self.age < 13:
            self.relInfectivity = 0.3
        
    def hospitalize(self, p, day):
        self.state = 'H'
        self.lastDay = day
        for layer in ['HH', 'NH']:
            self.present[layer] = False 

        if random.random() < self.virus.probability['ICUage'][self.decade]:
            self.nextDay = day+1+np.random.poisson(self.virus.duration['H-ICU'])
            self.nextState = 'ICU'
            
        elif random.random() < self.virus.probability['DRage'][self.decade]:
            self.nextDay = day+1+np.random.poisson(self.virus.duration['H-D'])
            self.nextState = 'D'
        else:
            self.nextDay = day+1+np.random.poisson(self.virus.duration['H-R'])
            self.nextState = 'R'
    
    def enterICU(self, p, day):
        self.state = 'ICU'
        self.lastDay = day

        if random.random() < self.virus.probability['DRage'][self.decade]:
            self.nextDay = day+1+np.random.poisson(self.virus.duration['ICU-D'])
            self.nextState = 'D'
        else:
            self.nextDay = day+1+np.random.poisson(self.virus.duration['ICU-R'])
            self.nextState = 'R'

    def die(self, p, day):
        self.diedFrom = self.state
        self.state = 'D'
        self.lastDay = day
        self.nextDay = -1
        self.nextState = ''
        self.sick = False
        for layer in self.present:
            self.present[layer] = False

    def vaccinateNode(self, p=1.0):
        if random.random() < p:
            self.state = 'R'
            self.sick = False
            for layer in self.present:
                self.present[layer] = True

    """
    def partialVaccination(attrs, vaccPool, n, p):
        '''TODO'''
        for node in vaccPool[0:n]:
            vaccinateNode(attrs, node, p)
        del vaccPool[:n]    
    """


class Commuter(Person):
    
    def __init__(self, Person, municipality_home, municipality_commute):
        super().__init__(Person.id_number, Person.age)
        self.municipality_home = municipality_home
        self.municipality_commute = municipality_commute

    def __repr__(self):
        return f'{self.id_number} {self.municipality_home}->{self.municipality_commute}'

    def __len__(self):
        return 1


class Commuter2(Person):
    '''Simple class for commuters without a created home municipality'''
    def __init__(self, municipality_commute):
        super().__init__(Person.id_number, Person.age)
        self.municipality_commute = municipality_commute
        

# ============================================================
# CLIQUE CLASS 
# ============================================================


class Clique:
    '''Clique class containing Persons'''

    def __init__(self, municipality='', nodes=None):
        self.municipality = municipality
        self.nodes = nodes if nodes is not None else []
        self.open = True
        self.openRating = 1.0

    def __repr__(self):
        return f'C: {len(self.nodes)} nodes.'

    def __iter__(self):
        return self.nodes.__iter__()

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, key):
        return self.nodes[key]


    def hasCases(self):
        for node in self.nodes:
            if node.sick:
                return True
        return False
    
    def pooledTest(self, parameters, fnr):
        for node in self.nodes:
            if node.test():
                if random.random() < fnr:
                    return False
                else:
                    return True
        return False

    def pooledTestAdultOnly(self, parameters, age=18):
        for node in self.nodes:
            if node.age > age and node.test():
                return True
        return False

    def quarantineClique(self):
        for node in self.nodes:
            node.quarantineNode()

    def dequarantineClique(self):
        for node in self.nodes:
            node.dequarantineNode()

    def testAndQuarantine(self, parameters, fnr, fpr):
        if self.pooledTest(parameters, fnr):
            self.quarantineClique()
        else:
            self.dequarantineClique()

    def testAndQuarantineAdults(self, parameters, fnr, fpr, age=18):
        if self.pooledTestAdultOnly(parameters, age):
            self.quarantineClique()
        else:
            self.dequarantineClique()


class Commuter_Clique(Clique):

    def __init__(self, Clique, commuter_nodes):
        super().__init__(Clique.municipality)
        self.commuter_nodes = commuter_nodes


    def __repr__(self):
        return f'C-C: {len(self.commuter_nodes)} commuters.'



# ============================================================
# LAYER CLASS 
# ============================================================


class Layer:
    '''Layer class containing cliques'''

    def __init__(self, name):
        self.name = name
        self.cliques = []
        self.open = True


    def __repr__(self):
        persons = 0
        for clique in self.cliques:
            # persons += clique.get_size()
            persons += len(clique)
        return 'Layer: {}, cliques: {}, persons: {}, open: {}'.format(self.name, len(self.cliques), persons, self.open)


    def __iter__(self):
        return self.cliques.__iter__()


    def addClique(self, Clique):
        self.cliques.append(Clique)

    def hasCases(self):
        for clique in self:
            if clique.hasCases():
                return True
        return False


# ============================================================
# MUNICIPALITY CLASS 
# ============================================================


class Municipality:
    '''Municipality class containing cliques'''

    def __init__(self, name, layers, attrs):
        self.name = name
        self.layers = layers
        self.attrs = attrs
        self.population = len(attrs.values())
        self.pools = []


    def __repr__(self):
        return f'{self.name}, {self.population}'


    def __iter__(self):
        return self.attrs.__iter__()

    def hasCases(self):
        for layer in self.layers.values():
            if layer.name != 'R' and layer.hasCases():
                return True
        return False

    def setTestRules(self, parameters):
        self.pools = modelFunctions.setTestRules(
            parameters, self.layers, self.attrs)
        
