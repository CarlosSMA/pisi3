import os

def read_csv_data():
    files = os.listdir('./data')
    csv_files = []

    for file in files:
        if file.endswith('.csv'):
            csv_files.append(file)

    print(csv_files)

def main():
    read_csv_data()

if __name__ == "__main__":
    main()