import asyncio
from pathlib import Path
from asyncExcelFile import AsyncExcelFile

async def main() -> None:
    """Main execution function demonstrating usage of AsyncExcelFile."""
    excel_file = Path("test.xlsx")
    sheet_name = "工作表1"
    
    async with await AsyncExcelFile.open(excel_file, sheet_name) as excel:
        try:
            while True:
                data = await excel.read_data()
                if data:
                    print(data[:5])
                
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    asyncio.run(main())
