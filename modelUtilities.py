"""
Author: Helge Bergo
Date: February 2021
File: modelUtilities.py

This module contains utility functions used in model.py, mostly used in the 
setup and finish of the simulation. 

Not much used during the end of the project, but extensively the first few months. 

"""

import numpy as np
import pandas as pd
import os

from parameters import *
import model


def printProgress(iteration, total, timeUsed, bar_length=100, **kwargs):
    percents = f'{100 * (iteration / float(total)):.2f}'
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = f'{"█" * filled_length}{"-" * (bar_length - filled_length)}'

    timeRemaining = getRemainingTime(iteration, total, timeUsed)
    meanTime = np.mean(timeUsed)
    totalTime = f'{meanTime*total/60:.0f} min'

    print(f'\rProgress: |{bar}| {percents}% complete;  Remaining: {timeRemaining}/{totalTime}; {meanTime:.1f} sec/day  ', end='')


def getRemainingTime(iteration, total, timeUsed):
    '''Function that gives an estimate time left, based on the average of the runtime of the previous 10 days.'''
    if iteration < 3:
        timeString = 'TBD min'
    else:
        remainingTime = np.mean(timeUsed) * (total-iteration)
        timeString = '{:.1f} sec'.format(remainingTime)
        if remainingTime > 120:
            timeString = '{:.1f} min'.format(remainingTime/60)
    
    return timeString


def printResults(stateLog, infLogByLayer, parameters, runtime):
    if runtime > 7200:
        print(f'\nFinished {parameters.cityName} simulation in {runtime/3600:.0f} hours; {runtime/parameters.runDays:.1f} sec/day.\n')
    elif runtime > 110:
        print(f'\nFinished {parameters.cityName} simulation in {runtime/60:.0f} minutes; {runtime/parameters.runDays:.1f} sec/day.\n')
    else:
        print(f'\nFinished {parameters.cityName} simulation in {runtime:.0f} seconds; {runtime/parameters.runDays:.1f} sec/day.\n')


def profiler(function=model.main, filename='model', saveStats=True):
    '''Profiling to benchmark the code'''
    import cProfile, pstats
    profiler = cProfile.Profile()
    profiler.enable()
    function()
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(10)

    if saveStats:
        folder_path = f'./results/profilers'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        stats.dump_stats(f'{folder_path}/{filename}_profile')


def saveModelResults(stateLog, infLogByLayer, parameters, *attrs):
    simulationName = f'{parameters.cityName[0]}-{parameters.runDays}D-{parameters.n}N'
    saveToCSV(stateLog, f'{simulationName}-states')
    saveToCSV(infLogByLayer, f'{simulationName}-infections')
    print(f'\nSaved states and infections to file.')


def saveToCSV(data, filename, folder_path='./results/simulations'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, filename)
    
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    
    if not os.path.isfile(f'{file_path}.csv'):
        data.to_csv(f'{file_path}.csv', index=False)
    else:
        fileNumber = 1
        while True:
            file_path = os.path.join(folder_path,filename)
            file_name = f'{file_path}_{fileNumber}.csv'
            if not os.path.isfile(file_name):
                data.to_csv(file_name, index=False)
                break
            else:
                fileNumber += 1


def getFilenames(path='./results/',folder='',endswith=''):
    filenames = [os.path.join(path,folder,basename) for basename in os.listdir(path+folder) if basename.endswith(endswith)]
    filenames = sorted(filenames, key=os.path.getctime, reverse=True)
    return filenames
    

def savePickle(data, name, folder='/simulations'):
    import pickle
    pickle.dump(data, open(f'results{folder}/{name}.pkl', 'wb'))


def loadPickle(file_path=''):
    if not file_path:
        file_path = getFilenames(path='./results/simulations', endswith='.pkl')[0]
    import pickle
    data = pickle.load(open(f'{file_path}', 'rb'))
    if data is dict:
        data['name'] = file_path.split('/')[-1].split('.pkl')[0]
    return data

