'use client';
import { useRef, useState, useEffect, useMemo, useCallback, forwardRef, useImperativeHandle } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

/**
 * SpreadsheetEditorAG — Production-grade AG Grid spreadsheet
 * 
 * Features:
 * ✅ Dynamic columns (NO hardcoding)
 * ✅ Edit any cell
 * ✅ Add/delete rows
 * ✅ Add/delete columns  
 * ✅ Rename columns
 * ✅ Resize columns
 * ✅ Copy/paste
 * ✅ Undo/redo
 * ✅ Keyboard navigation
 * ✅ Column sorting
 * ✅ Confidence-based cell coloring
 * ✅ Client-side Excel export (SheetJS)
 * ✅ Fullscreen mode
 */

const SpreadsheetEditorAG = forwardRef(({ rows = [], onUpdate, readOnly = false }, ref) => {
  const gridRef = useRef(null);
  const [mounted, setMounted] = useState(false);
  const [columnDefs, setColumnDefs] = useState([]);
  const [rowData, setRowData] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Build dynamic column definitions from row data
  useEffect(() => {
    if (!rows || rows.length === 0) {
      setColumnDefs([]);
      setRowData([]);
      return;
    }

    // Collect all unique keys from all rows (excluding internal fields)
    const internalKeys = new Set(['confidence', 'row_number', '_balance', '_count', '_id']);
    const allKeys = new Set();
    const keyOrder = [];
    
    rows.forEach(row => {
      Object.keys(row).forEach(key => {
        if (!internalKeys.has(key) && !allKeys.has(key)) {
          allKeys.add(key);
          keyOrder.push(key);
        }
      });
    });

    // Preferred column order (if keys exist)
    const preferredOrder = ['date', 'description', 'amount', 'type', 'category', 'gst', 'reference'];
    const orderedKeys = [];
    
    preferredOrder.forEach(key => {
      if (allKeys.has(key)) {
        orderedKeys.push(key);
        allKeys.delete(key);
      }
    });
    
    // Append remaining columns
    keyOrder.forEach(key => {
      if (allKeys.has(key)) {
        orderedKeys.push(key);
      }
    });

    // Build AG Grid column definitions
    const colDefs = orderedKeys.map(key => {
      const headerName = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
      
      const def = {
        field: key,
        headerName,
        editable: !readOnly,
        sortable: true,
        filter: true,
        resizable: true,
        headerComponentParams: {
          enableRename: true,
        },
      };

      // Column-specific configs
      if (key === 'amount' || key === 'gst') {
        def.type = 'numericColumn';
        def.valueFormatter = params => {
          const val = parseFloat(params.value);
          return isNaN(val) ? '0.00' : val.toFixed(2);
        };
        def.width = 120;
      } else if (key === 'date') {
        def.width = 120;
      } else if (key === 'description') {
        def.width = 280;
        def.wrapText = true;
        def.autoHeight = false;
      } else if (key === 'type') {
        def.cellEditor = 'agSelectCellEditor';
        def.cellEditorParams = {
          values: ['debit', 'credit', 'expense', 'income', 'other'],
        };
        def.width = 100;
      } else if (key === 'category') {
        def.cellEditor = 'agSelectCellEditor';
        def.cellEditorParams = {
          values: ['food', 'transport', 'utilities', 'salary', 'rent', 'transfer', 'shopping', 'healthcare', 'education', 'entertainment', 'other'],
        };
        def.width = 130;
      } else {
        def.width = 150;
      }

      // Cell styling based on confidence
      def.cellStyle = params => {
        const confidence = params.data?.confidence ?? 1;
        if (confidence < 0.3) {
          return { 
            backgroundColor: '#fef2f2',
            borderLeft: '3px solid #ef4444',
          };
        } else if (confidence < 0.6) {
          return {
            backgroundColor: '#fffbeb',
            borderLeft: '3px solid #f59e0b',
          };
        }
        return null;
      };

      return def;
    });

    // Add row number column at start
    colDefs.unshift({
      field: '_rowNum',
      headerName: '#',
      width: 60,
      editable: false,
      pinned: 'left',
      valueGetter: params => params.node.rowIndex + 1,
      cellStyle: { backgroundColor: '#f8fafc', fontWeight: 600, color: '#64748b' },
    });

    setColumnDefs(colDefs);

    // Transform row data
    const transformedRows = rows.map((row, idx) => ({
      ...row,
      _rowNum: idx + 1,
      _rowId: row._id || `row_${idx}_${Date.now()}`,
    }));

    setRowData(transformedRows);
  }, [rows, readOnly]);

  // Handle cell value changes
  const onCellValueChanged = useCallback((event) => {
    if (!onUpdate) return;
    
    const api = event.api;
    const updatedRows = [];
    
    api.forEachNode(node => {
      if (node.data) {
        // Remove internal fields
        const { _rowNum, _rowId, ...cleanRow } = node.data;
        updatedRows.push(cleanRow);
      }
    });
    
    onUpdate(updatedRows);
  }, [onUpdate]);

  // Add row
  const addRow = useCallback(() => {
    const api = gridRef.current?.api;
    if (!api) return;

    // Get all column fields (except internal ones)
    const allCols = api.getColumns()?.map(col => col.getColId()).filter(id => !id.startsWith('_')) || [];
    
    const newRow = {};
    allCols.forEach(col => {
      if (col === 'amount' || col === 'gst') {
        newRow[col] = 0;
      } else if (col === 'type') {
        newRow[col] = 'debit';
      } else if (col === 'confidence') {
        newRow[col] = 1.0;
      } else {
        newRow[col] = '';
      }
    });

    newRow._rowId = `new_${Date.now()}`;
    newRow.confidence = 1.0;

    api.applyTransaction({ add: [newRow] });
    
    if (onUpdate) {
      const updatedRows = [];
      api.forEachNode(node => {
        if (node.data) {
          const { _rowNum, _rowId, ...cleanRow } = node.data;
          updatedRows.push(cleanRow);
        }
      });
      onUpdate(updatedRows);
    }
  }, [onUpdate]);

  // Delete selected rows
  const deleteSelectedRows = useCallback(() => {
    const api = gridRef.current?.api;
    if (!api) return;

    const selectedRows = api.getSelectedRows();
    if (selectedRows.length === 0) return;

    api.applyTransaction({ remove: selectedRows });

    if (onUpdate) {
      const updatedRows = [];
      api.forEachNode(node => {
        if (node.data) {
          const { _rowNum, _rowId, ...cleanRow } = node.data;
          updatedRows.push(cleanRow);
        }
      });
      onUpdate(updatedRows);
    }
  }, [onUpdate]);

  // Add column
  const addColumn = useCallback(() => {
    const api = gridRef.current?.api;
    if (!api) return;

    const existingCols = api.getColumns()?.filter(col => !col.getColId().startsWith('_')).length || 0;
    const newColName = `Column ${existingCols + 1}`;

    const newColDef = {
      field: newColName,
      headerName: newColName,
      editable: !readOnly,
      sortable: true,
      filter: true,
      resizable: true,
      width: 150,
    };

    const currentCols = columnDefs.filter(col => col.field !== '_rowNum');
    setColumnDefs([columnDefs[0], ...currentCols, newColDef]);

    // Update all rows to include new column
    const updatedRows = rowData.map(row => ({ ...row, [newColName]: '' }));
    setRowData(updatedRows);

    if (onUpdate) {
      const cleanRows = updatedRows.map(({ _rowNum, _rowId, ...rest }) => rest);
      onUpdate(cleanRows);
    }
  }, [columnDefs, rowData, readOnly, onUpdate]);

  // Delete column
  const deleteColumn = useCallback((field) => {
    if (!field || field === '_rowNum') return;

    const newColDefs = columnDefs.filter(col => col.field !== field);
    setColumnDefs(newColDefs);

    const updatedRows = rowData.map(row => {
      const { [field]: removed, ...rest } = row;
      return rest;
    });
    setRowData(updatedRows);

    if (onUpdate) {
      const cleanRows = updatedRows.map(({ _rowNum, _rowId, ...rest }) => rest);
      onUpdate(cleanRows);
    }
  }, [columnDefs, rowData, onUpdate]);

  // Rename column
  const renameColumn = useCallback((oldField, newField) => {
    if (!oldField || !newField || oldField === '_rowNum' || oldField === newField) return;

    const newColDefs = columnDefs.map(col => {
      if (col.field === oldField) {
        return { ...col, field: newField, headerName: newField };
      }
      return col;
    });
    setColumnDefs(newColDefs);

    const updatedRows = rowData.map(row => {
      const { [oldField]: value, ...rest } = row;
      return { ...rest, [newField]: value };
    });
    setRowData(updatedRows);

    if (onUpdate) {
      const cleanRows = updatedRows.map(({ _rowNum, _rowId, ...rest }) => rest);
      onUpdate(cleanRows);
    }
  }, [columnDefs, rowData, onUpdate]);

  // Export to Excel (client-side with SheetJS)
  const exportExcel = useCallback(async (filename) => {
    try {
      const XLSX = (await import('xlsx')).default || (await import('xlsx'));
      const api = gridRef.current?.api;
      if (!api) return false;

      // Get all columns (except internal)
      const allCols = api.getColumns()?.filter(col => !col.getColId().startsWith('_')) || [];
      const headers = allCols.map(col => col.getColDef().headerName || col.getColId());

      // Get all row data
      const data = [];
      api.forEachNode(node => {
        if (node.data) {
          const row = allCols.map(col => {
            const value = node.data[col.getColId()];
            return value ?? '';
          });
          data.push(row);
        }
      });

      // Create worksheet
      const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);

      // Auto-size columns
      const colWidths = headers.map((h, i) => {
        let maxLen = h.length;
        data.forEach(row => {
          const cellLen = String(row[i] ?? '').length;
          if (cellLen > maxLen) maxLen = cellLen;
        });
        return { wch: Math.min(Math.max(maxLen + 2, 10), 50) };
      });
      ws['!cols'] = colWidths;

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Extracted Data');
      XLSX.writeFile(wb, filename || `docxl_export_${Date.now()}.xlsx`);
      return true;
    } catch (err) {
      console.error('Excel export error:', err);
      return false;
    }
  }, []);

  // Export to JSON
  const exportJSON = useCallback(() => {
    const api = gridRef.current?.api;
    if (!api) return;

    const allCols = api.getColumns()?.filter(col => !col.getColId().startsWith('_')) || [];
    const headers = allCols.map(col => col.getColDef().headerName || col.getColId());

    const jsonData = [];
    api.forEachNode(node => {
      if (node.data) {
        const obj = {};
        allCols.forEach((col, i) => {
          obj[headers[i]] = node.data[col.getColId()];
        });
        jsonData.push(obj);
      }
    });

    const blob = new Blob([JSON.stringify({ rows: jsonData }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `docxl_export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev);
  }, []);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    exportExcel,
    exportJSON,
    addRow,
    deleteSelectedRows,
    addColumn,
    deleteColumn,
    renameColumn,
    toggleFullscreen,
  }), [exportExcel, exportJSON, addRow, deleteSelectedRows, addColumn, deleteColumn, renameColumn, toggleFullscreen]);

  // Default column properties
  const defaultColDef = useMemo(() => ({
    sortable: true,
    filter: true,
    resizable: true,
    editable: !readOnly,
  }), [readOnly]);

  // Context menu for right-click
  const getContextMenuItems = useCallback((params) => {
    const result = [
      {
        name: 'Add Row Above',
        action: () => {
          const api = params.api;
          const rowIndex = params.node.rowIndex;
          const allCols = api.getColumns()?.map(col => col.getColId()).filter(id => !id.startsWith('_')) || [];
          const newRow = {};
          allCols.forEach(col => {
            newRow[col] = col === 'amount' || col === 'gst' ? 0 : '';
          });
          newRow._rowId = `new_${Date.now()}`;
          newRow.confidence = 1.0;
          api.applyTransaction({ add: [newRow], addIndex: rowIndex });
        },
      },
      {
        name: 'Add Row Below',
        action: () => {
          const api = params.api;
          const rowIndex = params.node.rowIndex + 1;
          const allCols = api.getColumns()?.map(col => col.getColId()).filter(id => !id.startsWith('_')) || [];
          const newRow = {};
          allCols.forEach(col => {
            newRow[col] = col === 'amount' || col === 'gst' ? 0 : '';
          });
          newRow._rowId = `new_${Date.now()}`;
          newRow.confidence = 1.0;
          api.applyTransaction({ add: [newRow], addIndex: rowIndex });
        },
      },
      {
        name: 'Delete Row',
        action: () => {
          const api = params.api;
          api.applyTransaction({ remove: [params.node.data] });
          if (onUpdate) {
            const updatedRows = [];
            api.forEachNode(node => {
              if (node.data) {
                const { _rowNum, _rowId, ...cleanRow } = node.data;
                updatedRows.push(cleanRow);
              }
            });
            onUpdate(updatedRows);
          }
        },
      },
      'separator',
      {
        name: 'Rename Column',
        action: () => {
          const colId = params.column.getColId();
          if (colId === '_rowNum') return;
          const newName = prompt('Enter new column name:', params.column.getColDef().headerName);
          if (newName && newName.trim()) {
            renameColumn(colId, newName.trim());
          }
        },
      },
      {
        name: 'Delete Column',
        action: () => {
          const colId = params.column.getColId();
          if (colId === '_rowNum') return;
          if (confirm(`Delete column "${params.column.getColDef().headerName}"?`)) {
            deleteColumn(colId);
          }
        },
      },
      'separator',
      'copy',
      'paste',
      'separator',
      'export',
    ];
    return result;
  }, [deleteColumn, renameColumn, onUpdate]);

  if (!mounted || rowData.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 bg-gray-50 rounded-lg">
        <div className="text-center text-muted-foreground">
          <p className="text-lg font-medium">No data to display</p>
          <p className="text-sm mt-1">Upload a document to see extracted data here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`ag-spreadsheet-wrapper ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : 'relative'}`}>
      <style jsx global>{`
        .ag-spreadsheet-wrapper .ag-theme-alpine {
          --ag-header-background-color: #f8fafc;
          --ag-header-foreground-color: #334155;
          --ag-border-color: #e2e8f0;
          --ag-row-hover-color: #f1f5f9;
          --ag-selected-row-background-color: #eff6ff;
          font-family: 'Inter', -apple-system, sans-serif;
        }
        .ag-spreadsheet-wrapper .ag-header-cell {
          font-weight: 600;
          font-size: 13px;
        }
        .ag-spreadsheet-wrapper .ag-cell {
          font-size: 13px;
          line-height: 1.5;
        }
        .ag-spreadsheet-wrapper.fixed {
          padding: 1rem;
        }
      `}</style>
      
      {isFullscreen && (
        <div className="flex items-center justify-between p-4 border-b bg-white">
          <h3 className="text-lg font-semibold">Spreadsheet Editor</h3>
          <button
            onClick={toggleFullscreen}
            className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Exit Fullscreen
          </button>
        </div>
      )}
      
      <div className={`ag-theme-alpine ${isFullscreen ? 'h-[calc(100vh-5rem)]' : 'h-[600px]'} w-full`}>
        <AgGridReact
          ref={gridRef}
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onCellValueChanged={onCellValueChanged}
          rowSelection="multiple"
          enableRangeSelection={true}
          enableCellTextSelection={true}
          getContextMenuItems={getContextMenuItems}
          undoRedoCellEditing={true}
          undoRedoCellEditingLimit={20}
          singleClickEdit={false}
          stopEditingWhenCellsLoseFocus={true}
          suppressContextMenu={false}
          animateRows={true}
          suppressMovableColumns={false}
          enableBrowserTooltips={true}
        />
      </div>
    </div>
  );
});

SpreadsheetEditorAG.displayName = 'SpreadsheetEditorAG';

export default SpreadsheetEditorAG;
