import pandas as pd

# Processor data banate hain
data = [f"Processor {i}(RAW)" for i in range(1, 129)]

# Data ko DataFrame mein convert karte hain
df = pd.DataFrame(data, columns=['Processor'])

# CSV file mein save karte hain
df.to_csv('processors.csv', index=False)

print("Data successfully saved to processors.csv!")
