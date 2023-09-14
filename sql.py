import sqlite3

# Set up a connection to the database file
conn = sqlite3.connect('database.db')

# Create a cursor object to execute queries
c = conn.cursor()

# Loop to accept user input and execute queries
while True:
    # Get input from the user
    command = input("Enter a SQL command (or 'quit' to exit): ")

    # Check if the user wants to quit
    if command.lower() == 'quit':
        break

    # Execute the user's command
    try:
        c.execute(command)

        # If the command is a SELECT statement, print the results
        if command.upper().startswith('SELECT'):
            results = c.fetchall()
            for row in results:
                print(row)
    except Exception as e:
        print(f"Error: {e}")

# Close the connection when finished
conn.close()
