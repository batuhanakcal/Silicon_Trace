import streamlit as st
import pandas as pd 
import plotly.express as px 
import os 
import plotly.graph_objects as go
import colorsys
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
# Placing the scenario modelling Guage
gauge_value = st.session_state.get("adjustment_slider", 0) 

# Creating and displaying the guage at the top center 
st.markdown("<h3 style = 'text_align: center;'>Scenario Adjustment</h3>", unsafe_allow_html = True)
# creating a guage with smooth color gradient from red to green
def red_to_green_gradient(n):
    colors = []
    for i  in range(n):
        ratio = i/(n-1)
        r, g, b = colorsys.hsv_to_rgb(0.33 * ratio, 1,1) #HSV hue from red (0) to green (0.33)
        color_str = f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})"
        colors.append({'range': [i * (100/n), (i+1)*(100 / n)], 'color': color_str})
    return colors

fig_guage = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = gauge_value,
    title = {'text': f"Emission Reduction Target %"},
    gauge = {
        'axis': {'range': [0,100]},
        'bar': {'color': "rgba(0,0,0,0)"},
        'steps': red_to_green_gradient(1000), #The more the steps the smoother the gradient 
        'threshold':{
            'line': {'color': "black", 'width': 6},
            'thickness': 1.0,
            'value': gauge_value
        }
    }
))
# Setting the size of the Guage 
fig_guage.update_layout(
    width = 500,
    height = 250,
    margin = dict(t=40, b = 10, l = 10, r = 10)
)
st.plotly_chart(fig_guage, use_container_width = True)

# A Button for users to upload data 
fl = st.sidebar.file_uploader(":file_folder: upload a file", type = (["csv", "txt", "xlsx","xls"]))
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
with st.expander(f"Raw Data {filename}"):
    st.write(df)
with st.expander(f"Charts"):
    # Date Picker Code
    # Creating a data card 
    col1, col2 = st.columns((2))
    filtered_df = df.copy() # Ensure this exists in all cases 
    # Detect a column with dataes 
    date_col = None
    for col in df.columns:
        if df[col].dtype in ['object', 'datetime64[ns]']: #Avoid numeric columns like "2020"
            try:
                converted = pd.to_datetime(df[col], errors = 'coerce', infer_datetime_format = True)
                # Require at least 50% of values to be valid dates
                if converted.notna().mean() > 0.5: #At least one valid datetime
                    df[col] = converted
                    date_col = col
                    break
            except Exception as e:
                continue
    # Fallback to 'Year' column if no proper date found
    if date_col is None and 'Year' in df.columns:
        try:
            df['Year'] = pd.to_datetime(df['Year'], format = '%Y', errors = 'coerce')
            if df['Year'].notna().sum() > 0:
                date_col = 'Year'
                df = df.dropna(subset = ['Year'])
                st.markdown("**Falback to 'Year' column for date filtering")
        except Exception: 
            pass
    if date_col:

        st.markdown(f"**Date column detected: ** `{date_col}`")

        # Drop rows where date parsing failed 
        df = df.dropna(subset = [date_col])

        # Get the actual min and max dates from the data
        startDate = df[date_col].min().date()
        endDate = df[date_col].max().date()

        # Display date pickers with the data's date range 
        with col1: 
            date1 = st.date_input('Start Date', startDate, min_value = startDate, max_value = endDate)
        with col2: 
            date2 = st.date_input('End Date', endDate, min_value = startDate, max_value = endDate)
        
        # Filter the dataframe based on the selected date 
        mask = (df[date_col].dt.date >= date1) & (df[date_col].dt.date <= date2)
        filtered_df = df.loc[mask]
    else:
        st.warning("No valid date column detected. Skipping date filtering.")

        # Detecting categorical columns 
    categorical_cols = [col for col in df.columns if df[col].nunique() < 20 and df[col].dtype == 'object']

    # Create sidebar filters
    st.sidebar.header("Filters")

    # Initializing filtered data frame
    # filtered_df = df.copy()

    # Dictionary to store filtered selections
    filtered_selection = {}

    # Creating filters for each categorical columns 
    for col in categorical_cols:
        filtered_selection[col] = st.sidebar.multiselect(
            f"Select {col}",
            options = df[col].unique()
        )
    # Apply filters Sequentially 
    for col, selection in filtered_selection.items():
        if selection: #if any selection was made for this column
            filtered_df = filtered_df[filtered_df[col].isin(selection)]
    # Detecting Numerical Columns 
    
    numeric_columns = filtered_df.select_dtypes(include=['int64', 'float64']).columns

    # Add an empty option at the top of the list
    numeric_column_options = ["-- Select a numeric column --"] + list(numeric_columns)

    # Sidebar: Let user select numeric column (optional)
    st.sidebar.subheader("Select a Numeric Column to Display")
    selected_numeric_col = st.sidebar.selectbox("Choose a numeric column", numeric_column_options)

    # Adding a slider for Scenario Adjustment Gauge 
    st.sidebar.markdown("----") #This is a horizontal line to separate the slider from other filters
    st.sidebar.subheader("Scenario Adjustment Slider")
    adjustment_slider = st.sidebar.slider(
        "Adjustment (%)",
        min_value = 0,
        max_value = 100,
        value = 0,
        step = 1,
        key = "adjustment_slider" #Store value in session state
    )
    if selected_numeric_col != "-- Select a numeric column --":
        adjustment_factor = (100 - st.session_state["adjustment_slider"])/100
        filtered_df["Adjusted_Value"] = filtered_df[selected_numeric_col] * adjustment_factor

    # Check if the user has selected an actual numeric column
    # with st.expander("Filtered Data"):
    if selected_numeric_col != "-- Select a numeric column --":
    # Get only the categorical columns that were filtered + selected numeric column
        active_cat_filters = [col for col, values in filtered_selection.items() if values]
        columns_to_display = active_cat_filters + [selected_numeric_col]

        # Display only those columns
        display_df = filtered_df[columns_to_display]
        # st.write(f"Filtered Data: {selected_numeric_col} and associated categories", display_df)
    # ---- Charts -----

    # # Creating a donut chart
    with col1:

        # Only create chart if a numeric column has been selected
        if selected_numeric_col != "-- Select a numeric column --":
            # Ensure at least one categorical column is present
            if active_cat_filters:
                group_col = active_cat_filters[0]  # Use the first filtered categorical column as category
                chart_data = (
                    filtered_df
                    .groupby(group_col)[selected_numeric_col]
                    .sum()
                    .reset_index()
                )

                # Create the donut chart
                fig = px.pie(
                    chart_data,
                    names=group_col,
                    values=selected_numeric_col,
                    hole=0.4,  # This makes it a donut chart
                    title=f"{selected_numeric_col} Distribution by {group_col}"
                )
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("Please apply at least one categorical filter to generate the chart.")
    with col2:
        if selected_numeric_col != "-- Select a numeric column --":
            # Ensure at least one categorical column is present
            if active_cat_filters:
                group_col = active_cat_filters[0] # Tells the program to use the first categorical filter
                bargraph_data = (
                    filtered_df
                    .groupby(group_col)[selected_numeric_col]
                    .sum()
                    .reset_index()
                )

                # Creating the bar graph
                fig_bar = px.bar(
                    bargraph_data,
                    x = group_col,
                    y = selected_numeric_col,
                    title = f"{selected_numeric_col} by {group_col}",
                    labels = {group_col: group_col, selected_numeric_col: f"Sum of {selected_numeric_col}"},
                    text_auto = True
                )
                st.plotly_chart(fig_bar, use_container_width = True)
            else:
                st.info("")

    with col1:
        if selected_numeric_col != "-- Select a numeric column --":
        
            # if 'Year' in filtered_df.columns:
            if date_col and date_col in filtered_df.columns:
                if filtered_df[date_col].dtype != 'datetime64[ns]':
                    filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors = 'coerce')

                    filtered_df = filtered_df.dropna(subset = [date_col])


                # Aggregating the selected numeric column by year 
                time_series_data = (
                    filtered_df
                    .groupby(date_col)[selected_numeric_col]
                    .sum()
                    .reset_index()
                )

                fig_time = px.line(
                    time_series_data,
                    x = date_col,
                    y = selected_numeric_col,
                    title = f"Time Series Chart for {selected_numeric_col} Over Years"
                )
                st.plotly_chart(fig_time, use_container_width = True)
            else:
                st.warning("The 'Year' column is missing from the filtered data.")
    with col2: 
        if selected_numeric_col != "-- Select a numeric column --":
            if active_cat_filters:
                group_col = active_cat_filters[0]
                treemap_data = (
                    filtered_df
                    .groupby(group_col)[selected_numeric_col]
                    .sum()
                    .reset_index()
                )

                fig_tree = px.treemap(
                    treemap_data,
                    path = [group_col],
                    values = selected_numeric_col,
                    title = f"Treemap of {selected_numeric_col} by {group_col}"
                )
                st.plotly_chart(fig_tree, use_container_width = True)
            else:
                st.write()
    # with col1:
    if selected_numeric_col != "-- Select a numeric column --":
        if len(active_cat_filters) >= 2:
            row_cat = active_cat_filters[0]  #x- axis
            col_cat = active_cat_filters[1] #y-axis

        #Pivot data for form a matrix for the hit map 
            heatmap_data = (
                filtered_df
                .groupby([row_cat, col_cat])[selected_numeric_col]
                .sum()
                .reset_index()
                .pivot(index =col_cat, columns = row_cat, values = selected_numeric_col)
            )

            fig_heat = px.imshow(
                heatmap_data,
                text_auto = True,
                color_continuous_scale = "sunset",
                aspect = "auto",
                title = f"Heatmap of {selected_numeric_col} by {row_cat} and {col_cat}"
            )
            st.plotly_chart(fig_heat, use_container_width = True)
        else:
            st.info("Apply at least two categorical filters to generate heat map")

    if selected_numeric_col != "-- Select a numeric column --" and "Location" in active_cat_filters:
        try: 
            # Group data by country
            map_data = (

                filtered_df
                .groupby("Location")[selected_numeric_col]
                .sum()
                .reset_index()
            )

            fig_map = px.choropleth(
                map_data, 
                locations = "Location",
                locationmode = "country names",
                color = selected_numeric_col,
                color_continuous_scale = "Viridis",
                title = f"{selected_numeric_col} by country",
            )
            st.plotly_chart(fig_map, use_container_width = True)
        except Exception as e:
            st.warning(f"Could not render map {e}")
    else:
            st.info("To display a world map, filter by 'Location' and select a numeric column.")


    # ---- End of Charts -----
with st.expander("Filtered Data"):
    if selected_numeric_col != "-- Select a numeric column --":
    
# Get only the categorical columns that were filtered + selected numeric column
        active_cat_filters = [col for col, values in filtered_selection.items() if values]
        columns_to_display = active_cat_filters + [selected_numeric_col]

    # Display only those columns
        display_df = filtered_df[columns_to_display]
        st.write(f"Filtered Data: {selected_numeric_col} and associated categories", display_df)

with st.expander(f"{selected_numeric_col} targets: "):
    if selected_numeric_col != "-- Select a numeric column --":

        # Only create a pivot table if atleast one categorical filter is active 
        if active_cat_filters:
            pivot_index = active_cat_filters[0] #Use the first selected categorical filter 
            pivot_table = filtered_df.pivot_table(
                index = pivot_index,
                values = "Adjusted_Value",
                aggfunc = "sum"
            ).reset_index()

            st.subheader("Scenario Model Pivot Table")
            st.dataframe(pivot_table, use_container_width = True)
        else:
            st.info("Please select at least one categorical filter to display the pivot table")




# st.write(filtered_df)
        





































