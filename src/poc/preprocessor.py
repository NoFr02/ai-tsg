import os
from datetime import datetime, timedelta
import pandas as pd
import helpers.api_helpers as ahp
import helpers.pipe_helpers as php
import json


class Preprocessor:
    def __init__(
        self, pathCache: str, timeCache=1, useCache=True, one_hot_encoded=False
    ):
        """
        Initialize the Preprocessor class with given parameters.

        Parameters:
        - pathCache: The path to the cache directory.
        - timeCache: The cache duration in days.
        - useCache: Boolean to indicate if caching should be used.
        - one_hot_encoded: Boolean to indicate if one-hot encoding should be applied.
        """
        self.useCache = useCache
        self.pathCache = pathCache
        self.daysAgo = datetime.now() - timedelta(days=timeCache)
        self.one_hot_encoded = one_hot_encoded

    def process(self, classification_node: str) -> pd.DataFrame:
        """
        Process data for the given classification node and return a DataFrame.

        Parameters:
        - classification_node: The classification node to process.

        Returns:
        - A DataFrame with processed data.
        """

        # Define the path to the cache file based on the classification node
        cache_file = (
            self.pathCache + "/" + classification_node + "_values_from_db.parquet"
        )

        # Check if the cache file exist
        if not os.path.exists(cache_file):
            cable_probes = pd.DataFrame()
            pointer = 0
            while True:
                data = ahp.read_from_windchill_per_node(classification_node, pointer)
                json_data = json.loads(data)

                # Extract data and concatenate to the main DataFrame
                json_data_value = pd.DataFrame(json_data["value"])
                cable_probes = pd.concat(
                    [cable_probes, json_data_value], ignore_index=True
                )

                # Extract data and concatenate to the main DataFrame
                if "@odata.nextLink" not in json_data:
                    break
                pointer = json_data["@odata.nextLink"].split("=")[1]

            # Extract unique cable names
            unique_cable = cable_probes["Name"].unique()
            cable_probes_values = pd.DataFrame()

            # Read data for each unique cable name
            for name in unique_cable:
                data = ahp.read_from_windchill_per_name(name)
                json_data = json.loads(data)
                json_data_value = pd.DataFrame(json_data["value"])
                cable_probes_values = pd.concat(
                    [cable_probes_values, json_data_value], ignore_index=True
                )
            # Save the concatenated DataFrame to the cache file
            cable_probes_values.to_parquet(cache_file)

        # Check if the cache file is older than the specified duration
        elif datetime.fromtimestamp(os.path.getmtime(cache_file)) < self.daysAgo:
            cable_probes_modified = pd.DataFrame()
            pointer = 0
            cache_age_str = datetime.fromtimestamp(
                os.path.getmtime(cache_file)
            ).strftime("%Y-%m-%dT00:00:00Z")
            while True:
                data = ahp.read_from_windchill_last_modified(cache_age_str, pointer)
                json_data = json.loads(data)
                json_data_value = pd.DataFrame(json_data["value"])
                cable_probes_modified = pd.concat(
                    [cable_probes_modified, json_data_value], ignore_index=True
                )
                if "@odata.nextLink" not in json_data:
                    break
                pointer = json_data["@odata.nextLink"].split("=")[2]
            # Read the existing cache file
            cable_probes_values = pd.read_parquet(cache_file)

            # Iterate over the rows of cable_probes_modified DataFrame
            for index, cable in cable_probes_modified.iterrows():
                # Skip if 'Classification' is not present
                if not cable["Classification"]:
                    continue

                # Skip if the classification node does not match
                if (
                    cable["Classification"][0]["ClfNodeInternalName"]
                    != classification_node
                ):
                    continue

                # Read data from Windchill for the given SAPMATNR
                data = ahp.read_from_windchill_per_sapnr(cable["SAPMATNR"])
                json_data = json.loads(data)
                json_data_value = pd.DataFrame(json_data["value"])
                # Remove rows from cable_probes_values where SAPMATNR is in json_data_value
                cable_probes_values = cable_probes_values[
                    ~cable_probes_values["SAPMATNR"].isin(json_data_value["SAPMATNR"])
                ]

                # Append the new data to cable_probes_values
                cable_probes_values = pd.concat(
                    [cable_probes_values, json_data_value], ignore_index=True
                )

            # Save the updated DataFrame back to the parquet file
            cable_probes_values.to_parquet(cache_file)
            print("Exported DataFrame Shape:", cable_probes_values.shape)

        # Re-read the cached parquet file into a DataFrame
        cable_probes_values = pd.read_parquet(cache_file)

        cable_probes_pipe = (
            cable_probes_values.pipe(php.start_pipeline)
            .pipe(
                php.drop_columns,
                column_names=[
                    "ID",
                    "BENENNUNG",
                    "Identity",
                    "Latest",
                    "Name",
                    "Number",
                    "CreatedOn",
                    "LastModified",
                    "AlternateNumber",
                    "AssemblyMode",
                    "BESCHREIBUNG",
                    "BOMType",
                    "CabinetName",
                    "CabinetName@PTC.AccessException",
                    "ChangeStatus",
                    "CheckOutStatus",
                    "CheckoutState",
                    "Comments",
                    "ConfigurableModule",
                    "CreatedBy",
                    "DESCRIPTIONENG",
                    "DefaultTraceCode",
                    "DefaultUnit",
                    "ESTIMATEDPRICE",
                    "EndItem",
                    "FolderLocation",
                    "FolderLocation@PTC.AccessException",
                    "FolderName",
                    "FolderName@PTC.AccessException",
                    "GatheringPart",
                    "GeneralStatus",
                    "HANDELSNAME",
                    "LifeCycleTemplateName",
                    "LifeCycleTemplateName@PTC.AccessException",
                    "MATERIAL",
                    "MATERIALFARBE",
                    "ModifiedBy",
                    "ObjectType",
                    "OrganizationReference",
                    "PhantomManufacturingPart",
                    "Revision",
                    "ShareStatus",
                    "Source",
                    "State",
                    "Supersedes",
                    "TypeIcon",
                    "Version",
                    "VersionID",
                    "View",
                    "WorkInProgressState",
                ],
            )
            .pipe(php.get_value_from_class)
            .pipe(
                php.drop_columns,
                column_names=[
                    "Classification",
                    "TSG.WithFlatSpring",
                    "TSG.ConnectionTypeSleeveCable",
                    "TSG.WithCable",
                    "TSG.CableDetails",
                    "TSG.IPProtectionClass",
                    "TSG.ProjectNo",
                    "TSG.ProjectNo",
                    "TSG.PackagingTypeCode",
                    "TSG.ElectricalConnection",
                    "TSG.ProductionLocation",
                    "TSG.PackagingtypeText",
                    "TSG.Application",
                    "TSG.BranchApplication",
                    "TSG.ConnectorTechnology",
                    "TSG.MaterialCableJacket",
                    "TSG.CustomerPartNo",
                    "TSG.ConnectionTypeSensorWire",
                    "TSG.DeveloppedforCustomer",
                    "TSG.MaterialSleeveHousing",
                    "TSG.SensorHeatTransfer",
                    "TSG.CircuitType",
                    "TSG.description",
                ],
            )
            .pipe(
                php.extract_from_regex,
                column_names=[
                    ("PT_Type", "TSG.SensorDetails", r".*Pt(\d+)"),
                    ("PT_Class", "TSG.SensorDetails", r"(class\s?\w?)"),
                    (
                        "Widerstand",
                        "TSG.SensorDetails",
                        r"R\d+=\s*(\d+[,.]?\d*)\s*[kK][oO][hH][mM]",
                    ),
                    ("B_Wert", "TSG.SensorDetails", r"(B\d+/\d+\s?=\s*\d+\s*K)"),
                    ("KTY_Class", "TSG.SensorDetails", r"KTY\s?(\d+[.-]?\d+)"),
                ],
            )
            .pipe(
                php.replace_character,
                column_names=[
                    ("KTY_Class", r"(\.)", "-"),
                    ("TSG.ConnectorType", r"\s", "_"),
                ],
            )
            .pipe(
                php.aggregate_columns,
                new_column="Sensorclass",
                column_names=["PT_Type", "PT_Class", "Widerstand", "KTY_Class"],
            )
            .pipe(
                php.replace_whitespace,
                column_names=["Sensorclass", "TSG.ConnectorType"],
            )
            .pipe(
                php.drop_columns,
                column_names=[
                    "PT_Type",
                    "PT_Class",
                    "Widerstand",
                    "B_Wert",
                    "KTY_Class",
                    "TSG.SensorDetails",
                ],
            )
            .pipe(
                php.change_dtype,
                column_names=(
                    ("TSG.OuterDiameterSleeveTip", "float"),
                    ("TSG.LengthCable", "float"),
                    ("TSG.LengthSleeve", "float"),
                    ("TSG.OperatingTemperatureMax", "int32"),
                    ("TSG.OperatingTemperatureMin", "int32"),
                ),
            )
        )
        # Set original same as probes to prevent errors
        cable_probes_original = cable_probes_pipe

        # Apply one-hot encoding if specified
        if self.one_hot_encoded:
            cable_probes_pipe, cable_probes_original = cable_probes_pipe.pipe(
                php.start_pipeline
            ).pipe(
                php.one_hot_encoding,
                column_names=["TSG.SensorType", "Sensorclass", "TSG.ConnectorType"],
            )

        return cable_probes_pipe, cable_probes_original
