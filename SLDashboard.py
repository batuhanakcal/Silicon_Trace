import streamlit as st
import pandas as pd 
import plotly.express as px 
import os 
import warnings
warnings.filterwarnings('ignore') # This helps with telling python to ignore warnings

# Setting the page layout
st.set_page_config(page_title ="SiliconTrace", page_icon = ":factory",layout = "wide")

# Setting the title of the web app
st.title(":factory: SiliconTrace")

# Styling the title by adding some padding
st.markdown(
    '<style>div.block-container{padding-top: 3rem;}</style>', unsafe_allow_html = True
)

# A Button for users to upload data 
fl = st.file_uploader(":file_folder: upload a file", type = (["csv", "txt", "xlsx","xls"]))
if fl is not None: 
    filename = fl.name
    st.write(filename)
    df = pd.read_csv(fl, encoding = "ISO-8859-1")
else:
    # Use absolute path for the default file
    default_file = ""
    if os.path.exists(default_file):
        df = pd.read_csv(default_file, encoding = "ISO-8859-1")
    else:
        st.error(f"Please upload a file or ensure {default_file} exists.")
        st.stop()

# Store the original dataframe
original_df = df.copy()

# Creating a data card 
col1, col2 = st.columns((2))

# Check for Year column
if 'Year' not in df.columns:
    st.error("Missing required column: Year")
    st.stop()

# Convert Year to datetime if it's not already
df['Year'] = pd.to_datetime(df['Year'], format='%Y')

# Get the actual min and max dates from your data
startDate = df['Year'].min()
endDate = df['Year'].max()

# Display date pickers with your data's date range
with col1:
    date1 = st.date_input('Start Date', startDate, min_value=startDate, max_value=endDate)
with col2:
    date2 = st.date_input('End Date', endDate, min_value=startDate, max_value=endDate)

# Filter the dataframe based on selected dates
mask = (df['Year'].dt.date >= date1) & (df['Year'].dt.date <= date2)
filtered_df = df.loc[mask]

# Format the Year column to show only the year
filtered_df['Year'] = filtered_df['Year'].dt.year

# Create sidebar filters
st.sidebar.header("Filters")

# Function to identify categorical columns
def is_categorical(series):
    # Check if the column has relatively few unique values compared to its length
    n_unique = series.nunique()
    n_total = len(series)
    return n_unique < n_total * 0.5  # If unique values are less than 50% of total, consider it categorical

# Get categorical columns
categorical_columns = [col for col in filtered_df.columns if is_categorical(filtered_df[col])]

# Let user select which columns to filter by
st.sidebar.subheader("Select Columns to Filter")
selected_columns = st.sidebar.multiselect(
    "Choose columns to filter by:",
    options=categorical_columns,
    default=categorical_columns[:2] if len(categorical_columns) > 0 else []
)

# Create filters for selected columns
for column in selected_columns:
    st.sidebar.subheader(f"Filter by {column}")
    selected_values = st.sidebar.multiselect(
        f"Select {column}:",
        options=sorted(filtered_df[column].unique()),
        key=f"filter_{column}"
    )
    if selected_values:
        filtered_df = filtered_df[filtered_df[column].isin(selected_values)]

# Display the filtered data in a scrollable container
st.write("Filtered Data:")

# Create a container with fixed height and scrolling
st.markdown("""
    <style>
        .dataframe-container {
            height: 400px;
            overflow-y: scroll;
        }
    </style>
""", unsafe_allow_html=True)

# Display the dataframe in the scrollable container
st.dataframe(
    filtered_df,
    height=400,  # Fixed height in pixels
    use_container_width=True  # Use full width of the container
)

# Display date range information
st.write(f"Data range: {startDate.year} to {endDate.year}")


