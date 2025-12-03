"""
Unit tests for CSV streaming processor
Tests memory efficiency with large files (100k+ rows)
"""
import unittest
import io
import csv
import tempfile
import os
from csv_processor import (
    process_csv_stream,
    process_excel_stream,
    process_upload_stream,
    validate_required_columns,
    get_missing_columns
)


class TestCSVProcessor(unittest.TestCase):
    
    def test_small_csv_stream(self):
        """Test basic CSV streaming with small file"""
        csv_data = "name,email,age\nJohn,john@example.com,30\nJane,jane@example.com,25\n"
        file_stream = io.BytesIO(csv_data.encode('utf-8'))
        
        chunks = list(process_csv_stream(file_stream, chunk_size=1))
        
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0][0]['name'], 'John')
        self.assertEqual(chunks[1][0]['name'], 'Jane')
    
    def test_csv_chunking(self):
        """Test that CSV is properly chunked"""
        # Create CSV with 5 rows, chunk size of 2
        csv_data = "id,value\n1,a\n2,b\n3,c\n4,d\n5,e\n"
        file_stream = io.BytesIO(csv_data.encode('utf-8'))
        
        chunks = list(process_csv_stream(file_stream, chunk_size=2))
        
        # Should have 3 chunks: [2 rows, 2 rows, 1 row]
        self.assertEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0]), 2)
        self.assertEqual(len(chunks[1]), 2)
        self.assertEqual(len(chunks[2]), 1)
    
    def test_csv_column_normalization(self):
        """Test that column names are normalized to lowercase"""
        csv_data = "Name,EMAIL,Age\nJohn,john@example.com,30\n"
        file_stream = io.BytesIO(csv_data.encode('utf-8'))
        
        chunks = list(process_csv_stream(file_stream))
        row = chunks[0][0]
        
        self.assertIn('name', row)
        self.assertIn('email', row)
        self.assertIn('age', row)
        self.assertNotIn('Name', row)
        self.assertNotIn('EMAIL', row)
    
    def test_large_csv_memory_efficiency(self):
        """Test memory efficiency with 100k row CSV"""
        # Create a temporary large CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'email', 'value'])
            
            # Write 100,000 rows
            for i in range(100000):
                writer.writerow([i, f'User{i}', f'user{i}@example.com', f'value{i}'])
            
            temp_file = f.name
        
        try:
            # Process the file in chunks
            with open(temp_file, 'rb') as f:
                total_rows = 0
                chunk_count = 0
                
                for chunk in process_csv_stream(f, chunk_size=1000):
                    chunk_count += 1
                    total_rows += len(chunk)
                    
                    # Verify chunk structure
                    self.assertLessEqual(len(chunk), 1000)
                    self.assertIn('id', chunk[0])
                    self.assertIn('name', chunk[0])
                
                # Verify all rows were processed
                self.assertEqual(total_rows, 100000)
                self.assertEqual(chunk_count, 100)  # 100k rows / 1k chunk size
        
        finally:
            # Clean up temp file
            os.unlink(temp_file)
    
    def test_validate_required_columns(self):
        """Test column validation"""
        row = {'name': 'John', 'email': 'john@example.com', 'age': '30'}
        
        # Test with all required columns present
        self.assertTrue(validate_required_columns(row, {'name', 'email'}))
        
        # Test with missing required column
        self.assertFalse(validate_required_columns(row, {'name', 'phone'}))
    
    def test_get_missing_columns(self):
        """Test missing column detection"""
        available = {'name', 'email', 'age'}
        required = {'name', 'email', 'phone', 'address'}
        
        missing = get_missing_columns(available, required)
        
        self.assertEqual(missing, {'phone', 'address'})
    
    def test_empty_csv(self):
        """Test handling of empty CSV"""
        csv_data = "name,email\n"  # Headers only, no data
        file_stream = io.BytesIO(csv_data.encode('utf-8'))
        
        chunks = list(process_csv_stream(file_stream))
        
        self.assertEqual(len(chunks), 0)
    
    def test_csv_with_special_characters(self):
        """Test CSV with special characters and quotes"""
        csv_data = 'name,description\n"John, Jr.","He said ""Hello"""\n'
        file_stream = io.BytesIO(csv_data.encode('utf-8'))
        
        chunks = list(process_csv_stream(file_stream))
        row = chunks[0][0]
        
        self.assertEqual(row['name'], 'John, Jr.')
        self.assertEqual(row['description'], 'He said "Hello"')


class TestExcelProcessor(unittest.TestCase):
    
    def test_excel_basic(self):
        """Test basic Excel processing"""
        # Note: This test requires openpyxl and a test Excel file
        # For now, we'll create a simple test
        try:
            from openpyxl import Workbook
            
            # Create a temporary Excel file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as f:
                temp_file = f.name
            
            wb = Workbook()
            ws = wb.active
            ws.append(['Name', 'Email', 'Age'])
            ws.append(['John', 'john@example.com', 30])
            ws.append(['Jane', 'jane@example.com', 25])
            wb.save(temp_file)
            wb.close()
            
            try:
                with open(temp_file, 'rb') as f:
                    chunks = list(process_excel_stream(f, chunk_size=1))
                
                self.assertEqual(len(chunks), 2)
                self.assertEqual(chunks[0][0]['name'], 'John')
                self.assertEqual(chunks[1][0]['name'], 'Jane')
            
            finally:
                os.unlink(temp_file)
        
        except ImportError:
            self.skipTest("openpyxl not installed")


class TestFileUploadProcessor(unittest.TestCase):
    
    def test_unsupported_file_type(self):
        """Test that unsupported file types raise ValueError"""
        class MockUpload:
            filename = 'test.txt'
            stream = io.BytesIO(b'test data')
        
        upload = MockUpload()
        
        with self.assertRaises(ValueError) as context:
            list(process_upload_stream(upload))
        
        self.assertIn('Unsupported file type', str(context.exception))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
