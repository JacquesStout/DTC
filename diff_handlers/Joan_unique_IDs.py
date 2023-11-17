import xlsxwriter
import pandas as pd
import numpy as np
from decimal import Decimal

def weighted_mean(values, weights):
    value_mean = 0
    for value, weight in zip(values,weights):
        if not np.isnan(value):
            value_mean += value*weight
    value_mean = value_mean/np.sum(weights)
    return value_mean

def get_max_decimasls(values):
    list = []
    for value in values:
        if not np.isnan(value):
            list.append(len(str(value).split(".")[1]))
    return np.max(list)

def round_down_decimals(value, list):
    return round(value, get_max_decimasls(list))


JOAN_path = "/Users/jas/Downloads/JOAN_MWM.csv"
JOAN_path_new = "/Users/jas/Downloads/JOAN_MWM_combined.csv"

JOAN_df = pd.read_csv(JOAN_path)
JOAN_df_new = pd.DataFrame(columns=JOAN_df.columns)
JOAN_df_new.drop('Segment of test', axis=1, inplace=True)
#for test in np.arange(1, 2):
for test in np.arange(1,np.max(JOAN_df.Test)):
    dataframe_Test = JOAN_df[JOAN_df['Test'] == test]
    JOAN_df_new.at[test, 'Test'] = test
    firstkey = dataframe_Test.index[0]
    for column in JOAN_df.columns[0:8]:
        try:
            JOAN_df_new.at[test, column] = dataframe_Test[column][firstkey]
        except:
            print('hi')
    JOAN_df_new.at[test, 'Duration'] = np.sum(dataframe_Test['Duration'])
    JOAN_df_new.at[test, 'Distance'] = round_down_decimals(np.sum(dataframe_Test['Distance']), dataframe_Test['Distance'])
    JOAN_df_new.at[test, 'Mean speed'] = round_down_decimals(weighted_mean(dataframe_Test['Mean speed'],dataframe_Test['Duration']), dataframe_Test['Mean speed'])
    JOAN_df_new.at[test, 'Max speed'] = np.max(dataframe_Test['Max speed'])
    JOAN_df_new.at[test, 'Freezing episodes'] = np.sum(dataframe_Test['Freezing episodes'])
    for column in JOAN_df.columns[13:16]:
        JOAN_df_new.at[test, column] = np.sum(dataframe_Test[column])
    for column in list(JOAN_df.columns[16:28]) + list(JOAN_df.columns[30:33]):
        if 'average' in column:
            JOAN_df_new.at[test, column] = round_down_decimals(weighted_mean(dataframe_Test[column], dataframe_Test[column.replace('average speed', 'time')]),dataframe_Test[column])
        else:
            JOAN_df_new.at[test, column] = round_down_decimals(np.sum(dataframe_Test[column]), dataframe_Test[column])

    for column in list(JOAN_df.columns[28:30]) + list(JOAN_df.columns[33:36]):
        if dataframe_Test[column].isnull().all().all():
            JOAN_df_new.at[test, column] = np.nan
        else:
            JOAN_df_new.at[test, column] = dataframe_Test[column][firstkey]
JOAN_df_new.set_index('Test')

JOAN_df_new.to_csv(JOAN_path_new)


for index, row in JOAN_df.iterrows():
    print(type(index))
    print(index)
    print('~~~~~~')

    print(type(row))
    print(row)
    print('------')