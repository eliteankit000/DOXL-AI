'use client';
import { useRef, useState, useEffect, useMemo, useCallback, forwardRef, useImperativeHandle } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

/**
 * SpreadsheetEditorAG — CLEAN Excel-like Grid
 * 
 * ✅ Single-click editing
 * ✅ Dynamic columns (NO hardcoding)
 * ✅ Keyboard navigation
 * ✅ Copy/paste
 * ✅ Column resize
 * ✅ Excel export
 * 
 * ❌ NO toolbars
 * ❌ NO context menus
 * ❌ NO add/delete buttons
 * ❌ NO confidence colors
 */

const SpreadsheetEditorAG = forwardRef(({ rows = [], onUpdate, readOnly = false, onReady }, ref) => {
  const gridRef = useRef(null);
  const [mounted, setMounted] = useState(false);
  const [columnDefs, setColumnDefs] = useState([]);
  const [rowData, setRowData] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Notify parent when component is ready
  useEffect(() => {
    if (mounted && rowData.length > 0 && onReady) {
      console.log('[SpreadsheetEditorAG] Component ready, calling onReady callback');
      onReady();
    }
  }, [mounted, rowData.length, onReady]);

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
        resizable: true,
        flex: 1,
        minWidth: 120,
      };

      // Column-specific configs
      if (key === 'amount' || key === 'gst') {
        def.type = 'numericColumn';
        def.valueFormatter = params => {
          const val = parseFloat(params.value);
          return isNaN(val) ? '0.00' : val.toFixed(2);
        };
      } else if (key === 'description') {
        def.minWidth = 280;
        def.wrapText = true;
      } else if (key === 'type') {
        def.cellEditor = 'agSelectCellEditor';
        def.cellEditorParams = {
          values: ['debit', 'credit', 'expense', 'income', 'other'],
        };
      } else if (key === 'category') {
        def.cellEditor = 'agSelectCellEditor';
        def.cellEditorParams = {
          values: ['food', 'transport', 'utilities', 'salary', 'rent', 'transfer', 'shopping', 'healthcare', 'education', 'entertainment', 'other'],
        };
      }

      return def;
    });

    setColumnDefs(colDefs);

    // Transform row data (remove internal fields)
    const transformedRows = rows.map(row => {
      const { _rowNum, _rowId, confidence, row_number, ...cleanRow } = row;
      return cleanRow;
    });

    setRowData(transformedRows);
  }, [rows, readOnly]);

  // Handle cell value changes
  const onCellValueChanged = useCallback((event) => {
    if (!onUpdate) return;
    
    const api = event.api;
    const updatedRows = [];
    
    api.forEachNode(node => {
      if (node.data) {
        updatedRows.push(node.data);
      }
    });
    
    onUpdate(updatedRows);
  }, [onUpdate]);

  // Export to Excel (client-side with SheetJS)
  const exportExcel = useCallback(async (filename) => {
    console.log('[SpreadsheetEditorAG] exportExcel called with filename:', filename);
    try {
      console.log('[SpreadsheetEditorAG] Importing xlsx...');
      const XLSX = (await import('xlsx')).default || (await import('xlsx'));
      console.log('[SpreadsheetEditorAG] xlsx imported:', !!XLSX);
      
      const api = gridRef.current?.api;
      console.log('[SpreadsheetEditorAG] Grid API:', !!api);
      
      if (!api) {
        console.error('[SpreadsheetEditorAG] No grid API found');
        return false;
      }

      // Get all columns
      const allCols = api.getColumns() || [];
      console.log('[SpreadsheetEditorAG] Columns count:', allCols.length);
      const headers = allCols.map(col => col.getColDef().headerName || col.getColId());
      console.log('[SpreadsheetEditorAG] Headers:', headers);

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
      console.log('[SpreadsheetEditorAG] Rows count:', data.length);

      if (data.length === 0) {
        console.warn('[SpreadsheetEditorAG] No data to export');
        alert('No data to export. The spreadsheet is empty.');
        return false;
      }

      // Create worksheet
      console.log('[SpreadsheetEditorAG] Creating worksheet...');
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

      console.log('[SpreadsheetEditorAG] Creating workbook...');
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Extracted Data');
      
      console.log('[SpreadsheetEditorAG] Writing file:', filename);
      XLSX.writeFile(wb, filename || `docxl_export_${Date.now()}.xlsx`);
      
      console.log('[SpreadsheetEditorAG] ✅ Export successful');
      return true;
    } catch (err) {
      console.error('[SpreadsheetEditorAG] ❌ Excel export error:', err);
      alert('Export failed: ' + err.message);
      return false;
    }
  }, []);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    console.log('[SpreadsheetEditorAG] toggleFullscreen called');
    console.log('[SpreadsheetEditorAG] Current fullscreen state:', isFullscreen);
    setIsFullscreen(prev => {
      console.log('[SpreadsheetEditorAG] New fullscreen state:', !prev);
      return !prev;
    });
  }, [isFullscreen]);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    exportExcel,
    toggleFullscreen,
  }), [exportExcel, toggleFullscreen]);

  // Default column properties
  const defaultColDef = useMemo(() => ({
    editable: !readOnly,
    resizable: true,
    sortable: true,
    flex: 1,
    minWidth: 120,
  }), [readOnly]);

  if (!mounted) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (rowData.length === 0) {
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
    <div className={`ag-spreadsheet-wrapper ${isFullscreen ? 'fixed inset-0 z-50 bg-white p-4' : 'relative'}`}>
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
      `}</style>
      
      {isFullscreen && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b">
          <h3 className="text-lg font-semibold">Spreadsheet Editor</h3>
          <button
            onClick={toggleFullscreen}
            className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Exit Fullscreen
          </button>
        </div>
      )}
      
      <div className={`ag-theme-alpine ${isFullscreen ? 'h-[calc(100vh-8rem)]' : 'h-[600px]'} w-full`}>
        <AgGridReact
          ref={gridRef}
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onCellValueChanged={onCellValueChanged}
          rowSelection="multiple"
          enableRangeSelection={true}
          enableCellTextSelection={true}
          undoRedoCellEditing={true}
          undoRedoCellEditingLimit={20}
          singleClickEdit={true}
          stopEditingWhenCellsLoseFocus={true}
          suppressContextMenu={true}
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
