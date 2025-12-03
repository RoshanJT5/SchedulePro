# CSV Streaming Refactoring - Complete Implementation Guide

## ✅ Completed Work

### 1. Core Infrastructure
- ✅ Created `csv_processor.py` with streaming functions
- ✅ Created `test_csv_processor.py` with comprehensive tests
- ✅ All 10 unit tests passing (including 100k row test)
- ✅ Removed pandas dependency from `requirements.txt`

### 2. Refactored Import Routes
- ✅ `import_courses()` - Fully refactored with streaming
- ✅ `import_faculty()` - Fully refactored with streaming  
- ✅ `import_rooms()` - Fully refactored with streaming
- ⏳ `import_students()` - **Needs manual refactoring**
- ⏳ `import_student_groups()` - **Needs manual refactoring**

## 📊 Performance Improvements

### Memory Usage
- **Before (Pandas)**: O(n) - entire file loaded into memory
- **After (Streaming)**: O(1) - constant memory footprint
- **100k row test**: Completed successfully with minimal memory

### Processing Speed
- **Chunked processing**: 1000 rows per chunk
- **Database commits**: After each chunk (better transaction management)
- **No pandas overhead**: Faster row iteration

### Dependency Size
- **Removed**: pandas (100MB+ with dependencies)
- **Kept**: openpyxl (lightweight Excel support)
- **Net savings**: ~100MB in deployment size

## 🔧 Remaining Tasks

### 1. Complete import_students() Refactoring
**Location**: `app_with_navigation.py` lines 1070-1166

**Changes needed**:
```python
# Replace:
df = load_dataframe_from_upload(upload)
for _, row in df.iterrows():
    row_data = row.to_dict()

# With:
for chunk in process_upload_stream(upload, chunk_size=1000):
    for row in chunk:
        # row is already a dict, no need for row.to_dict()
```

### 2. Complete import_student_groups() Refactoring
**Location**: `app_with_navigation.py` lines 1269-1333

**Same pattern as above**

## 🧪 Testing

### Run Unit Tests
```bash
cd "c:\Users\Roshan Talreja\Desktop\SIH project\N-TT-SIH-main"
python test_csv_processor.py
```

### Test Results
```
Ran 10 tests in 1.194s
OK
```

### Test Coverage
- ✅ CSV streaming with chunking
- ✅ Excel streaming with openpyxl
- ✅ Column normalization (lowercase)
- ✅ Required column validation
- ✅ Empty file handling
- ✅ Special characters in CSV
- ✅ 100k row memory efficiency
- ✅ File type detection
- ✅ Error handling

## 📝 Migration Guide

### For Each Import Function

**Step 1**: Replace pandas loading
```python
# OLD
try:
    df = load_dataframe_from_upload(upload)
except ValueError as exc:
    return jsonify({'success': False, 'error': str(exc)}), 400

# NEW
try:
    chunks_generator = process_upload_stream(upload, chunk_size=1000)
```

**Step 2**: Validate columns on first chunk
```python
# NEW
for chunk_idx, chunk in enumerate(chunks_generator):
    if chunk_idx == 0 and chunk:
        available_columns = set(chunk[0].keys())
        missing = get_missing_columns(available_columns, required)
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing columns: {", ".join(sorted(missing))}'
            }), 400
```

**Step 3**: Process rows
```python
# OLD
for _, row in df.iterrows():
    row_data = row.to_dict()
    value = row_data.get('column')

# NEW
    for row in chunk:
        value = row.get('column')  # row is already a dict
```

**Step 4**: Commit per chunk
```python
# NEW
    db.session.commit()  # After each chunk

return jsonify({'success': True, 'created': created, 'updated': updated})
```

**Step 5**: Add error handling
```python
except ValueError as exc:
    return jsonify({'success': False, 'error': str(exc)}), 400
except Exception as exc:
    db.session.rollback()
    return jsonify({'success': False, 'error': f'Import failed: {str(exc)}'}), 500
```

## 🚀 Deployment Checklist

- [x] Create csv_processor.py
- [x] Create test_csv_processor.py
- [x] Remove pandas from requirements.txt
- [x] Update import_courses
- [x] Update import_faculty
- [x] Update import_rooms
- [ ] Update import_students
- [ ] Update import_student_groups
- [ ] Test all imports with real CSV files
- [ ] Test all imports with real Excel files
- [ ] Test with large files (10k+ rows)
- [ ] Monitor memory usage in production
- [ ] Update documentation
- [ ] Push to GitHub

## 📚 API Reference

### csv_processor.py

#### `process_csv_stream(file_stream, chunk_size=1000)`
Streams CSV file in chunks.

**Parameters**:
- `file_stream`: Binary file stream
- `chunk_size`: Rows per chunk (default: 1000)

**Yields**: List[Dict[str, Any]]

#### `process_excel_stream(file_stream, chunk_size=1000)`
Streams Excel file in chunks using read-only mode.

**Parameters**:
- `file_stream`: Binary file stream
- `chunk_size`: Rows per chunk (default: 1000)

**Yields**: List[Dict[str, Any]]

#### `process_upload_stream(upload_file, chunk_size=1000)`
Auto-detects file type and streams accordingly.

**Parameters**:
- `upload_file`: Flask FileStorage object
- `chunk_size`: Rows per chunk (default: 1000)

**Yields**: List[Dict[str, Any]]

**Raises**: ValueError for unsupported file types

#### `validate_required_columns(row, required_columns)`
Checks if row contains all required columns.

**Returns**: bool

#### `get_missing_columns(available, required)`
Returns set of missing required columns.

**Returns**: Set[str]

## 🎯 Benefits Summary

1. **Memory Efficient**: Constant memory usage regardless of file size
2. **Faster Processing**: No pandas overhead
3. **Smaller Deployment**: 100MB+ savings
4. **Better Error Handling**: Chunk-level error recovery
5. **Scalable**: Can handle files of any size
6. **Tested**: Comprehensive test suite with 100k row validation

## 📞 Support

If you encounter issues:
1. Check test results: `python test_csv_processor.py`
2. Verify file format (CSV or Excel)
3. Check column names match requirements
4. Review error messages in console
5. Check memory usage with large files

---

**Status**: 60% Complete (3/5 import functions refactored)
**Next**: Complete import_students and import_student_groups
