import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO


#Removing leading and trailing spaces of columns
def columns_cleaning(df):
    x = df.columns
    df.columns = [i.strip() for i in x]  
    return df




#finding null values
def finding_null_values(df):
    # Find rows with at least one null value
    null_rows = df[df.isnull().any(axis=1)]
    
    # Only keep columns that contain null values in the null rows
    null_rows_with_null_columns = null_rows.loc[:, null_rows.isnull().any()]
    
    return null_rows_with_null_columns

#Figuring out the structure of data and make it accurate
def determine_type(value):
    value = value.strip()  
    try:
        datetime.strptime(value, "%Y-%m-%d")  # Format: YYYY-MM-DD
        return "Datetime"
    except ValueError:
        pass
    try:
        float(value)
        return "Float"
    except ValueError:
        pass
    
    if value.isdigit():
        return "Number"

    return "Object."




def figure_out(df):
    df=df.astype(str)
    for i in df.columns:
        for j in df[i]:
            if determine_type(j)=="Number":
                df[i]=df[i].astype(int)
            elif determine_type(j)=="Datetime":
                df[i]=pd.to_datetime(df[i], errors='coerce')
            elif determine_type(i)=="Float":
                df[i]=df[i].astype(float)
            else:
                df[i]=df[i].astype(object)
    return df



def show_duplicate_rows(df):
    duplicates = df[df.duplicated(keep=False)]
    return duplicates

# Function to show duplicate columns
def show_duplicate_columns(df):
    duplicates = df.loc[:, df.T.duplicated(keep=False)]
    return duplicates


def remove_duplicate_columns(df):
    duplicates = df.T.duplicated()
    df = df.loc[:, ~duplicates]
    return df


def clean_and_validate_phone_number(phone):
    if pd.isna(phone): 
        return 'No Contact'

    newphone = ''
    for i in str(phone):
        if i.isdigit():
            newphone=newphone+i
    if len(newphone) == 10:
        return newphone 
    else:
        return 'No Contact'  


def trimming_unnecessary_spaces(dataset,column):
    for i in range(len(dataset)):
                   dataset[column][i]=dataset[column][i].strip()

#filling the null values
def filling_the_null_values(df):
    for column in df.columns:
        if df[column].dtype == 'object':  # For object columns
            df[column].fillna('No information', inplace=True)
        elif df[column].dtype=='int' or df[column].dtype=='float':
            df[column] = pd.to_numeric(df[column], errors='coerce')
            
            # Compute rolling mean and fill null values
            rolling_mean = df[column].rolling(window=10, min_periods=1).mean()
            df[column] = df[column].fillna(rolling_mean)


    return df

# Function to convert dataframe to an Excel file in memory
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()

# Function to convert dataframe to PDF in memory
def to_pdf(df):
    output = BytesIO()
    pdf = PdfPages(output)

    # Create a figure for the PDF
    fig, ax = plt.subplots(figsize=(8.5, 11))  # A4 size
    ax.axis('tight')
    ax.axis('off')
    
    # Convert dataframe to a string format and plot it on the figure
    table_data = df.to_string(index=False)
    ax.text(0.1, 0.9, table_data, ha='left', va='top', fontsize=10)

    # Add the page to the PDF
    pdf.savefig(fig, bbox_inches='tight')
    pdf.close()

    return output.getvalue()


#Preparing the UI
st.title("CSV File Cleaning Application")
st.write("Upload a CSV file to clean and process it.")

uploaded_file = st.file_uploader("Choose a CSV file or excel file ", type=["csv","xlsx"])

if uploaded_file is not None:
    # Load the data
    try:
        if uploaded_file.name.endswith('.csv'):
            # Process CSV file
            st.write("### Processing as CSV File")
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            # Process Excel file
            st.write("### Processing as Excel File")
            df = pd.read_excel(uploaded_file,engine='openpyxl')

        
        st.write("### Original Data Preview")
        st.dataframe(df.head())

        # Clean columns
        st.write("### Clean Column Names")
        data = columns_cleaning(df)        
        st.success("Column names cleaned!")

        # Check for duplicate rows
        st.write("### Check for Duplicate Rows")
        duplicates=show_duplicate_rows(df)
        if not duplicates.empty:
            st.dataframe(duplicates)
            df=df.drop_duplicates()
            st.success("Duplicate Rows removed")
        else:
            st.success("No Duplicate Rows found")

        # Display cleaned data
        duplicates = show_duplicate_columns(df)
        
        if not duplicates.empty:
            st.write("### Removal of Duplicate Columns")
            # Display duplicate columns
            st.write("Duplicate Columns Found:")
            st.dataframe(duplicates)
            df=remove_duplicate_columns(df)
            st.write(f"Columns affected: {len(duplicates.columns)-1} \n Rows affected: {len(duplicates)}")
            st.success(f"Duplicates Successfully removed.")
        

        # Check for null values
        st.write("### Find Rows with Null Values")
        null_values = finding_null_values(df)
        if  not null_values.empty:
            st.success("Rows with null values:")
            st.dataframe(null_values)
            
        else:
            st.success("No Null values found")

        # Change data types of columns
        st.write("### Change the datatype of the column")
        x=figure_out(df)
        st.success("Successfully changed the datatype")


        # # Clean phone numbers (if a phone column exists)
        try:
            numbers_list=df['Phone Number']
            x = []
            for i in numbers_list:
                x.append(clean_and_validate_phone_number(str(i)))
            
            # Update the column with the validated phone numbers
            df["Phone Number"] = x
            st.write("### Validate Phone Numbers")
            st.write('Here is the editted version of Phone Number Column')
            st.dataframe(df["Phone Number"])
            st.write(f"Columns affected=1  ;  Rows affected= {len(df)}")
            st.success("Phone Number Validated")
        except:
            pass

        # Remove unnecessary spaces
        st.write("### Trim Spaces from a Column")
        for i in df.select_dtypes(include=['object']).columns:
            df[i] = df[i].str.strip()

        st.success("Trimming spaces done")
        
        st.write("### Remove all the empty row and column")
        row_affected = df.dropna(how='all', axis=0)
        column_affected = df.dropna(how='all', axis=1)
        df=column_affected
        st.write(f"Rows affected:{len(row_affected)}  ;  Columns affected: 1")
        st.success("Successfully cleaned unnecessary rows and columns")


        st.write("### Cleaned Data Preview")
        filling_the_null_values(df)
        st.dataframe(df)


        # Provide download option
        st.write("### Download Cleaned CSV with null values filled.")
        csv_file=df.to_csv(index=False)
        st.download_button(
        label="Download data as CSV",
        data=csv_file,
        file_name="cleaned_dataset.csv",
        mime="text/csv"
)
        # Convert the dataframe to Excel and PDF format
        xlsx_data = to_excel(df)
        pdf_data = to_pdf(df)

        # Streamlit download buttons
        st.download_button(
            label="Download data as Excel",
            data=xlsx_data,
            file_name="cleaned_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="Download data as PDF",
            data=pdf_data,
            file_name="cleaned_dataset.pdf",
            mime="application/pdf"
        )

        

    except Exception as e:
        st.error(f"Error loading the file: {e}")

