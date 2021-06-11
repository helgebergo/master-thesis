import numpy as np
import pandas as pd

def createData():
    municipalityNamesFile = open("networkGeneration/populationData/kommuneNavnFixed2019.txt", "r", encoding='utf-8')
    municipalityNames = municipalityNamesFile.readlines()
    municipalityNamesFile.close()
    
    idAndAge = []
    socialNetwork = []
    fails = []

    for municipality in municipalityNames:
        municipality = municipality.replace('\n','')
        folder_path = f'networkGeneration/output/{municipality}'
        ageFile = f'{folder_path}/idAndAge_{municipality}_1.txt'
        cliqueFile = f'{folder_path}/socialNetwork_{municipality}_1.txt'
        
        try:
            for file_, l in zip([ageFile, cliqueFile], [idAndAge, socialNetwork]):
                f = open(file_)
                for line in f:
                    line = line.replace('\n','')
                    l.append(f'{municipality};{line}')
        except:
            fails.append(municipality)
    
    print(f'Failed {len(fails)} municipalities.')
    pd.DataFrame(idAndAge).to_csv("networkGeneration/idAndAge_national.txt", index=False)
    pd.DataFrame(socialNetwork).to_csv("networkGeneration/socialNetwork_national.txt", index=False)


createData()
