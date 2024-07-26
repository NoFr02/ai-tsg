from recommender import Recommender
from cableprobe import CableProbe
import pandas as pd
from scipy.spatial import distance
import helpers.pipe_helpers as php


class Recommender_Cosine(Recommender):

    def __init__(self, probes_compare: pd.DataFrame, probes_original: pd.DataFrame):
        """
        Initialize the Recommender_Cosine class with given dataframes.

        Parameters:
        - probes_compare: DataFrame containing the probes to compare against.
        - probes_original: DataFrame containing the original probes.
        """
        super().__init__(probes_original)  # Initialize the parent class
        self.df_compare = probes_compare  # Store the comparison dataframe

    def evaluate(
        self, probe_required: CableProbe, return_count=1
    ) -> dict[CableProbe, (float, int)]:
        """
        Evaluate the best matching probes based on cosine similarity.

        Parameters:
        - probe_required: The required probe to compare against.
        - return_count: The number of best matches to return.

        Returns:
        - A dictionary of best matching probes with their ratings and ranks.
        """
        self.probe_required = probe_required  # Store the required probe
        best_probes = {}  # Dictionary to store the best probes

        # Iterate over each probe in the comparison dataframe
        for index, probe in self.df_compare.iterrows():
            rating = self.__calc_rating_total_nearest(
                probe
            )  # Calculate the cosine similarity
            best_probes = super().replace_highest_if_lower(
                self.probes_compare[index],
                rating,
                best_probes,
                return_count=return_count,
            )

        # Calculate the rank of the best probes
        best_probes = super().calc_rank(best_probes, reverse=False)
        return best_probes

    def __calc_rating_total_nearest(self, probe_compare: pd.Series) -> float:
        """
        Calculate the cosine similarity rating between the required probe and a comparison probe.

        Parameters:
        - probe_compare: A series representing a comparison probe.

        Returns:
        - The cosine similarity rating.
        """
        df_probe_required = self.__encode_single_probe(
            self.probe_required
        )  # Encode the required probe
        rating = distance.cosine(
            probe_compare.drop(
                "SAPMATNR", axis=0
            ),  # Drop the SAPMATNR column for comparison
            df_probe_required.drop("SAPMATNR", axis=0),
        )
        return rating

    def __encode_single_probe(self, probe_required: CableProbe) -> pd.Series:
        """
        Encode a single probe into a format suitable for comparison.

        Parameters:
        - probe_required: The required probe to encode.

        Returns:
        - A series representing the encoded probe.
        """
        # Create a DataFrame from the required probe's attributes
        df_probe = pd.DataFrame(
            {
                "SAPMATNR": probe_required.sapmatnr,
                "TSG.OuterDiameterSleeveTip": probe_required.diameter_sleeve,
                "TSG.SensorType": probe_required.sensor_type[0],
                "Sensorclass": probe_required.sensor_type[1],
                "TSG.OperatingTemperatureMax": probe_required.max_temp,
                "TSG.LengthSleeve": probe_required.len_sleeve,
                "TSG.LengthCable": probe_required.len_cable,
                "TSG.OperatingTemperatureMin": probe_required.min_temp,
                "TSG.ConnectorType": probe_required.con_type,
            },
            index=[0],
        )

        # Apply a series of transformations to encode the DataFrame
        df_probe_encoded = (
            df_probe.pipe(php.start_pipeline)
            .pipe(
                php.one_hot_encoding,
                column_names=["TSG.ConnectorType", "TSG.SensorType", "Sensorclass"],
            )[0]
            .pipe(php.align_columns, column_names=self.df_compare.columns)
        )

        df_return = df_probe_encoded.iloc[0]  # Return the encoded probe as a series
        return df_return
