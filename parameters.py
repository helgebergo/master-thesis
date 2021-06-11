"""
Author: Helge Bergo
Date: February 2021
File: parameters.py

This file contains the global parameters used in the main simulation model. 
"""

layers = {'BH': {}, 'BS': {}, 'US': {}, 'VS': {},
          'W': {}, 'HH': {}, 'NH': {}, 'R': {}}

stateList = ['S', 'E', 'Ia', 'Ip', 'Is', 'R', 'H', 'ICU', 'D']
states = ['Susceptible', 'Exposed', 'Asymptomatic ', 'Presymptomatic',
          'Symptomatic', 'Recovered', 'Hospitalised', 'ICU', 'Dead']


class Parameters:
    """The default parameters used in the model."""
    
    def __init__(self, infected=0, runDays=50, cityName='Trondheim', **kwargs):
        self.n = infected
        self.cityName = cityName
        self.startDay = 0
        self.runDays = runDays
        self.prevalence = kwargs.get('prevalence', 0.005)
        self.seedMunicipality = kwargs.get('seedMunicipality', None)
        self.region = kwargs.get('region', 'Trondheim')
        
        self.activity = kwargs.get(
            'activity', {'mode': 10, 'var': 3, 'exp': -0.75})
        self.strategy = kwargs.get('strategy', {'S': 12, 'W': 1, 'R': 0.25})
        self.testing = kwargs.get('testing', {})
        self.testRules = {}
        self.inVec = kwargs.get('inVec',{})
        
        self.mutationChance = kwargs.get('mutationChance', 0.0)
        self.commuterFraction = kwargs.get('commuterFraction', 1.0)
        self.commuter_prevalence = kwargs.get(
            'commuter_prevalence', self.prevalence)
        self.removeWorkers = 0.0

        self.saveResults = kwargs.get('saveResults', False)
        self.printResults = kwargs.get('printResults', False)
        self.plotResults = kwargs.get('plotResults', False)
        
    def __repr__(self):
        return f'{self.cityName}: {self.runDays} days, {self.n} infected.'



class SARS_CoV_2():
    """The SARS-CoV-2 virus class, with all disease probabilities and 
    durations of disease states. """
    
    name = 'SARS-CoV-2'

    duration = {
        'I-E': 1,
        'PS-I': 2,
        'I-R': 5,
        'I-H': 6,
        'AS-R': 8,
        'H-R': 8,
        'H-ICU': 4,
        'ICU-R': 12
    }
    duration['ICU-D'] = duration['ICU-R']
    duration['H-D'] = duration['H-ICU'] + .5*duration['ICU-D']
    duration['I-D'] = duration['I-H'] + duration['H-D']

    probability = {
        # base infection probability
        'inf': {
            'BH': 0.00015, 'BS': 0.000015, 'US': 0.00015,
            'VS': 0.00015, 'W': 0.00015, 'R': 0.5*pow(10, -6),
            'HH': 0.15, 'NH': 0.15, 'dynR': 0.015
        },
        
        """
        # 'rec' : 0.1,
        # 'inc' : 1, # asymptomatic
        """
        
        # chance of developing symptoms
        'S': {
            0: 0.5, 10: 0.5, 20: 0.5, 30: 0.5, 40: 0.5,
            50: 0.5, 60: 0.5, 70: 0.5, 80: 0.5
        },

        # hospitalisation risk
        'H': {'B': 0.0001, 'A1': 0.02, 'A2': 0.08, 'E1': 0.15, 'E2': 0.184},

        # death risk once hospitalised
        'D': {'B': 0.1, 'A1': 0.05, 'A2': 0.15, 'E1': 0.3, 'E2': 0.40},
        'ICU': 0.3,
        'NI': 0,

        """
        'infRatio' : {'B': 0.25, 'A1': 1, 'A2': 1, 'E1': 1, 'E2': 1},
        """

        # hospitalisation by age bracket
        'Hage': {
            0: 0.0001, 10: 0.00048, 20: 0.0104, 30: 0.0343, 40: 0.0425,
            50: 0.0816, 60: 0.118, 70: 0.166, 80: 0.184
        },

        # ICU per hospitalization by age bracket
        'ICUage': {
            0: 0.3, 10: 0.3, 20: 0.3, 30: 0.3, 40: 0.3,
            50: 0.3, 60: 0.3, 70: 0.3, 80: 0.3
        },

        # hospital-death per case by age bracket
        'Dage': {
            0: 1.61*pow(10, -5), 10: 6.95*pow(10, -5), 20: 3.09*pow(10, -4),
            30: 8.44*pow(10, -4), 40: 1.61*pow(10, -3), 50: 5.95*pow(10, -3),
            60: 0.0193, 70: 0.0428, 80: 0.078
        }
    }
    
    # hospitalisation corrected for asymptomatic cases
    probability['HRage'] = {}
    for ageGrp in probability['Hage']:
        probability['HRage'][ageGrp] = probability['Hage'][ageGrp] / \
            probability['S'][ageGrp]

    # death rate by age group
    probability['DRage'] = {}
    for ageGrp in probability['Hage']:
        probability['DRage'][ageGrp] = probability['Dage'][ageGrp] / \
            (probability['Hage'][ageGrp])

    probability['NHDage'] = {
        60: probability['DRage'][60],
        70: probability['DRage'][70],
        80: probability['DRage'][80]
    }

    def __init__(self):
        pass

    def __repr__(self):
        return f"{self.name}: R {self.probability['inf']['R']:.1E}, dynR {self.probability['inf']['dynR']:.1E}"
