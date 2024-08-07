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
import shapely.geometry
import shapely.wkb
import typing


class xDrainageRouting_Wrapper(base.Component):
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
        Initializes the xDrainageRouting component.

        Args:
            name: The name of the component.
            observer: The default observer used by the component.
            store: The data store used by the component.
        """
        super(xDrainageRouting_Wrapper, self).__init__(
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
                base.Input(
                    "MasDraWatLay",
                    (
                        attrib.Class(np.ndarray, 1),
                        attrib.Unit("g/m2", 1),
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
                        attrib.Class(list[bytes]),
                        attrib.Unit(None),
                        attrib.Scales("space/reach", 1),
                    ),
                    self.default_observer,
                ),
                base.Input(
                    "RoutingMatrix",
                    (
                        attrib.Class(np.ndarray, 1),
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
        self.output_file = self.dir.joinpath("LineicMassDra_g_m_h.csv")

        self.fields = (
            self.inputs["FieldGeometries"].read().element_names[0].get_values()
        )
        self.reaches = (
            self.inputs["HydrographyGeometries"].read().element_names[0].get_values()
        )
        self.number_time_steps = self.inputs["MasDraWatLay"].describe()["shape"][0]
        self.time = range(self.number_time_steps)
        self.fields_flux_data = self.inputs["MasDraWatLay"].read().values

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

        self.read_outputs(os.path.join(processing_path, "experiment"))

    def attribute_fluxes_file(
        self,
        fields_flux,
        matrix_flux,
        fields_area,
        reaches_length,
        reaches_names,
        time,
    ):
        """returns the fluxes per reach per meter

        Args :


        Returns :


        """

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
            lineic_mass_drainage = np.zeros((number_time_steps, 1))

            with open(os.path.join(output_path, self.output_file)) as f:
                f.readline()
                for t in range(number_time_steps):
                    reach_row = f.readline().split(",")
                    lineic_mass_drainage[t] = float(reach_row[i])

            self.outputs["LineicMassLoadingDrainage"].set_values(
                lineic_mass_drainage,
                slices=(slice(number_time_steps), slice(i, i + 1)),
                create=False,
            )
