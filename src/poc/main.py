import sys
import pandas as pd
import random
from sklearn.preprocessing import MinMaxScaler
from preprocessor import Preprocessor
from recommender_mean import Recommender_Mean
from recommender_weighted import Recommender_Weighted
from recommender_cosine import Recommender_Cosine
from recommender_euclidean import Recommender_Euclidean
from cableprobe import CableProbe
from evaluator import Evaluator


def main(recommender_type, normalize, evaluate):
    # Normalize if required
    scaler = MinMaxScaler() if normalize else None

    # Create a Preprocessor instance
    one_hot_encoded = recommender_type in ("cosine", "euclidean")
    processor = Preprocessor("./cache", one_hot_encoded=one_hot_encoded)
    probes_encoded, probes_original = processor.process("TSGCableProbes")

    if normalize:
        # Define columns to be normalized
        scale_columns = [
            "TSG.OuterDiameterSleeveTip",
            "TSG.OperatingTemperatureMax",
            "TSG.OperatingTemperatureMin",
            "TSG.LengthCable",
            "TSG.LengthSleeve",
        ]
        # Fit the scaler on the selected columns and transform them
        scaler.fit(probes_encoded[scale_columns])
        probes_encoded[scale_columns] = scaler.transform(probes_encoded[scale_columns])
        # Save the processed data to a parquet file
        probes_encoded.to_parquet("./cache/TSGCableProbes_processed_from_db.parquet")

    # Initialize the recommender based on the argument
    if recommender_type == "cosine":
        recom = Recommender_Cosine(probes_encoded, probes_original)
    elif recommender_type == "euclidean":
        recom = Recommender_Euclidean(probes_encoded, probes_original)
    elif recommender_type == "mean":
        recom = Recommender_Mean(probes_encoded)
    elif recommender_type == "weighted":
        recom = Recommender_Weighted(probes_encoded)
    else:
        print(f"Unknown recommender type: {recommender_type}")
        return

    # Evaluate if required
    if evaluate:
        eval = Evaluator("./res", recom, scaler=scaler if normalize else None)
        print(
            f"{recommender_type.capitalize()} {'Normalized' if normalize else 'Unnormalized'}"
        )
        print("Top1", eval.calc(top_counter=1))
        print("Top3", eval.calc(top_counter=3))
        print("Top5", eval.calc(top_counter=5))
    else:
        print(
            f"Recommender {recommender_type.capitalize()} initialized without evaluation"
        )


def get_random_probe(probes: pd.DataFrame) -> CableProbe:
    # SensorType
    group = probes["TSG.SensorType"].unique()
    ran_value_sensor = group.item(random.randint(0, len(group) - 1))

    # SensorArt
    group = probes["Sensorclass"].unique()
    # Ensure the SensorArt is compatible with the SensorType
    while True:
        ran_value_sensor_class = group.item(random.randint(0, len(group) - 1))
        if "-" in ran_value_sensor_class and ran_value_sensor == "KTY":
            break
        elif str(ran_value_sensor_class).isdigit() and ran_value_sensor == "NTC":
            break
        elif "class" in ran_value_sensor_class and ran_value_sensor == "Pt":
            break
        elif (
            ran_value_sensor != "NTC"
            and ran_value_sensor != "Pt"
            and ran_value_sensor != "KTY"
        ):
            ran_value_sensor_class = ""
            break

    # MinTemp
    group = probes["TSG.OperatingTemperatureMin"].unique()
    ran_value_min = group.item(random.randint(0, len(group) - 1))

    # MaxTemp
    group = probes["TSG.OperatingTemperatureMax"].unique()
    # Ensure MaxTemp is greater than MinTemp
    while True:
        ran_value_max = group.item(random.randint(0, len(group) - 1))
        if ran_value_max > ran_value_min:
            break

    # OuterDiameter
    group = probes["TSG.OuterDiameterSleeveTip"].unique()
    ran_value_diam = group.item(random.randint(0, len(group) - 1))

    # LenSleeve
    group = probes["TSG.LengthSleeve"].unique()
    ran_value_len_sleeve = group.item(random.randint(0, len(group) - 1))

    # LenCable
    group = probes["TSG.LengthCable"].unique()
    ran_value_len_cable = group.item(random.randint(0, len(group) - 1))

    # ConType
    group = probes["TSG.ConnectorType"].unique()
    ran_value_con_type = group.item(random.randint(0, len(group) - 1))

    # Create a CableProbe instance with the random values
    ran_probe = CableProbe(
        (ran_value_sensor, ran_value_sensor_class),
        float(ran_value_max),
        float(ran_value_diam),
        float(ran_value_len_sleeve),
        float(ran_value_len_cable),
        ran_value_con_type,
        min_temp=float(ran_value_min),
    )

    return ran_probe


# Run the main function if this script is executed directly
if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) != 4:
        print("Usage: python main.py <recommender_type> <normalize> <evaluate>")
        print("recommender_type: cosine, euclidean, mean, weighted")
        print("normalize: true, false")
        print("evaluate: true, false")
        sys.exit(1)

    recommender_type = sys.argv[1].lower()
    normalize = sys.argv[2].lower() == "true"
    evaluate = sys.argv[3].lower() == "true"

    if recommender_type not in ("euclidean", "cosine") and normalize:
        print(
            "Normalization is just usable with cosine or euclidean recommendation"
        )
        sys.exit(1)

    main(recommender_type, normalize, evaluate)
