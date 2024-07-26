from recommender import Recommender
from cableprobe import CableProbe
import pandas as pd


class Recommender_Weighted(Recommender):

    def __init__(
        self,
        probes_compare: pd.DataFrame,
        weights={
            "sensor_type": 0.25,
            "temps": 0.2,
            "diam_sleeve": 0.15,
            "len_sleeve": 0.075,
            "len_cable": 0.075,
            "con_type": 0.05,
        },
    ):
        """
        Initialize the Recommender_Weighted class with given dataframes and weights.

        Parameters:
        - probes_compare: DataFrame containing the probes to compare against.
        - weights: A dictionary specifying the weights for different attributes.
        """
        super().__init__(probes_compare)  # Initialize the parent class
        self.weights = weights  # Store the weights for different attributes

    def evaluate(
        self, probe_required: CableProbe, return_count=1
    ) -> dict[CableProbe, float]:
        """
        Evaluate the best matching probes based on weighted ratings.

        Parameters:
        - probe_required: The required probe to compare against.
        - return_count: The number of best matches to return.

        Returns:
        - A dictionary of best matching probes with their ratings.
        """
        self.probe_required = probe_required  # Store the required probe
        best_probes = {}  # Dictionary to store the best probes

        # Iterate over each probe in the comparison dataframe
        for cableprobe in self.probes_compare:
            rating = self.__calc_rating_total_weighted(
                cableprobe
            )  # Calculate the weighted rating
            best_probes = super().replace_lowest_if_higher(
                cableprobe, rating, best_probes, return_count=return_count
            )

        # Calculate the rank of the best probes
        best_probes = super().calc_rank(best_probes)
        return best_probes

    def __calc_rating_total_weighted(self, probe_compare: CableProbe) -> float:
        """
        Calculate the weighted rating based on various attributes of the probe.

        Parameters:
        - probe_compare: The comparison probe to rate.

        Returns:
        - The weighted rating of the probe.
        """
        rating = 0
        # Accumulate weighted ratings for different attributes of the probe
        rating += self.weights["sensor_type"] * super().calc_rating_sensor(
            probe_compare.sensor_type
        )
        rating += self.weights["temps"] * super().calc_rating_temp(
            probe_compare.min_temp, True
        )
        rating += self.weights["temps"] * super().calc_rating_temp(
            probe_compare.max_temp, False
        )
        rating += self.weights["diam_sleeve"] * super().calc_rating_diam_sleeve(
            probe_compare.diameter_sleeve
        )
        rating += self.weights["len_sleeve"] * super().calc_rating_len_sleeve(
            probe_compare.len_sleeve
        )
        rating += self.weights["len_cable"] * super().calc_rating_cable(
            probe_compare.len_cable
        )
        rating += self.weights["con_type"] * super().calc_rating_con_type(
            probe_compare.con_type
        )

        return rating  # Return the total weighted rating
