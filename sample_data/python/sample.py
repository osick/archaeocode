"""Sample Python module"""
import json
import sys

class DataProcessor:
    """Process data"""

    def __init__(self):
        self.data = []

    def process(self, item):
        """Process an item"""
        if item:
            self.data.append(item)
        return True

def main():
    """Main function"""
    processor = DataProcessor()
    processor.process("test")
    print("Done")

if __name__ == "__main__":
    main()
