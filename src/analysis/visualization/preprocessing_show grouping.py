import helpers.api_helpers as ahp
import helpers.pipe_helpers as php
import os
import json
import pandas as pd
from datetime import datetime, timedelta

one_week_ago = datetime.now() - timedelta(weeks=3)

if (
    not os.path.exists("./cache/cable_probes_values_from_db.parquet")
    or datetime.fromtimestamp(
        os.path.getmtime("./cache/cable_probes_values_from_db.parquet")
    )
    < one_week_ago
):
    cable_probes = pd.DataFrame()
    pointer = 0

    while True:
        data = ahp.read_from_windchill_per_node("TSGCableProbes", pointer)
        json_data = json.loads(data)
        if "@odata.nextLink" not in json_data:
            break
        json_data_value = pd.DataFrame(json_data["value"])
        cable_probes = pd.concat(
            [cable_probes, json_data_value], ignore_index=True
        )  # TODO: Erst in Liste speichern und dann concat?

        pointer = json_data["@odata.nextLink"].split("=")[1]
    cable_probes.to_parquet("./cache/cable_probes_from_db.parquet")

    unique_cable = cable_probes["Name"].unique()
    cable_probes_values = pd.DataFrame()
    counter = 0
    for name in unique_cable:
        counter += 1
        data = ahp.read_from_windchill_per_name(name)
        json_data = json.loads(data)
        json_data_value = pd.DataFrame(json_data["value"])
        cable_probes_values = pd.concat(
            [cable_probes_values, json_data_value], ignore_index=True
        )
    cable_probes_values.to_parquet("./cache/cable_probes_values_from_db.parquet")

cable_probes_values = pd.read_parquet("./cache/cable_probes_values_from_db.parquet")


cable_probes_pipe = (
    cable_probes_values.pipe(php.start_pipeline)
    .pipe(
        php.drop_columns,
        column_names=[
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
            "TSG.ProjectNo",
            "TSG.PackagingTypeCode",
            "TSG.ProductionLocation",
            "TSG.PackagingtypeText",
            "TSG.Application",
            "TSG.BranchApplication",
            "TSG.CustomerPartNo",
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
        column_names=[("KTY_Class", r"(\.)", "-"), ("TSG.ConnectorType", r"\s", "_")],
    )
    .pipe(
        php.aggregate_columns,
        new_column="Sensorclass",
        column_names=["PT_Type", "PT_Class", "Widerstand", "KTY_Class"],
    )
    .pipe(php.replace_whitespace, column_names=["Sensorclass", "TSG.ConnectorType"])
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

print(cable_probes_pipe.info())

cable_probes_unique_maxTemp = php.group_by_and_count(
    cable_probes_pipe, column_name="TSG.OperatingTemperatureMax"
)
cable_probes_unique_minTemp = php.group_by_and_count(
    cable_probes_pipe, column_name="TSG.OperatingTemperatureMin"
)

""" cable_grouped = cable_probes_pipe.groupby(
    [
        "TSG.OperatingTemperatureMin",
        "TSG.OperatingTemperatureMax",
        "TSG.WithCable",
        "TSG.LengthSleeve",
        "TSG.WithFlatSpring",
        "TSG.SensorType",
        "TSG.LengthCable",
        "TSG.OuterDiameterSleeveTip",
        "TSG.ConnectorType",
        "TSG.CableDetails",
    ]
).size() """

""" columns = ['ID', 'BENENNUNG', 'Identity', 'Latest', 'Name', 'Number', 'SAPMATNR',
       'TSG.OuterDiameterSleeveTip', 'TSG.WithFlatSpring',
       'TSG.ConnectionTypeSleeveCable', 'TSG.IPProtectionClass',
       'TSG.WithCable', 'TSG.SensorType', 'TSG.ElectricalConnection',
       'TSG.OperatingTemperatureMax', 'TSG.LengthCable',
       'TSG.ConnectorTechnology', 'TSG.ConnectorType', 'TSG.LengthSleeve',
       'TSG.OperatingTemperatureMin', 'TSG.ConnectionTypeSensorWire',
       'TSG.CableDetails', 'TSG.SensorHeatTransfer', 'TSG.CircuitType'] """

columns = [
    "TSG.OuterDiameterSleeveTip",
    "TSG.WithFlatSpring",
    "TSG.ConnectionTypeSleeveCable",
    "TSG.IPProtectionClass",
    "TSG.WithCable",
    "TSG.SensorType",
    "TSG.ElectricalConnection",
    "TSG.OperatingTemperatureMax",
    "TSG.LengthCable",
    "TSG.ConnectorTechnology",
    "TSG.ConnectorType",
    "TSG.LengthSleeve",
    "TSG.OperatingTemperatureMin",
    "TSG.ConnectionTypeSensorWire",
    "TSG.SensorHeatTransfer",
    "TSG.CircuitType",
    "Sensorclass",
    "TSG.CableDetails",
    "TSG.MaterialCableJacket",
    "TSG.MaterialSleeveHousing",
]

columns_core = [
    "TSG.OperatingTemperatureMin",
    "TSG.OperatingTemperatureMax",
    "TSG.LengthSleeve",
    "TSG.OuterDiameterSleeveTip",
    "TSG.SensorType",
    "TSG.LengthCable",
    "TSG.ConnectorType",
    "Sensorclass",
]

columns_side = [
    "TSG.ConnectionTypeSleeveCable",
    "TSG.WithFlatSpring",
    "TSG.IPProtectionClass",
    "TSG.ElectricalConnection",
    "TSG.ConnectorTechnology",
    "TSG.ConnectionTypeSensorWire",
    "TSG.SensorHeatTransfer",
    "TSG.CircuitType",
    "TSG.WithCable",
    "TSG.CableDetails",
    "TSG.MaterialCableJacket",
    "TSG.MaterialSleeveHousing",
]

# This loop prints the values of the steps for the core columns
""" columns_iteration = []
for column in columns_core:
    columns_iteration.append(column)
    print("Grouped: ",columns_iteration)
    cable_grouped = cable_probes_pipe.groupby(columns_iteration).size()
    pd.DataFrame(cable_grouped).to_parquet('./cache/cable_probes_grouped_table.parquet')
    print("Shape:",cable_grouped.shape)
    print("Max Same: ",cable_grouped.max(),"\n")
    unique = len(cable_grouped[cable_grouped ==1])
    print("Unique Combinations: ", unique ) """

# This loop prints the different variations of every collumn
""" for column in columns:
    print(column)
    cable_grouped = cable_probes_pipe.groupby(column).size()
    pd.DataFrame(cable_grouped).to_parquet('./cache/cable_probes_grouped_table.parquet')
    print("Shape:",cable_grouped.shape)
    print("Max Same: ",cable_grouped.max())
    unique = len(cable_grouped[cable_grouped ==1])
    print("Unique Combinations: ", unique ) """

# This loop prints the different variations of the core values in addition of one side value
""" columns_iteration = columns_core
for column in columns_side:
    columns_iteration.append(column)
    print("Grouped: ",column)
    cable_grouped = cable_probes_pipe.groupby(columns_iteration).size()
    pd.DataFrame(cable_grouped).to_parquet('./cache/cable_probes_grouped_table.parquet')
    print("Shape:",cable_grouped.shape)
    print("Max Same: ",cable_grouped.max())
    columns_iteration.pop()
    unique = len(cable_grouped[cable_grouped ==1])
    print("Unique Combinations: ", unique,"\n") """

# This loop prints the different variation with one more sidevalue per iteration
columns_iteration = columns_core
for column in columns_side:

    columns_iteration.append(column)
    print("Grouped: ", columns_iteration)
    cable_grouped = cable_probes_pipe.groupby(columns_iteration).size()
    pd.DataFrame(cable_grouped).to_parquet("./cache/cable_probes_grouped_table.parquet")
    print("Shape:", cable_grouped.shape)
    print("Max Same: ", cable_grouped.max())
    unique = len(cable_grouped[cable_grouped == 1])
    print("Unique Combinations: ", unique, "\n")


""" import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.add_subplot()
ax.hist(cable_grouped, bins=160, log=True)
ax.set_xlabel("Count Used")
ax.set_ylabel("Count distribution") """
