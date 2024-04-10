import subprocess

# Define the path to the file containing commands
input_file = 'transactions1.txt'

# Open the file and execute each command
with open(input_file, 'r') as file:
    # Initialize line counter
    line_number = 0

    for line in file:
        # Increment line number for each line read
        line_number += 1

        # Print the line number and the command before executing
        print(f"Executing line {line_number}: {line.strip()}")

        try:
            # Execute the command using subprocess
            subprocess.run(line.strip(), shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing line {line_number}: {e}")
