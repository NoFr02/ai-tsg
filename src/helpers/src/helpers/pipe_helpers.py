import datetime as dt
from functools import wraps
import pandas as pd
from sklearn import preprocessing
import os
from dotenv import load_dotenv

# load environnement variables
load_dotenv()


def log_step(func):
    """
    Decorator to log the time taken by a function to execute and the shape of the DataFrame it returns.

    Parameters:
    - func: The function to be decorated.

    Returns:
    - The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        tic = dt.datetime.now()
        try:
            result = func(*args, **kwargs)
            if type(result) is tuple:
                shape = result[0].shape
            else:
                shape = result.shape
        except Exception as e:
            result = f"Error: {str(e)}"
            print("Exception: ", result)
        time_taken = str(dt.datetime.now() - tic)
        if os.getenv("PRINT_PIPESTEPS") == "True":
            print(f"just ran step {func.__name__} shape={shape} took {time_taken}s")
        return result

    return wrapper


@log_step
def start_pipeline(dataf: pd.DataFrame) -> pd.DataFrame:
    """
    Starts the data processing pipeline by returning a copy of the DataFrame.

    Parameters:
    - dataf: The DataFrame to start the pipeline with.

    Returns:
    - A copy of the input DataFrame.
    """
    return dataf.copy()


@log_step
def encoding_labels(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Encodes specified columns using label encoding.

    Parameters:
    - dataf: The DataFrame containing the columns to encode.
    - column_names: List of column names to encode.

    Returns:
    - The DataFrame with the new encoded columns.
    """
    label_encoder = preprocessing.LabelEncoder()
    for column_name in column_names:
        dataf[column_name] = label_encoder.fit_transform(dataf[column_name])
    return dataf


@log_step
def one_hot_encoding(
    dataf: pd.DataFrame, column_names: list
) -> pd.DataFrame | pd.DataFrame:
    """
    Encodes specified columns using one-hot encoding.

    Parameters:
    - dataf: The DataFrame containing the columns to encode.
    - column_names: List of column names to encode.

    Returns:
    - The DataFrame with the new encoded columns and the original DataFrame.
    """
    dataf_encoded = pd.get_dummies(dataf, columns=column_names, dtype=int)
    return dataf_encoded, dataf


@log_step
def align_columns(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Aligns the encoded DataFrame with the other dataset by reindexing columns.

    Parameters:
    - dataf: The DataFrame containing the columns to align.
    - column_names: List of column names which are in the original dataset.

    Returns:
    - The DataFrame with the same columns as the original dataset.
    """
    dataf = dataf.reindex(columns=column_names, fill_value=0)
    return dataf


@log_step
def change_dtype(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Changes the data type of specified columns.

    Parameters:
    - dataf: The DataFrame containing the columns to change.
    - column_names: List of tuples with column names and their new data types.

    Returns:
    - The DataFrame with the changed column data types.
    """
    for column, dtype in column_names:
        dataf[column] = dataf[column].astype(dtype)
    return dataf


@log_step
def extract_from_regex(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Extracts data from specified columns using regex and creates new columns with the extracted data.

    Parameters:
    - dataf: The DataFrame containing the columns to extract from.
    - column_names: List of tuples with new column names, column names to extract from, and regex patterns.

    Returns:
    - The DataFrame with the new extracted columns.
    """
    for new_column, column_name, regex in column_names:
        dataf[new_column] = dataf[column_name].str.extract(regex)[0]
    return dataf


@log_step
def aggregate_columns(
    dataf: pd.DataFrame, new_column: str, column_names: list
) -> pd.DataFrame:
    """
    Aggregates specified columns into a new column with values joined by a semicolon.

    Parameters:
    - dataf: The DataFrame containing the columns to aggregate.
    - new_column: The name of the new column to create.
    - column_names: List of column names to aggregate.

    Returns:
    - The DataFrame with the new aggregated column.
    """
    # Validation to check if the column names exist in the DataFrame
    for column in column_names:
        if column not in dataf.columns:
            raise ValueError(f"Column '{column}' does not exist in the DataFrame.")

    # Define a custom aggregation function that skips NaN values
    def custom_agg(row):
        return ";".join([str(item) for item in row if pd.notna(item)])

    dataf[new_column] = dataf[column_names].agg(custom_agg, axis=1)
    return dataf


@log_step
def strip_column(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Strips whitespace from specified columns.

    Parameters:
    - dataf: The DataFrame containing the columns to strip.
    - column_names: List of column names to strip.

    Returns:
    - The DataFrame with stripped columns.
    """
    for column_name in column_names:
        dataf[column_name] = dataf[column_name].str.strip()
    return dataf


@log_step
def drop_columns(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Drops specified columns from the DataFrame.

    Parameters:
    - dataf: The DataFrame to drop columns from.
    - column_names: List of column names to drop.

    Returns:
    - The DataFrame with the specified columns dropped.
    """
    return dataf.drop(column_names, axis=1)


@log_step
def rename_column(dataf: pd.DataFrame, column_name: list, value: str) -> pd.DataFrame:
    """
    Renames a specified column in the DataFrame.

    Parameters:
    - dataf: The DataFrame containing the column to rename.
    - column_name: The name of the column to rename.
    - value: The new name for the column.

    Returns:
    - The DataFrame with the renamed column.
    """
    dataf.rename(columns={column_name: value}, inplace=True)
    return dataf


@log_step
def replace_whitespace(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Replaces whitespace in specified columns with empty strings.

    Parameters:
    - dataf: The DataFrame containing the columns to replace whitespace.
    - column_names: List of column names to process.

    Returns:
    - The DataFrame with replaced whitespace.
    """
    for column_name in column_names:
        dataf[column_name] = dataf[column_name].replace(
            to_replace=r"\s", value="", regex=True
        )
    return dataf


@log_step
def replace_character(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Replaces characters in specified columns using regex.

    Parameters:
    - dataf: The DataFrame containing the columns to replace characters.
    - column_names: List of tuples with column names, regex patterns, and replacement values.

    Returns:
    - The DataFrame with replaced characters.
    """
    for column_name, regex, value in column_names:
        dataf[column_name] = dataf[column_name].replace(
            to_replace=regex, value=value, regex=True
        )
    return dataf


@log_step
def filterNaN_rows(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Filters out rows with NaN values in specified columns.

    Parameters:
    - dataf: The DataFrame to filter.
    - column_names: List of column names to check for NaN values.

    Returns:
    - The DataFrame with rows containing NaN values filtered out.
    """
    dataf = dataf.dropna(subset=column_names)
    return dataf


@log_step
def fillNaN_rows_with_zero(dataf: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Fills NaN values in specified columns with zero.

    Parameters:
    - dataf: The DataFrame to process.
    - column_names: List of column names to fill NaN values.

    Returns:
    - The DataFrame with NaN values filled with zero.
    """
    for column_name in column_names:
        dataf[column_name] = dataf[column_name].fillna(0)
    return dataf


@log_step
def group_by_and_count(dataf: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Groups the DataFrame by a specified column and counts the occurrences.

    Parameters:
    - dataf: The DataFrame to group and count.
    - column_name: The column name to group by.

    Returns:
    - The DataFrame with grouped and counted values.
    """
    dataf = dataf.groupby(column_name).size()
    return dataf


@log_step
def get_value_from_class(dataf: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts values from the 'Classification' column and expands them into new columns.

    Parameters:
    - dataf: The DataFrame containing the 'Classification' column.

    Returns:
    - The DataFrame with expanded classification attributes.
    """
    for index, row in dataf.iterrows():
        row = row["Classification"]
        row = row.item()
        attributes = {
            attr["InternalName"]: attr["Value"]
            for attr in row["ClassificationAttributes"]
        }
        for key, value in attributes.items():
            dataf.at[index, key] = value
    return dataf


def split_X_Y(dataf: pd.DataFrame, feature: str) -> pd.DataFrame | pd.Series:
    """
    Splits the DataFrame into features (X) and target (Y).

    Parameters:
    - dataf: The DataFrame to split.
    - feature: The column name of the target feature.

    Returns:
    - The features DataFrame (X) and the target Series (Y).
    """
    dataf_X = dataf.drop([feature], axis=1)
    dataf_Y = dataf[feature]
    return dataf_X, dataf_Y


def test():
    """
    A simple test function to return a calculation result.

    Returns:
    - The result of the calculation (4 + 8).
    """
    return 4 + 8
