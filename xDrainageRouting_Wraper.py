"""Component that encapsulates the xDrainageRouting module."""
import datetime
import numpy as np
import os

import base
import attrib

# import xDrainageRouting
from pathlib import Path
import pandas as pd
import sys
import xdrainagerouting.module.src as xDR_component
import shapely.geometry
import shapely.wkb
import typing


class xDrainageRouting_Wraper(base.Component):
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

    def __init__(
        self,
        name: str,
        default_observer: base.Observer,
        default_store: typing.Optional[base.Store],
    ) -> None:
        """
        Initializes the LandscapePEARL component.

        Args:
            name: The name of the component.
            observer: The default observer used by the component.
            store: The data store used by the component.
        """
        super(xDrainageRouting_Wraper, self).__init__(
            name, default_observer, default_store
        )

        self._inputs = base.InputContainer(
            self,
            [
                base.Input(
                    "ProcessingPath",
                    (
                        attrib.Class(str, 1),
                        attrib.Unit(None, 1),
                        attrib.Scales("global", 1),
                    ),
                    self.default_observer,
                    description="""The working directory for the module. It is used for all files prepared as module inputs
                or generated as module outputs.""",
                ),
                #    base.Input(
                #         "TimeSeriesStart",
                #         (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                #         self.default_observer,
                #         description="""The first time step for which input data is provided.
                #         This is also the time step of where
                #         the CascadeToxswa simulation starts."""
                #     ),
                #     base.Input(
                #         "SimulationStart",
                #         (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                #         self.default_observer,
                #         description="""First date that is simulated"""
                #     ),
                # base.Input(
                #     "SimulationEnd",
                #     (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                #     self.default_observer,
                #     description="""Last date that is simulated"""
                # ),
                base.Input(
                    "MasDraWatLay",
                    (
                        attrib.Class(datetime.date, 1),
                        attrib.Unit(None, 1),
                        attrib.Scales("time/hour, space/base_geometry", 1),
                    ),
                    self.default_observer,
                    description="""Mass flux per square meter of field at a specified moment in time.""",
                ),
                base.Input(
                    "FieldGeometries",
                    (
                        attrib.Class(list[bytes], 1),
                        attrib.Unit(None, 1),
                        attrib.Scales("space/base_geometry", 1),
                    ),
                    self.default_observer,
                ),
                base.Input(
                    "HydrographyGeometries",
                    (
                        attrib.Class(str),
                        attrib.Unit(None),
                        attrib.Scales("space/reach", 1),
                    ),
                    self.default_observer,
                ),
                base.Input(
                    "RoutingMatrix",
                    (
                        attrib.Class(str, 1),
                        attrib.Unit(None, 1),
                        attrib.Scales("space/base_geometry, space/reach"),
                    ),
                    self.default_observer,
                    description="""Routing drainage matrix""",
                ),
                base.Input(
                    "TimeSeriesStart",
                    (
                        attrib.Class(datetime.date, 1),
                        attrib.Unit(None, 1),
                        attrib.Scales("global", 1),
                    ),
                    self.default_observer,
                    description="""The first time step for which input data is provided. This is also the time step of where
                    the CascadeToxswa simulation starts.""",
                ),
                base.Input(
                    "MassLoadingSprayDrift",
                    (
                        attrib.Class(np.ndarray, 1),
                        attrib.Unit("mg/m²", 1),
                        attrib.Scales("time/day, space/reach", 1),
                    ),
                    self.default_observer,
                    description="The average drift deposition onto the surface of a water body.",
                ),
            ],
        )
        self._outputs = base.OutputContainer(
            self,
            (
                base.Output(
                    "LineicMassLoadingDrainage",
                    default_store,
                    self,
                    # {
                    #     "data_type": np.float,
                    #     "scales": "time/hour, space/base_geometry",
                    #     "unit": "g/m2/h",
                    # },
                    # "Mass flux per meter of reach resulting from the drainage of nearby fields at a specified\
                    #  moment in time. Whether a field is drained to a reach is an information provided in the \
                    #  landscape scenario component. The drained mass flux for each field (in g/m2/h) is calculated in the \
                    #  landscape drainage component.",
                    # {
                    #     "type": np.ndarray,
                    #     "shape": (
                    #         "the number of time steps as given by the input",  # which input?
                    #         "the number of reaches as given by the `Reaches` input",
                    #     ),
                    #     "chunks": "for fast retrieval of time series",
                    # },
                ),
            ),
        )

    def run(self):
        """
        Runs the component.

        Returns:
            Nothing.
        """

        processing_path = Path(self.inputs["ProcessingPath"].read().values)
        self.dir = processing_path.joinpath("experiment")
        self.output_file = self.dir.joinpath("LineicMassDra.csv")

        drainage_routing_file = processing_path.joinpath("xdrainagerouting.csv")
        output_file = processing_path.joinpath("LineicMassDra_g_m_h.csv")
        parameterization_file = os.path.join(processing_path, "config.toml")
        self.fields = (
            self.inputs["FieldGeometries"].read().element_names[0].get_values()
        )
        self.reaches = (
            self.inputs["HydrographyGeometries"].read().element_names[0].get_values()
        )
        time_series_start = self.inputs["MasDraWatLay"].describe()["offsets"][0]
        # startdate = datetime.strptime(time_series_start, "%Y/%m/%d")
        number_time_steps = self.inputs["MasDraWatLay"].describe()["shape"][0]
        self.time = range(number_time_steps)
        # reaches_length = self.inputs["RoutingMatrix"].geometries[0]
        self.fields_flux_data = self.inputs["MasDraWatLay"].read().values

        # Below : to improve with using values retrieved from the RoutingMatrix instead
        self.fields_area = [
            shapely.wkb.loads(geom).area
            for geom in self.inputs["FieldGeometries"].read().values
        ]
        # At this stage values cannot be obtained fom the geometries of the drainage matrix
        self.reaches_length = [
            shapely.wkb.loads(geom).length
            for geom in self.inputs["HydrographyGeometries"].read().values
        ]

        self.xdrainagerouting = self.inputs["RoutingMatrix"].read().values

        """
        above : section with data provided until the database can be used.
        to replace with the input
        """
        self.lineicmassdra_file = self.attribute_fluxes_file(
            self.fields_flux_data,
            self.xdrainagerouting,
            self.fields_area,
            self.reaches_length,
            self.reaches,
            self.time,
        )

        # self.prepare_field_area(processing_path, fields_area, "fields_area.csv")
        # self.prepare_mass_flux_drainage_per_field(
        #     processing_path,
        #     mass_flux_drainage_per_field,
        #     "mass_flux_drainage_field.csv",
        # )
        # self.prepare_reaches_length(
        #     processing_path, reaches_length, "reaches_length.csv"
        # )
        # self.prepare_xdrainagerouting(
        #     processing_path, drainage_routing, "xdrainagerouting.csv"
        # )
        # self.prepare_parameterization(
        #     parameterization_file,
        #     processing_path,
        #     self.fields_area,
        #     self.reaches_length,
        #     self.fields_flux_data,
        #     drainage_routing_file,
        # )

        self.read_outputs(os.path.join(processing_path, "experiment"))

    # def prepare_field_area(self, processing_path, field_area_file, output_file_name):
    #     field_area_file.to_csv(
    #         processing_path.joinpath("input", output_file_name),
    #         sep=",",
    #         columns=["Field", "Area_m2"],
    #     )

    # def prepare_reaches_length(self, processing_path, reaches_length, output_file_name):
    #     reaches_length.to_csv(
    #         processing_path.joinpath("input", output_file_name),
    #         sep=",",
    #         columns=["Reach", "length_m"],
    #     )

    # def prepare_mass_flux_drainage_per_field(
    #     self, processing_path, mass_flux_drainage_per_field, output_file_name
    # ):
    #     column_names = self.fields  # self.metadatadrainage
    #     output_file = processing_path.joinpath("input", output_file_name)
    #     with open(output_file, "w") as f:
    #         f.write("Time,LISTFIELDS\n")
    #         f.write("-, len(listfields)*[g/m2]\n")
    #     for mass in mass_flux_drainage_per_field:
    #         # f.write(f"{(time_series_start + datetime.timedelta(i)).strftime('%d-%b-%Y')},")
    #         f.write(f"{mass}\n")
    #     mass_flux_drainage_per_field.to_csv(
    #         processing_path.joinpath("input", output_file_name),
    #         sep=",",
    #         columns=["Field"],
    #     )  # + )

    # def prepare_xdrainagerouting(
    #     self, processing_path, drainage_routing_file, output_file_name
    # ):
    #     drainage_routing_file.to_csv(
    #         processing_path.joinpath("input", output_file_name), sep=","
    #     )
    def attribute_fluxes_file(
        self,
        fields_flux,
        matrix_flux,
        fields_area,
        reaches_length,
        reaches_names,
        time,
    ):
        """returns the fluxes per reach per meter"""

        flux_per_field = np.multiply(fields_flux, np.array(fields_area))
        flux_per_reach = np.matmul(flux_per_field, matrix_flux.T)
        lineic_flux_per_reach = np.divide(flux_per_reach, reaches_length)
        df = pd.DataFrame(lineic_flux_per_reach, columns=reaches_names)

        # how are reaches_names obtained HAS to be the name of the columns of this input
        df.index = np.arange(len(time))
        time_df = pd.DataFrame(data=time)
        lineicmassdra = pd.concat([time_df, df], axis=1).set_index(0)

        lineicmassdra.to_csv(
            self.output_file,
            index=False,
            header=self.reaches,
        )

    def prepare_parameterization(
        self,
        parameter_file,
        processing_path,
        fields_area,
        reaches_length,
        mass_flux_drainage_per_field,
        drainage_routing_file,
        output_file,
    ):
        """
        Prepares the module's parameterization.

        Args:
            parameter_file: The path for the parameterization file.
            processing_path: The processing path for the module.
            reacheslength_file: The path of the reach file reaches_lengths.csv.
            fieldsarea_file: The path of the field file fields_area.csv.
            fieldsarea_file: The path of the field file fields_area.csv.
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
            f.write(f"outputDir = {output_file}\n")
            f.write(
                f"fields = {self.fields}\n"
            )  # to obtain from xdrainagerouting metadata
            f.write(
                f"reaches= {self.reaches} \n"
            )  # to obtain from xdrainagerouting metadata
            f.write("overwrite = false\n")
            f.write(
                f"nProcessor = 1"
            )  # {self.inputs['NumberWorkers'].read().values}\n")

            # f.write(f"startDateSim = 01-Jan-1995") # = {self.inputs['TimeSeriesStart'].read().values.strftime('%d-%b-%Y')}\n") # to obtain from landscapescenario
            # f.write(f"endDateSim = 31-Dec-1995") # {end_date_sim}\n") # to obtain from landscapescenario

            f.write("\n[xroutingdrainage]\n")
            f.write(
                f"xdrainagerouting_file = {drainage_routing_file}\n"
            )  # nR*nF matrix
            f.write(f"output_lineic_file = {output_file}\n")
            f.write("outputVars = 'LineicMassLoadingDrainage'\n")
            f.write(f"fieldsAreaFile = Path({fields_area}\n")
            f.write(f"fieldsMassFluxFile = Path({mass_flux_drainage_per_field}\n")
            f.write(f"reachesLengthFile = Path({reaches_length}\n")

    def run_xroutingdrainage(config_file_path, parameterization_file, processing_path):
        """
        Runs the module.

        Args:
            parameterization_file: The path of the parameterization file.
            processing_path: The processing path of the module.

        Returns:
            Nothing.
        """
        python_exe = os.path.join(
            os.path.dirname(__file__),
            "module",
            "WPy64-3760",
            "python-3.7.6.amd64",
            "python.exe",
        )
        # noinspection SpellCheckingInspection
        python_script = os.path.join(
            os.path.dirname(__file__), "module", "src", "xDrainageRouting.py"
        )
        base.run_process(
            (python_exe, python_script, parameterization_file),
            processing_path,
            self.default_observer,
            {"PATH": ""},
        )

    def read_outputs(self, output_path):
        """
        Reads the module's outputs into the Landscape Model data store.

        Args:
            output_path: The output path of the module.

        Returns:
            Nothing.
        """

        number_time_steps = self.inputs["MasDraWatLay"].describe()["shape"][0]
        time_series_start = self.inputs["MasDraWatLay"].describe()["offsets"][0]

        self.outputs["LineicMassLoadingDrainage"].set_values(
            np.ndarray,
            shape=(number_time_steps, len(self.reaches)),
            chunks=(min(65536, number_time_steps), 1),
            element_names=(
                None,
                self.inputs["RoutingMatrix"].describe()["element_names"][0],
            ),
            offset=(time_series_start, None),
        )

        for i, reach in enumerate(self.reaches):
            lineic_mass_drainage = np.zeros(number_time_steps)

            with open(os.path.join(output_path, f"LineicMassDra.csv")) as f:
                f.readline()
                for t in range(number_time_steps):
                    reach_row = f.readline().split(",")
                    lineic_mass_drainage[t] = float(reach_row[i])

            self.outputs["LineicMassLoadingDrainage"].set_values(
                lineic_mass_drainage, slices=(slice(number_time_steps), i), create=False
            )

    # def postprocess(self) -> None :
    #    continue


"""
Interface
Provides flux data to system per reach
"""
