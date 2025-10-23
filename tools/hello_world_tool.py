import os

def main():
    # choose where to write the file
    path = os.path.join(os.getcwd(), "demo")
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "hello.txt")
    with open(file_path, "w") as f:
        f.write("hello from the agent 👋\n")

    print(f"Created {file_path}")

if __name__ == "__main__":
    main()