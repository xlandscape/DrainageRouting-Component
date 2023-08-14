
"""Component that encapsulates the xDrainageRouting module."""
import datetime
import numpy as np
import os
#import base
#import attrib
#import xDrainageRouting
from pathlib import Path
import pandas as pd
import sys


def main(config_file_path: Path) -> None:
    """Entry point

    Args:
        config_file_path: path to TOML config file
    """
    test = xDRAINAGEROUTING_Wraper(config_file_path)
    test.run()
    #xroutingdrainage.postprocess()

class xDRAINAGEROUTING_Wraper:
    """A component that encapsulates the xDrainageRouting module for usage within the xAquatics."""
   
    # # RELEASES
    # VERSION = base.VersionCollection(
    #     base.VersionInfo("1.1.1", "2023-07-27")
    #    )
    # # AUTHORS
    # VERSION.authors.extend((
    #     "Sascha Bub (component) - sascha.bub@gmx.de",
    #     "Thorsten Schad (component) - thorsten.schad@bayer.com",
    #     "Wim Beltman (module) - wim.beltman@wur.nl",
    #     "Maarten Braakhekke (module) - maarten.braakhekke@wur.nl",
    #     "Louise Wipfler (module) - louise.wipfler@wur.nl",
    #     "Héloïse Thouément (component) - heloise.thouement@wur.nl"
    # ))
    
    #  # ACKNOWLEDGEMENTS
    # VERSION.acknowledgements.extend((
    #     "[TOXSWA](https://www.pesticidemodels.eu/toxswa)",
    # ))

    # # ROADMAP
    # VERSION.roadmap.extend(())

    # # CHANGELOG
    # #below : changelog template
    # #VERSION.added("1.2.20", "components.CascadeToxswa component")

     
    def __init__(self, config_file_path: Path):
        reach_field_matrix_file = "matrix_xAquatics.csv"
        drainage_mass_flux_file = "JMass.csv"
        """
        Initializes the LandscapePEARL component.

        Args:
            name: The name of the component.
            observer: The default observer used by the component.
            store: The data store used by the component.
        """
        super(LandscapePEARL, self).__init__(name, observer, store)
        self._module = base.Module("") #NAME MODULE
        self._inputs = base.InputContainer(self,[ 
           base.Input(
                "ProcessingPath",
                (attrib.Class(str, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The working directory for the module. It is used for all files prepared as module inputs
                or generated as module outputs."""
            ),        
           base.Input(
                "TimeSeriesStart",
                (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The first time step for which input data is provided. 
                This is also the time step of where
                the CascadeToxswa simulation starts."""
            ),
            
            base.Input(
                "SimulationStart",
                (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""First date that is simulated"""
            ),
            
            base.Input(
                "SimulationEnd",
                (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""Last date that is simulated"""
            ),
                        base.Input(
                "MasDraWatLay",
                (attrib.Class(datetime.date, 1), 
                attrib.Unit(None, 1), 
                attrib.Scales("time/hour, space/base_geometry", 1)),
                self.default_observer,
                description="""Mass flux per square meter of field at a specified moment in time."""
            ),
                        base.Input(
                "DrainageRouting",
                (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), 
                attrib.Scales("reach, space/base_geometry", 1)),
                self.default_observer,
                description=""" """
            ),
                        base.Input(
                "REACHLENGTH",
                (attrib.Class(datetime.date, 1), attrib.Unit('m', 1), 
                attrib.Scales("reach", 1)),
                self.default_observer,
                description="""Length of the reaches"""
            ),
                        base.Input(
                "FIELDAREA",
                (attrib.Class(datetime.date, 1), attrib.Unit('m2', 1), 
                attrib.Scales("space/base_geometry", 1)),
                self.default_observer,
                description="""Area of the fields"""
            ),
        ])
        self._outputs = base.OutputContainer(
            self,
            (
                base.Output(
                    "LineicMassDrainage",
                    store,
                    self,
                    {"data_type": np.float, "scales": "time/hour, space/base_geometry", "unit": "g/m2/h"},
                    "Mass flux per meter of reach resulting from the drainage of nearby fields at a specified\
                     moment in time. Whether a field is drained to a reach is an information provided in the \
                     landscape scenario component. The drained mass flux for each field (in g/m2/h) is calculated in the \
                     landscape drainage component.",
                    {
                        "type": np.ndarray,
                        "shape": (
                            "the number of time steps as given by the input", # which input?
                            "the number of reaches as given by the `Reaches` input"
                        ),
                        "chunks": "for fast retrieval of time series"
                    }
                )
                
            ))
        
    def run(self):
        """
        Runs the component.

        Returns:
            Nothing.
        """

        processing_path = Path('D:/2_Cascade_toxswa/xdrainagerouting-xaquatics')#self.inputs["ProcessingPath"].read().values

        reaches_file = processing_path.joinpath('Reaches.csv')
        fields_file = processing_path.joinpath('Fields.csv')
        drainage_routing_file = processing_path.joinpath('xdrainagerouting.csv')

        output_file = processing_path.joinpath('LineicMassDra.csv')
        parameterization_file = os.path.join(processing_path, "config.toml")

        reach_field_routing = pd.read_csv(processing_path.joinpath('input',reach_field_matrix_file)) #self.inputs["DrainageRouting"].read().values
        """
        Below : section with data provided until the database can be used.
        to replace with the input
        """
        reaches_length = {'R601' : 50,
                        'R602' : 100,
                        'R603' : 25,
                        'R604' : 135,
                        'R605' : 210} #self.inputs["DrainageRouting"].read().values
        mass_flux_drainage_per_field = {'F1' : 0.8,
            'F2' : 10,
            'F3' : 0.1,
            'F4' : 2.3} #self.inputs["MATRIX"].read().values
        field_area = {'F1' : 200,
                    'F2' : 200,
                    'F3' : 200,
                    'F4' : 200} #self.inputs["FIELDAREA"].read().values
        reaches_length.to_csv(processing_path.joinpath('input', 'Reaches.csv'), columns = ['reach_length_m'])
        """
        above : section with data provided until the database can be used.
        to replace with the input
        """
        for data, name in zip([reach_field_routing], ['xdrainagerouting.csv']):
            self.create_input_csv(data, name, processing_path)


        self.prepare_parameterization(parameterization_file, processing_path, reaches_file, fields_file, drainage_routing_file)
       # self.read_outputs(os.path.join(processing_path, "experiments", "e1"))
        self.prepare_fields_input(processing_path,  field_area, mass_flux_drainage_per_field)


    def create_input_csv(self, file, name, processing_path):
        file.to_csv(processing_path.joinpath('input', name))

    def prepare_fields_input(self,processing_path,  field_area,mass_flux_drainage_per_field):
        fields_info =  {**field_area,**mass_flux_drainage_per_field}
        fields_info.to_csv(processing_path.joinpath('input', 'Fields.csv'), columns = ['field_area_m2', 'field_mass_flux_g_per_m2_h1'])
       

    def prepare_parameterization(self, parameter_file, processing_path, reaches_file, fields_file, drainage_routing_file, output_file):
        """
        Prepares the module's parameterization.

        Args:
            parameter_file: The path for the parameterization file.
            processing_path: The processing path for the module.
            reaches_file: The path of the reach file reaches.csv.
            fields_file: The path of the field file fields.csv.
            drainage_routing_file : The path to the xdrainagerouting.csv.
            output_file : the path to the LineicMassDra.csv 

        Returns:
            Nothing.
        """
    
        with open(parameter_file, "w") as f:
            f.write("[general]\n")
            f.write("experimentName = e1\n")
            f.write(f"runDirRoot = '..runs/test'\n")
            f.write(f"inputDir = {processing_path}\n")
            f.write(f"fieldsFile = Path({fields_file}\n")
            f.write(f"reachesFile = Path({reaches_file}\n") 
            f.write("overwrite = false\n")
            f.write(f"nProcessor = 1") #{self.inputs['NumberWorkers'].read().values}\n")

            #f.write(f"startDateSim = 01-Jan-1995") # = {self.inputs['TimeSeriesStart'].read().values.strftime('%d-%b-%Y')}\n") # to obtain from landscapescenario
            #f.write(f"endDateSim = 31-Dec-1995") # {end_date_sim}\n") # to obtain from landscapescenario

            f.write("\n[xroutingdrainage]\n")
            f.write(f"xdrainagerouting_file = {drainage_routing_file}\n") # nR*nF matrix
            f.write(f"output_lineic_file = {output_file}\n")
            f.write("outputVars = 'LineicMassLoadingDrainage'\n")


    def run_xroutingdrainage(config_file_path, parameterization_file, processing_path):
        """
        Runs the module.

        Args:
            parameterization_file: The path of the parameterization file.
            processing_path: The processing path of the module.

        Returns:
            Nothing.
        """
        python_exe = os.path.join(os.path.dirname(__file__), "module", "WPy64-3760", "python-3.7.6.amd64",
                                  "python.exe")
        # noinspection SpellCheckingInspection
        python_script = os.path.join(os.path.dirname(__file__), "module", "src", "xDrainageRouting.py")
        base.run_process(
            (python_exe, 
             python_script, 
             parameterization_file),
            processing_path,
            self.default_observer,
            {"PATH": ""}
        )

    def read_outputs(self, output_path):
        """
        Reads the module's outputs into the Landscape Model data store.

        Args:
            output_path: The output path of the module.

        Returns:
            Nothing.
        """
        
        number_time_steps = 365*24 #HOW TO GET NB of TIME STEP BASE ON START AND END DATE
        time_series_start = self.inputs["SimulationStart"].read().values

        self.outputs["LineicMassDrainage"].set_values(
            np.ndarray,
            shape=(number_time_steps, len(self.reaches)),
            chunks=(min(65536, number_time_steps), 1),
            element_names=(None, reaches),
            offset=(time_series_start, None)
        )

        for i, reach in enumerate(reaches):
            lineic_mass_drainage = np.zeros(number_time_steps)
            
            with open(os.path.join(output_path, f"LineicMassDra.csv")) as f:
                f.readline()
                for t in range(number_time_steps):
                    reaches = f.readline().split(",")
                    lineic_mass_drainage[t] = float(reaches[2])   # this is not going to work because our array is much larger
                  
            self.outputs["LineicMassDrainage"].set_values(
                lineic_mass_drainage, slices=(slice(number_time_steps), i), create=False)

if __name__ == "__main__":
    main(Path(sys.argv[1]))  


    #def postprocess(self) -> None :
    #    continue
"""
Interface
Provides flux data to system per reach
"""
        
        