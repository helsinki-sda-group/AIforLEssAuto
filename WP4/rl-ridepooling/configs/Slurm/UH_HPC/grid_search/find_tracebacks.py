import sys
import glob

def main():
    pattern = f"output/*"
    files = glob.glob(pattern)
    traceback_files = []
    for filename in files:
        with open(filename, 'r') as file:
            found_traceback = False
            for line in file:
                if found_traceback:
                    print(line, end='')
                elif line.startswith("Traceback"):
                    traceback_files.append(filename)
                    print(filename)
                    print(line, end='')
                    found_traceback = True
            
            if found_traceback:
                while True:
                    user_input = input("Type 'n' for next file or 'q' to quit: ").lower()
                    if user_input == 'n':
                        break
                    elif user_input == 'q':
                        print("Exiting...")
                        sys.exit(0)
                    else:
                        print("Invalid input. Type 'n' for next or 'q' to quit.")

    print(traceback_files)

if __name__ == '__main__':
    main()

