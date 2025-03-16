import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri

# Activate automatic conversion from R to pandas
pandas2ri.activate()

# Load the R library
senatebR = importr('senatebR')

# Define the codigos variable in Python
codigos = [12345, 12071, 12072, 12073]

# Convert the Python list to an R vector
codigos_r = robjects.IntVector(codigos)

# Call the R function with the variable
debates = senatebR.extrair_notas_taquigraficas(codigos_r)

# Convert the R object to a pandas DataFrame
debates_df = pandas2ri.rpy2py(debates)

# Print the DataFrame
print(debates_df)
#Guardar os textos (brutos) em um vetor de debates em .csv
import pandas as pd
import os

# Specify the folder (relative path)
folder_path = 'sessoes'

# Create the folder if it doesn't exist
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Iterate through each row in the DataFrame and save it to a separate file
for index, row in debates_df.iterrows():
    # Create a unique filename for each debate
    file_name = f"debate_{index}.txt"  # Convert index + 1 to a string
    file_path = os.path.join(folder_path, file_name)
    row_df = pd.DataFrame([row])

    # Save the row to a CSV file
    row_df.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
    # Save the row (debate) to a text file
    #with open(file_path, 'w', encoding='utf-8') as file:
    #    file.write(row.to_string())  # Convert the row to a string and write to file

#Caso nao precise fazer um arquivo para cada debate
#file_path = os.path.join(folder_path, 'debates.txt')

# Save the DataFrame to the specified folder
#debates_df.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
