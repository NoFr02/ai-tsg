from cableprobe import CableProbe
import pandas as pd


class Recommender:

    def __init__(self, probes_compare: pd.DataFrame):
        """
        Initialize the Recommender class with a given dataframe.

        Parameters:
        - probes_compare: DataFrame containing the probes to compare against.
        """
        self.df_compare = probes_compare  # Store the comparison dataframe
        probes = []
        # Iterate over each probe in the comparison dataframe and create CableProbe objects
        for index, probe in probes_compare.iterrows():
            probes.append(
                CableProbe(
                    (probe["TSG.SensorType"], probe["Sensorclass"]),
                    float(probe["TSG.OperatingTemperatureMax"]),
                    float(probe["TSG.OuterDiameterSleeveTip"]),
                    float(probe["TSG.LengthSleeve"]),
                    float(probe["TSG.LengthCable"]),
                    probe["TSG.ConnectorType"],
                    sapmatnr=probe["SAPMATNR"],
                    min_temp=float(probe["TSG.OperatingTemperatureMin"]),
                )
            )
        self.probes_compare = probes  # Store the list of CableProbe objects

    def evaluate(
        self, probe_required: CableProbe, return_count=1
    ) -> dict[CableProbe, (float, int)]:
        """
        Evaluate the best matching probes.

        Parameters:
        - probe_required: The required probe to compare against.
        - return_count: The number of best matches to return.

        Returns:
        - A dictionary of dummy best matching probes with a rating of 1 and rank 1.
        """
        dummy_return = {}
        for i in range(return_count):
            dummy_return[self.probes_compare[i]] = (1, 1)
        return dummy_return

    def replace_lowest_if_higher(
        self, key: CableProbe, value: float, data: dict[CableProbe, float], return_count
    ) -> dict[CableProbe, float]:
        """
        Replace the lowest value in the dictionary if the new value is higher.

        Parameters:
        - key: The probe key to be considered.
        - value: The new value to compare.
        - data: The dictionary of existing probes and their values.
        - return_count: The maximum number of items to keep in the dictionary.

        Returns:
        - The updated dictionary.
        """
        if len(data) < return_count:
            data[key] = value
            return data
        min_key = min(data, key=data.get)
        if value > data[min_key]:
            del data[min_key]
            data[key] = value
        return data

    def replace_highest_if_lower(
        self, key: CableProbe, value: float, data: dict[CableProbe, float], return_count
    ) -> dict[CableProbe, float]:
        """
        Replace the highest value in the dictionary if the new value is lower.

        Parameters:
        - key: The probe key to be considered.
        - value: The new value to compare.
        - data: The dictionary of existing probes and their values.
        - return_count: The maximum number of items to keep in the dictionary.

        Returns:
        - The updated dictionary.
        """
        if len(data) < return_count:
            data[key] = value
            return data
        max_key = max(data, key=data.get)
        if value < data[max_key]:
            del data[max_key]
            data[key] = value
        return data

    def calc_rank(
        self, data: dict[CableProbe, float], reverse=True
    ) -> dict[CableProbe, (float, int)]:
        """
        Calculate the rank of each probe based on its value.

        Parameters:
        - data: The dictionary of probes and their values.
        - reverse: Boolean indicating if the sorting should be in reverse order.

        Returns:
        - A dictionary of probes with their values and ranks.
        """
        sorted_dict = sorted(data.items(), key=lambda item: item[1], reverse=reverse)
        ranked_data = {}
        rank = 1
        for key in sorted_dict:
            ranked_data[key[0]] = (key[1], rank)
            rank += 1
        return ranked_data

    def calc_rating_cable(self, len_compare: float, deviation=500) -> float:
        """
        Calculate the rating for cable length comparison.

        Parameters:
        - len_compare: The length of the cable to compare.
        - deviation: The acceptable deviation in length.

        Returns:
        - The rating for the cable length.
        """
        difference = len_compare - self.probe_required.len_cable
        if 0 <= difference <= deviation:
            steps = 0.5 / deviation
            return 1 - steps * difference
        else:
            return 0

    def calc_rating_len_sleeve(self, len_compare: float, rel_deviation=0.1) -> float:
        """
        Calculate the rating for sleeve length comparison.

        Parameters:
        - len_compare: The length of the sleeve to compare.
        - rel_deviation: The acceptable relative deviation in length.

        Returns:
        - The rating for the sleeve length.
        """
        if self.probe_required.len_sleeve == 0:
            return 1 if len_compare == 0 else 0
        deviation = abs(self.probe_required.len_sleeve - len_compare)
        acceptable_range = rel_deviation * self.probe_required.len_sleeve
        if deviation <= acceptable_range:
            score = 0.5 + 0.5 * (1 - (deviation / acceptable_range))
        else:
            score = 0
        return score

    def calc_rating_temp(self, temp_compare: float, isMin=True) -> float:
        """
        Calculate the rating for temperature comparison.

        Parameters:
        - temp_compare: The temperature to compare.
        - isMin: Boolean indicating if the comparison is for minimum temperature.

        Returns:
        - The rating for the temperature.
        """
        max_diff = 100
        temp_required = (
            self.probe_required.min_temp if isMin else self.probe_required.max_temp
        )
        diff = abs(temp_compare - temp_required)
        similarity = max(0, 1 - (diff / max_diff))
        if (isMin and temp_compare <= temp_required) or (
            not isMin and temp_compare >= temp_required
        ):
            return similarity
        else:
            return 0

    def calc_rating_diam_sleeve(self, diam_compare: float) -> float:
        """
        Calculate the rating for diameter sleeve comparison.

        Parameters:
        - diam_compare: The diameter of the sleeve to compare.

        Returns:
        - The rating for the diameter sleeve.
        """
        return 1 if self.probe_required.diameter_sleeve == diam_compare else 0

    def calc_rating_sensor(self, type_compare: tuple) -> float:
        """
        Calculate the rating for sensor type comparison.

        Parameters:
        - type_compare: The sensor type to compare.

        Returns:
        - The rating for the sensor type.
        """
        rating = 0
        if self.probe_required.sensor_type[0] == type_compare[0]:  # Compare Sensortype
            rating += 0.75
            if (
                self.probe_required.sensor_type[1] == type_compare[1]
            ):  # Compare Sensordetails
                rating += 0.25
        return rating

    def calc_rating_con_type(self, type_compare: str) -> float:
        """
        Calculate the rating for connector type comparison.

        Parameters:
        - type_compare: The connector type to compare.

        Returns:
        - The rating for the connector type.
        """
        return 1 if self.probe_required.con_type == type_compare else 0
