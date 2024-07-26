from cableprobe import CableProbe
import pandas as pd
from helpers import pipe_helpers as php
from recommender import Recommender


class Evaluator:
    """
    The Evaluator class uses evaluation data to evaluate the different recommenders
    """

    def __init__(self, path_to_res: str, recommender: Recommender, scaler=None):
        self.eval_probes = pd.read_csv(
            path_to_res + "/input_evaluation_kabelfühler.csv", delimiter=";"
        )
        self.recommender = recommender
        self.scaler = scaler
        self.eval_probes = self.__preprocess()

    def calc(self, top_counter=1) -> float:
        """
        The function iterates through the evaldata and counts how often the SAPNr of the
        evaluationprobe gets hit by the recommender
        """

        hit_counter = 0
        all_scores = []
        for index, probe in self.eval_probes.iterrows():
            cable_probe = CableProbe(
                (probe["TSG.SensorType"], probe["Sensorclass"]),
                float(probe["TSG.OperatingTemperatureMax"]),
                float(probe["TSG.OuterDiameterSleeveTip"]),
                float(probe["TSG.LengthSleeve"]),
                float(probe["TSG.LengthCable"]),
                probe["TSG.ConnectorType"],
                sapmatnr=probe["SAPMATNR"],
                min_temp=float(probe["TSG.OperatingTemperatureMin"]),
            )
            result = self.recommender.evaluate(cable_probe, return_count=top_counter)
            scores = list(result.values())
            all_scores.append(scores)

            for probe in result.keys():
                found = False
                if cable_probe.sapmatnr == probe.sapmatnr:
                    found = True
                    hit_counter += 1
                    break
            if not found:
                pass

        accuracy = hit_counter / len(self.eval_probes)

        all_scores = [score[0] for sublist in all_scores for score in sublist]
        mean_score = sum(all_scores) / len(all_scores)
        return {"accuracy": accuracy, "mean_score": mean_score}

    def __preprocess(self):
        """
        This function preprocesses the evaluationdata with the help of the pipe-helper for pandas pipelines.
        """
        probes_processed = (
            self.eval_probes.pipe(php.start_pipeline)
            .pipe(php.replace_whitespace, column_names=["TSG.SensorType"])
            .pipe(
                php.replace_character,
                column_names=[
                    ("TSG.SensorType", r"(PT)", "Pt"),
                    ("TSG.ConnectorType", r"(Aderendhülsen)", "-"),
                    ("TSG.OuterDiameterSleeveTip", r"(,)", "."),
                    ("TSG.LengthCable", r"(,)", "."),
                ],
            )
            .pipe(
                php.extract_from_regex,
                column_names=[
                    ("PT_Type", "Sensorart", r"(\d+)(?:\s+class)?"),
                    ("PT_Class", "Sensorart", r"(class\s?\w?)"),
                    ("B_Wert", "Sensorart", r"(B\d+/\d+\s?=\s*\d+\s*K)"),
                    ("KTY_Class", "TSG.SensorType", r"KTY\s?(\d+[.-]?\d+)"),
                    ("NTC_Resistance", "Sensorart", r"(\d+[\.,]?\d*)k"),
                    ("TSG.SensorType", "TSG.SensorType", r"(KTY|.*)"),
                ],
            )
            .pipe(
                php.aggregate_columns,
                new_column="Sensorclass",
                column_names=["PT_Type", "PT_Class", "B_Wert", "KTY_Class"],
            )
            .pipe(php.replace_whitespace, column_names=["Sensorclass"])
            .pipe(
                php.drop_columns,
                column_names=[
                    "PT_Type",
                    "PT_Class",
                    "B_Wert",
                    "KTY_Class",
                    "NTC_Resistance",
                ],
            )
            .pipe(
                php.fillNaN_rows_with_zero, column_names=["TSG.OperatingTemperatureMin"]
            )
        )
        if self.scaler is not None:     # try if we normalize the data in preprocessor
            scale_columns = [
                "TSG.OuterDiameterSleeveTip",
                "TSG.OperatingTemperatureMax",
                "TSG.OperatingTemperatureMin",
                "TSG.LengthCable",
                "TSG.LengthSleeve",
            ]
            probes_processed[scale_columns] = self.scaler.transform(
                probes_processed[scale_columns]
            )

        return probes_processed
