import sys
import time

def main():
    # Simulate a loop with 10 steps
    for i in range(1, 11):
        time.sleep(0.5)  # Simulate work
        percent = i * 10
        # Print to stdout and flush immediately so PyQt can read it
        print(f"PROGRESS:{percent}")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
