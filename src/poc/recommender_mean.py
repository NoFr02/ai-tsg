from recommender import Recommender
from cableprobe import CableProbe
import pandas as pd


class Recommender_Mean(Recommender):

    def __init__(self, probes_compare: pd.DataFrame):
        """
        Initialize the Recommender_Mean class with a given dataframe.

        Parameters:
        - probes_compare: DataFrame containing the probes to compare against.
        """
        super().__init__(probes_compare)  # Initialize the parent class

    def evaluate(
        self, probe_required: CableProbe, return_count=1
    ) -> dict[CableProbe, (float, int)]:
        """
        Evaluate the best matching probes based on the mean of various ratings.

        Parameters:
        - probe_required: The required probe to compare against.
        - return_count: The number of best matches to return.

        Returns:
        - A dictionary of best matching probes with their ratings and ranks.
        """
        self.probe_required = probe_required  # Store the required probe
        best_probes = {}  # Dictionary to store the best probes

        # Iterate over each probe in the comparison dataframe
        for cableprobe in self.probes_compare:
            rating = self.__calc_rating_total_mean(
                cableprobe
            )  # Calculate the mean rating
            best_probes = super().replace_lowest_if_higher(
                cableprobe, rating, best_probes, return_count=return_count
            )

        # Calculate the rank of the best probes
        best_probes = super().calc_rank(best_probes)
        return best_probes

    def __calc_rating_total_mean(self, probe_compare: CableProbe) -> float:
        """
        Calculate the mean rating based on various attributes of the probe.

        Parameters:
        - probe_compare: The comparison probe to rate.

        Returns:
        - The mean rating of the probe.
        """
        rating = 0
        # Accumulate ratings for different attributes of the probe
        rating += super().calc_rating_sensor(probe_compare.sensor_type)
        rating += super().calc_rating_temp(probe_compare.min_temp, True)
        rating += super().calc_rating_temp(probe_compare.max_temp, False)
        rating += super().calc_rating_diam_sleeve(probe_compare.diameter_sleeve)
        rating += super().calc_rating_len_sleeve(probe_compare.len_sleeve)
        rating += super().calc_rating_cable(probe_compare.len_cable)
        rating += super().calc_rating_con_type(probe_compare.con_type)

        return rating / 7  # Return the mean rating
