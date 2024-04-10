import subprocess

# Define the path to the file containing commands
input_file = 'strt.txt'

# Open the file and execute each command
with open(input_file, 'r') as file:
    for line in file:
        # Execute the command using subprocess
        subprocess.run(line.strip(), shell=True)