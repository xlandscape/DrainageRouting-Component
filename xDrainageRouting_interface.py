"""
Obtain matrix field/reach, 
reaches Length 
fields area
fields fluxes

Output to system
flux to reach per reach length
"""

"""Component that encapsulates the CascadeToxswa module."""
import datetime
import numpy as np
import os
import base
from osgeo import ogr
import attrib


class xDrainageRouting(base.Component):
    """A component that encapsulates the xDrainageRouting module for usage within the xAquatics."""
    # RELEASES
    VERSION = base.VersionCollection(
        base.VersionInfo("1.1.1", "2023-07-27")
       )
    # AUTHORS
    VERSION.authors.extend((
        "Sascha Bub (component) - sascha.bub@gmx.de",
        "Thorsten Schad (component) - thorsten.schad@bayer.com",
        "Wim Beltman (module) - wim.beltman@wur.nl",
        "Maarten Braakhekke (module) - maarten.braakhekke@wur.nl",
        "Louise Wipfler (module) - louise.wipfler@wur.nl",
        "Héloïse Thouément (component) - heloise.thouement@wur.nl"
    ))
    
     # ACKNOWLEDGEMENTS
    VERSION.acknowledgements.extend((
        "[TOXSWA](https://www.pesticidemodels.eu/toxswa)",
    ))

    # ROADMAP
    VERSION.roadmap.extend(())

    # CHANGELOG
    #below : changelog template
    #VERSION.added("1.2.20", "components.CascadeToxswa component")
    
    def __init__(self, name, observer, store):
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
                "MATRIX",
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
                    "LineicMassDra",
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
                
            )
        
        def run(self):
        """
        Runs the component.

        Returns:
            Nothing.
        """
        processing_path = self.inputs["ProcessingPath"].read().values
        parameterization_file = os.path.join(processing_path, "config.toml")
        reach_field_matrix_file = "reach_field_matrix.csv"

        self.select_fields(processing_path, os.path.join(processing_path, reach_field_matrix_file))
        self.run_landscape_pearl(parameterization_file, processing_path)
        self.read_outputs(os.path.join(processing_path, "experiments", "e1"))
        self.prepare_parameterization(parameterization_file, processing_path, reach_file, temperature_file,
                                      substance_file)
        self.prepare_temperature(os.path.join(processing_path, temperature_file))

        def select_fields(self, matrix_file)
        """
        Select the fields to run 
        Based on data from the system

        """

        # Each field provided must be run, so not additionnal check is necessary 
        # Importing the matrix not necessary for landscapepearl

        C_import = np.array([[1,0,0,0],[0,1,1,0],[0,0,0,0],[0,0,1,0],[0,0,0,0]])
        field_names = np.array(['F1','F2','F3','F4'])
        reaches_names = np.array(['R601','R602','R603','R604','R605'])

    def prepare_parameterization(self, parameter_file, processing_path, reach_file, temperature_file, substance_file):
        """
        Prepares the module's parameterization.

        Args:
            parameter_file: The path for the parameterization file.
            processing_path: The processing path for the module.
            reach_file: The path of the reach file.
            temperature_file: The path of the temperature file.
            substance_file: The path of the substance file.

        Returns:
            Nothing.
        """
    
        with open(parameter_file, "w") as f:
                    
            f.write("\n[pearl]\n")
            f.write("fieldSelection = {fields_names} \n") # goal is to have self.input.field 
            f.write("outputVars = MasDraWatLay,MasRnfWatLay\n")

    def prepare_hydrological_data(self, output_path, fields_file):
        # Get the field parametrisation from the database
        # see example with CascadeToxswa.py
        continue

    def prepare_temperature(self, output_file):
        """
        Prepares the temperature input for the module.

        Args:
            output_file: The path for the input file.

        Returns:
            Nothing.
        """

        # at the moment obtains the end date of the simulation through 
        # the "MassLoadingSprayDrift" input, do we proceed the same way?
        # temperature file could be obtained from TOXSWA run? 
        # Should be the same (or time step different?)
        # Probably copy structure of funcion in CascadeToxswa.py

    def prepare_substance()
        # use function in CascadeToxswa.py
        continue 

    def run_landscape_pearl(self, parameterization_file, processing_path):
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
            (python_exe, python_script, parameterization_file),
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
        number_fields = 3 #
        number_time_steps = 50 #self.inputs["WaterDischarge"].describe()["shape"][0]
        time_series_start = self.inputs["TimeSeriesStart"].read().values

        self.outputs["LINEICDRAMASS"].set_values(
            np.ndarray,
            shape=(number_time_steps, number_reaches),
            chunks=(min(65536, number_time_steps), 1),
            element_names=(None, names_reaches),
            offset=(time_series_start, None)
        )

        for i, reach in enumerate(names_reaches):
            lineic_mass_drainage = np.zeros(number_time_steps)
            
            with open(os.path.join(output_path, f"F{reach}.csv")) as f:
                f.readline()
                for t in range(number_time_steps):
                    reaches = f.readline().split(",")
                    lineic_mass_drainage[t] = float(reaches[2])
                  
            self.outputs["LINEICMASSDRA"].set_values(
                lineic_mass_drainage, slices=(slice(number_time_steps), i), create=False)


        
        