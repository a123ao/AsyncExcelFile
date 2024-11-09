import asyncio
from pathlib import Path
from typing import Optional, Tuple, Any
import pythoncom
import win32com.client as win32

class AsyncExcelFile:
    """
    Asynchronously watches an Excel file and handles read/write operations.
    
    This class provides an async interface to interact with Excel files, supporting
    real-time monitoring of changes and asynchronous read/write operations.
    
    Attributes:
        filename (Path): Path to the Excel file being monitored
        saveOnClose (bool): Whether to save changes when closing the file
        visible (bool): Whether the Excel application should be visible
        update_interval (int): Interval in seconds between file checks
    """
    
    SUPPORTED_EXTENSIONS = (".xlsx", ".xls")

    def __init__(self, filename: str | Path, saveOnClose=True, visible=True, update_interval=1) -> None:
        """
        Initialize the AsyncExcelFile instance.
        
        Args:
            filename: Path to the Excel file
            saveOnClose: Whether to save changes when closing the file
            visible: Whether the Excel application should be visible
            update_interval: Time in seconds between file checks
            
        Raises:
            FileNotFoundError: If the specified file doesn"t exist
            ValueError: If the file is not an Excel file
        """
        self.filename = Path(filename)
        self.saveOnClose = saveOnClose
        self.visible = visible
        self.update_interval = update_interval
        
        if not self.filename.exists():
            raise FileNotFoundError(f"File not found: {self.filename}")
        
        if self.filename.suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {self.filename.suffix}")
        
        self._is_watching: bool = False
        self._excel_app: Optional[Any] = None
        self._workbook: Optional[Any] = None
        self._sheet: Optional[Any] = None
        self._cached_data: Optional[Tuple[Tuple[Any, ...], ...]] = None
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "AsyncExcelFile":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

    @classmethod
    async def open(cls, filename: str | Path, sheet_name: str, saveOnClose=True, visible=True, update_interval=1) -> "AsyncExcelFile":
        """
        Create and initialize an AsyncExcelFile instance.
        
        Args:
            filename: Path to the Excel file
            sheet_name: Name of the sheet to monitor
            saveOnClose: Whether to save changes when closing the file
            visible: Whether the Excel application should be visible
            update_interval: Time in seconds between file checks
            
        Returns:
            An initialized AsyncExcelFile instance
        """
        instance = cls(filename, saveOnClose, visible, update_interval)
        await instance.start_watching(sheet_name)
        return instance

    async def _connect_to_excel(self, sheet_name: str) -> bool:
        """
        Establish connection to Excel application and open the specified sheet.
        
        Args:
            sheet_name: Name of the sheet to open
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._excel_app = win32.Dispatch("Excel.Application")
            self._excel_app.Visible = self.visible
            
            abs_path = str(self.filename.absolute())
            self._workbook = self._excel_app.Workbooks.Open(abs_path)
            self._sheet = self._workbook.Sheets(sheet_name)
            
            return True
        except Exception as exc:
            print(f"Failed to connect to Excel: {exc}")
            return False

    async def _read_sheet_data(self) -> Tuple[Tuple[Any, ...], ...]:
        """
        Read data from the current Excel sheet.
        
        Raises:
            ValueError: If sheet is not initialized
            
        Returns:
            Tuple of tuples containing sheet data
        """
        if not self._sheet:
            raise ValueError("Excel sheet is not initialized")
        
        used_range = self._sheet.UsedRange
        return used_range.Value

    async def start_watching(self, sheet_name: str) -> None:
        """
        Start watching the Excel file for changes.
        
        Args:
            sheet_name: Name of the sheet to monitor
        """
        asyncio.create_task(self._watch_loop(sheet_name))

    async def _watch_loop(self, sheet_name: str) -> None:
        """
        Main watching loop that monitors Excel file for changes.
        
        Args:
            sheet_name: Name of the sheet to monitor
        """
        pythoncom.CoInitialize()
        
        MAX_RETRIES = 5
        retry_count = 0
        self._is_watching = True

        try:
            while self._is_watching:
                if not self._excel_app or not self._workbook:
                    if retry_count >= MAX_RETRIES:
                        raise ConnectionError("Failed to connect to Excel after multiple retries")

                    if not await self._connect_to_excel(sheet_name):
                        retry_count += 1
                        await asyncio.sleep(self.update_interval)
                        continue

                    retry_count = 0

                try:
                    async with self._lock:
                        self._cached_data = await self._read_sheet_data()
                except Exception as exc:
                    print(f"Error reading Excel data: {exc}")

                await asyncio.sleep(self.update_interval)
                
        except Exception as exc:
            print(f"Watch loop error: {exc}")
        finally:
            pythoncom.CoUninitialize()

    async def read_data(self) -> Optional[Tuple[Tuple[Any, ...], ...]]:
        """
        Get the most recently cached data from the Excel file.
        
        Returns:
            Cached data as tuple of tuples, or None if no data available
        """
        return self._cached_data
    
    async def write_cell(self, row: int, column: int, value: Any) -> bool:
        """
        Write a value to a specific cell in the Excel sheet.
        
        Args:
            row: Row index (0-based)
            column: Column index (0-based)
            value: Value to write
            
        Returns:
            True if write successful, False otherwise
            
        Raises:
            ValueError: If sheet is not initialized
        """
        if not self._sheet:
            raise ValueError("Excel sheet is not initialized")
        
        PREFIX = 1

        try:
            async with self._lock:
                self._sheet.Cells(row + PREFIX, column + PREFIX).Value = value
            return True
        except Exception as exc:
            print(f"Failed to write to Excel: {exc}")
            return False
        
    async def write_cells(self, data: Tuple[Tuple[int, int, Any]]) -> bool:
        """
        Write values to multiple cells in the Excel sheet.
        
        Args:
            data: Tuple of tuples containing (row, column, value) data
        """
        if not self._sheet:
            raise ValueError("Excel sheet is not initialized")
        
        PREFIX = 1

        try:
            async with self._lock:
                for row, column, value in data:
                    self._sheet.Cells(row + PREFIX, column + PREFIX).Value = value
            return True
        except Exception as exc:
            print(f"Failed to write to Excel: {exc}")
            return False
        
    async def close(self) -> None:
        """Clean up resources and close Excel connections."""
        self._is_watching = False
        
        try:
            if self._workbook:
                self._workbook.Close(SaveChanges=self.saveOnClose)
            if self._excel_app:
                self._excel_app.Quit()
        except Exception as exc:
            print(f"Error during Excel cleanup: {exc}")
        finally:
            self._sheet = None
            self._workbook = None
            self._excel_app = None
            self._cached_data = None

    async def save(self) -> None:
        """Save changes to the Excel file."""
        if self._workbook:
            self._workbook.Save()