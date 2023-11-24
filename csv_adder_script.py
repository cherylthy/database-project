import pandas as pd

# Load the CSV file
file_path = '2023 Car Dataset final.csv'
df = pd.read_csv(file_path)

# Clean and strip column names
df.columns = df.columns.str.strip()

# Create the 'Image Path' column
df['image_path'] = df['car_make'].str.lower() + ".jpg"

# Save the updated DataFrame to the original CSV file
df.to_csv(file_path, index=False)
