
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri

# Activate pandas conversion
pandas2ri.activate()

# Load the senatebR package
robjects.r('suppressWarnings(library(senatebR))')

# Fetch the senate debates data
debates = robjects.r('obter_dados_partidos()')

# Convert the R data frame to a pandas DataFrame
debates_df = pandas2ri.rpy2py(debates)

# Display the first few rows of the DataFrame
print(debates_df.head())
