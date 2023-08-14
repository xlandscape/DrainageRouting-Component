"""Interface :
Import the matrix
import field area

Function python
"""
from config import load_config
import sys
import csv
import numpy as np
from pathlib import Path
import pandas as pd
import os

C_import = np.array([[1,0,0,0],[0,1,1,0],[0,0,0,0],[0,0,1,0],[0,0,0,0]])
field_names = np.array(['F1','F2','F3','F4'])
reaches_names = np.array(['R601','R602','R603','R604','R605'])
"""
the fields area will be obtained from the system (unit : m2)
"""
dict_field_area = {'F1' : 200,
                    'F2' : 200,
                    'F3' : 200,
                    'F4' : 200}


dict_J_g_per_m2_h1 = {'F1' : 0.8,
            'F2' : 10,
            'F3' : 0.1,
            'F4' : 2.3}
"""
the reaches length will be obtained from the system (unit : m)
"""
dict_reaches_length = {'R601' : 50,
                        'R602' : 100,
                        'R603' : 25,
                        'R604' : 135,
                        'R605' : 210}


def main(config_file_path: Path) -> None:
    """Entry point

    Args:
        config_file_path: path to TOML config file
    """
    xroutingdrainage = AttributeDrainageFluxes(config_file_path)
    xroutingdrainage.setup()
    #xroutingdrainage.postprocess()

class AttributeDrainageFluxes :
    def __init__(self, config_file_path: Path) -> None:
        """
        Args:
            config_file_path: path to toml config file
        """
        
        self.config_root = load_config(config_file_path)
        self.config = self.config_root.general
        self.dir = Path(self.config.runDirRoot)
        self.output_file = self.dir.joinpath('LineicMassDra.csv')
        self.input_dir = Path(self.config.inputDir)

        self.mass_flux_per_field_file = 'Jmass.csv' #self.config.fieldsMassFluxFile
        self.matrix_flux = 'matrix_xAquatics.csv'  #self.config.xdrainagerouting_file

        self.fields_area_file = 'fields_area.csv' #self.config.fieldsAreaFile
        self.reaches_lengths_file = 'reaches_length.csv'#self.config.reachesLengthFile
        
        self.reaches = np.array(['R1','R2','R3','R4','R5']) # self.config.reaches

        self.HML_firstRow = None
        self.HML_nRow = None
        self.HML_skipRows = [1]

    def setup(self):

        fields_flux_time = pd.read_csv(Path(self.config.inputDir.joinpath(self.mass_flux_per_field_file)), sep = ',', skiprows = [1])
        self.time = list(fields_flux_time.Time)
        self.fields_flux_data = fields_flux_time.drop('Time', axis = 1)
        self.fields_area = pd.read_csv(Path(self.config.inputDir.joinpath(self.fields_area_file)), sep = ',', skiprows = [1])
        self.reaches_length = pd.read_csv(Path(self.config.inputDir.joinpath(self.reaches_lengths_file)), sep = ',', skiprows = [1])

        self.xdrainagerouting = self.load_dataframe_as_array(self.input_dir, self.xdrainagerouting)
    
        self.attribute_fluxes(self.fields_flux_data, 
                              self.matrix_flux, 
                              self.fields_area, 
                              self.reaches_length, 
                              self.reaches, 
                              self.time)
        
    def prepare_mass_flux_table(self) :

        MassFluxLoadingsTable = pd.read_csv(os.path.join(self.generalConfig['inputDir'],self.mass_flux_per_field_file),
                                                     header = [0], parse_dates=[0],infer_datetime_format = True,
                                                     skiprows = self.HML_skipRows)
        if self.HML_nRow is None:
            filter = ((MassFluxLoadingsTable.Time>=self.startTime) & 
                      (MassFluxLoadingsTable.Time<=self.endTime+dt.timedelta(hours=1)))
            MassFluxLoadingsTable = MassFluxLoadingsTable.loc[filter,]
            MassFluxLoadingsTable.reset_index(drop=True,inplace=True)
            self.HML_firstRow = filter.idxmax() + 2
            self.HML_nRow = filter.sum()
            self.HML_skipRows = lambda x: not(x==0 or (x>=self.HML_firstRow and (x<=self.HML_firstRow+self.HML_nRow)))
        return MassFluxLoadingsTable
    
    #def get_time(self, path):
        
    def load_dataframe_as_array(self, input_dir : Path, file : str):
        """returns the matrix as an array"""
        df = pd.read_csv(Path(input_dir.joinpath(file)), sep = ',')
        df = df.drop(df.columns[0], axis=1).to_numpy()
        return df
    
    def attribute_fluxes(self, 
                         fields_flux, 
                         matrix_flux, 
                         fields_area, 
                         reaches_length, 
                         reaches_names, 
                         time):
        """returns the fluxes per reach per meter """

        df = pd.DataFrame(columns = reaches_names)
        for i in np.arange(len(time)) :
            flux_per_reach = np.matmul(matrix_flux, np.multiply(list(fields_flux.iloc[i]), fields_area ))
            lineic_flux_per_reach = np.divide(flux_per_reach, reaches_length )
            df = pd.concat([df,pd.DataFrame(data = [lineic_flux_per_reach], columns = reaches_names)])
        df.index = np.arange(len(time))
        time_df = pd.DataFrame(data = time)
        lineicmassdra = pd.concat([time_df, df], axis = 1)
        lineicmassdra.to_csv(self.output_file, index = False)
    
    def create_array(self, dict, list):
        """returns an array of values for a given dictionnary and list """
        return [dict[element] for element in list]

if __name__ == "__main__":
    main(Path(sys.argv[1]))  


    #def postprocess(self) -> None :
    #    continue
"""
Interface
Provides flux data to system per reach
"""