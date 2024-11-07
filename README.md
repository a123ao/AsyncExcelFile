# AsyncExcelFile

`AsyncExcelFile` is a Python class designed to enable asynchronous read and write operations on Excel files in real-time. It provides an easy-to-use async interface for handling Excel files, allowing users to monitor changes and perform operations on specific sheets without blocking other tasks in an application.

## Features

- **Asynchronous Excel Monitoring**: The class uses an asynchronous loop to monitor Excel files for updates without blocking the main application.
- **Read/Write Capabilities**: You can read data and write values to specific cells within an Excel sheet.
- **Auto-save Option**: Changes can be saved automatically when the Excel file is closed.
- **Configurable Update Interval**: Set a custom interval for how often the file should be checked for updates.
- **Context Manager Support**: The class can be used with `async with` statements, ensuring proper resource cleanup when the file is no longer needed.

## Requirements

- **Python 3.8+**
- **Packages**:
  - `pywin32` for interacting with the Excel COM object.
  - `pythoncom` for COM initialization within async loops.

Install `pywin32` if it's not already installed:
```bash
pip install pywin32
```

## Getting Started
1. **Setup**: Import the AsyncExcelFile class into your Python script.
2. **File Monitoring**: Use the open method to create an instance of AsyncExcelFile, specifying the Excel file path, the sheet name, and other optional parameters.
3. **Reading and Writing**:
  - Use read_data() to fetch the latest data from the sheet.
  - Use write_cell(row, column, value) to write a value to a specific cell.
4. **Save Changes**: Call the save method to save any changes made to the Excel file.
5. **Close the File**: Use the close method to release resources and close the Excel file.

## Example Usage
```python
import asyncio
from pathlib import Path
from asyncExcelFile import AsyncExcelFile  # Adjust this to your file structure

async def main() -> None:
    excel_file = Path("test.xlsx")
    sheet_name = "Sheet1"  # Change to your target sheet

    # Open the Excel file asynchronously
    async with await AsyncExcelFile.open(excel_file, sheet_name) as excel:
        try:
            # Loop to continuously monitor and print the top 5 rows
            while True:
                data = await excel.read_data()
                if data:
                    print(data[:5])  # Print first 5 rows for brevity
                await asyncio.sleep(1)  # Adjust sleep as needed
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    asyncio.run(main())
```