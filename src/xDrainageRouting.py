"""Interface :
Import the matrix
import field area

Function python
"""
from config import load_config
import sys
import numpy as np, datetime as dt, pandas as pd
from pathlib import Path
import os


def main(config_file_path: Path) -> None:
    """Entry point

    Args:
        config_file_path: path to TOML config file
    """
    xroutingdrainage = AttributeDrainageFluxes(config_file_path)
    xroutingdrainage.setup()
    # xroutingdrainage.postprocess()


class AttributeDrainageFluxes:
    def __init__(self, config_file_path: Path) -> None:
        """
        Args:
            config_file_path: path to toml config file
        """

        self.config_root = load_config(config_file_path)
        self.config = self.config_root.general
        self.config_xdr = self.config_root.xroutingdrainage
        self.dir = Path(self.config.runDirRoot)
        self.output_file = self.dir.joinpath("LineicMassDra.csv")
        self.input_dir = Path(self.config.inputDir)

        self.mass_flux_per_field_file = self.config_xdr.fieldsMassFluxFile
        self.xdrainagerouting = self.config_xdr.xdrainagerouting_file
        self.fields_area_file = self.config_xdr.fieldsAreaFile
        self.reaches_lengths_file = self.config_xdr.reachesLengthFile
        self.reaches = self.config.reaches

        self.HML_firstRow = None
        self.HML_nRow = None
        self.HML_skipRows = [1]

    def setup(self):
        fields_flux_time = pd.read_csv(
            Path(self.mass_flux_per_field_file),
            sep=",",
            skiprows=[1],
        )
        self.time = list(fields_flux_time.Time)
        self.fields_flux_data = fields_flux_time.drop("Time", axis=1)
        self.fields_area = pd.read_csv(Path(self.fields_area_file), sep=",")
        self.reaches_length = pd.read_csv(Path(self.reaches_lengths_file), sep=",")

        self.xdrainagerouting = self.load_dataframe_as_array(
            self.input_dir, self.xdrainagerouting
        )

        self.lineicmassdra_file = self.attribute_fluxes_file(
            self.fields_flux_data,
            self.xdrainagerouting,
            self.fields_area,
            self.reaches_length,
            self.reaches,
            self.time,
        )

    def prepare_mass_flux_table(self):
        MassFluxLoadingsTable = pd.read_csv(
            os.path.join(self.generalConfig["inputDir"], self.mass_flux_per_field_file),
            header=[0],
            parse_dates=[0],
            infer_datetime_format=True,
            skiprows=self.HML_skipRows,
        )
        if self.HML_nRow is None:
            filter = (MassFluxLoadingsTable.Time >= self.startTime) & (
                MassFluxLoadingsTable.Time <= self.endTime + dt.timedelta(hours=1)
            )
            MassFluxLoadingsTable = MassFluxLoadingsTable.loc[filter,]
            MassFluxLoadingsTable.reset_index(drop=True, inplace=True)
            self.HML_firstRow = filter.idxmax() + 2
            self.HML_nRow = filter.sum()
            self.HML_skipRows = lambda x: not (
                x == 0
                or (x >= self.HML_firstRow and (x <= self.HML_firstRow + self.HML_nRow))
            )
        return MassFluxLoadingsTable

    # def get_time(self, path):

    def load_dataframe_as_array(self, input_dir: Path, file: str):
        """returns the matrix as an array with no columns or index names"""
        df = pd.read_csv(file, sep=",")
        df = df.drop(df.columns[0], axis=1).to_numpy()
        return df

    def attribute_fluxes_file(
        self, fields_flux, matrix_flux, fields_area, reaches_length, reaches_names, time
    ):
        """returns the fluxes per reach per meter"""

        df = pd.DataFrame(columns=reaches_names)

        for i in np.arange(len(time)):
            flux_per_reach = np.matmul(
                matrix_flux,
                np.multiply(
                    np.array(fields_flux.iloc[i]), np.array(fields_area["area_m2"])
                ),
            )
            lineic_flux_per_reach = np.divide(
                flux_per_reach, np.array(reaches_length["length_m"])
            )
            df = pd.concat(
                [df, pd.DataFrame(data=[lineic_flux_per_reach], columns=reaches_names)]
            )  # how are reaches_names obtained HAS to be the name of the columns of this input
        df.index = np.arange(len(time))
        time_df = pd.DataFrame(data=time)
        lineicmassdra = pd.concat([time_df, df], axis=1).set_index(0)

        with open(self.output_file, "w") as f:
            f.write(f"Time,LISTREACHES\n")
            f.write("-, len(listreaches)*[g/m/h]\n")
            f.write(lineicmassdra.to_string(index_names=False, header=False))

    def create_array(self, dict, list):
        """returns an array of values for a given dictionnary and list"""
        return [dict[element] for element in list]


if __name__ == "__main__":
    main(Path(sys.argv[1]))

    # def postprocess(self) -> None :
    #    continue
"""
Interface
Provides flux data to system per reach
"""
