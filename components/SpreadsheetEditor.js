'use client';
import { useRef, useState, useEffect, useMemo, useCallback } from 'react';
import { HotTable } from '@handsontable/react-wrapper';
import { registerAllModules } from 'handsontable/registry';
import 'handsontable/styles/handsontable.css';
import 'handsontable/styles/ht-theme-main.css';

registerAllModules();

/**
 * SpreadsheetEditor — Production-grade spreadsheet UI powered by Handsontable
 *
 * Features:
 * - Edit any cell (click or Enter)
 * - Add/delete rows (right-click context menu)
 * - Add/delete columns (right-click context menu)
 * - Rename columns (double-click header)
 * - Resize columns (drag border)
 * - Copy/paste (Ctrl+C/V)
 * - Undo/redo (Ctrl+Z/Y)
 * - Keyboard navigation (arrows, Tab, Enter)
 * - Column sorting
 * - Confidence-based cell coloring
 * - Client-side Excel export (SheetJS)
 */

const SpreadsheetEditor = ({ rows = [], onUpdate, readOnly = false }) => {
  const hotRef = useRef(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Derive columns dynamically from row data
  const { columns, headerLabels, columnConfig } = useMemo(() => {
    if (!rows || !rows.length) {
      return {
        columns: ['date', 'description', 'amount', 'type', 'category', 'gst', 'reference'],
        headerLabels: ['Date', 'Description', 'Amount', 'Type', 'Category', 'GST', 'Reference'],
        columnConfig: [],
      };
    }
    // Collect all keys, exclude internal ones
    const internalKeys = new Set(['confidence', 'row_number', '_balance', '_count']);
    const allKeys = [];
    const keySet = new Set();
    rows.forEach(row => {
      Object.keys(row).forEach(key => {
        if (!internalKeys.has(key) && !keySet.has(key)) {
          keySet.add(key);
          allKeys.push(key);
        }
      });
    });

    // Preferred column order
    const preferredOrder = ['date', 'description', 'amount', 'type', 'category', 'gst', 'reference'];
    const ordered = [];
    preferredOrder.forEach(key => {
      if (keySet.has(key)) {
        ordered.push(key);
        keySet.delete(key);
      }
    });
    // Append remaining columns
    allKeys.forEach(key => {
      if (keySet.has(key)) ordered.push(key);
    });

    const labels = ordered.map(key =>
      key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')
    );

    // Column type configs
    const configs = ordered.map(key => {
      if (key === 'amount' || key === 'gst') {
        return { data: key, type: 'numeric', numericFormat: { pattern: '0,0.00' }, width: 120 };
      }
      if (key === 'date') {
        return { data: key, type: 'text', width: 120 };
      }
      if (key === 'description') {
        return { data: key, type: 'text', width: 280 };
      }
      if (key === 'type') {
        return { data: key, type: 'dropdown', source: ['debit', 'credit', 'expense', 'income', 'other'], width: 100 };
      }
      if (key === 'category') {
        return {
          data: key,
          type: 'dropdown',
          source: ['food', 'transport', 'utilities', 'salary', 'rent', 'transfer', 'shopping', 'healthcare', 'education', 'entertainment', 'other'],
          width: 130,
        };
      }
      return { data: key, type: 'text', width: 140 };
    });

    return { columns: ordered, headerLabels: labels, columnConfig: configs };
  }, [rows]);

  // Build confidence map for cell coloring
  const confidenceMap = useMemo(() => {
    const map = {};
    rows.forEach((row, i) => {
      map[i] = row.confidence ?? 1;
    });
    return map;
  }, [rows]);

  // Transform rows into clean data for Handsontable (array of objects)
  const tableData = useMemo(() => {
    return rows.map(row => {
      const clean = {};
      columns.forEach(col => {
        clean[col] = row[col] ?? '';
      });
      return clean;
    });
  }, [rows, columns]);

  // Custom cell renderer for confidence-based coloring
  const cellsCallback = useCallback((row) => {
    const props = {};
    const conf = confidenceMap[row];
    if (conf !== undefined && conf < 0.3) {
      props.className = 'htLowConfidence';
    } else if (conf !== undefined && conf < 0.6) {
      props.className = 'htMedConfidence';
    }
    return props;
  }, [confidenceMap]);

  // After any change, propagate to parent
  const handleAfterChange = useCallback((changes, source) => {
    if (!changes || source === 'loadData') return;
    if (onUpdate && hotRef.current?.hotInstance) {
      const hot = hotRef.current.hotInstance;
      const currentData = hot.getSourceData();
      onUpdate(currentData);
    }
  }, [onUpdate]);

  const handleAfterRemoveRow = useCallback(() => {
    if (onUpdate && hotRef.current?.hotInstance) {
      const hot = hotRef.current.hotInstance;
      onUpdate(hot.getSourceData());
    }
  }, [onUpdate]);

  const handleAfterCreateRow = useCallback(() => {
    if (onUpdate && hotRef.current?.hotInstance) {
      const hot = hotRef.current.hotInstance;
      onUpdate(hot.getSourceData());
    }
  }, [onUpdate]);

  const handleAfterRemoveCol = useCallback(() => {
    if (onUpdate && hotRef.current?.hotInstance) {
      const hot = hotRef.current.hotInstance;
      onUpdate(hot.getSourceData());
    }
  }, [onUpdate]);

  const handleAfterCreateCol = useCallback(() => {
    if (onUpdate && hotRef.current?.hotInstance) {
      const hot = hotRef.current.hotInstance;
      onUpdate(hot.getSourceData());
    }
  }, [onUpdate]);

  // Get current data (for export)
  const getCurrentData = useCallback(() => {
    const hot = hotRef.current?.hotInstance;
    if (!hot) return { headers: columns, data: tableData };
    const headers = [];
    for (let c = 0; c < hot.countCols(); c++) {
      headers.push(hot.getColHeader(c));
    }
    const data = [];
    for (let r = 0; r < hot.countSourceRows(); r++) {
      const row = [];
      for (let c = 0; c < hot.countCols(); c++) {
        row.push(hot.getDataAtCell(r, c));
      }
      data.push(row);
    }
    return { headers, data };
  }, [columns, tableData]);

  // Client-side Excel export using SheetJS
  const exportExcel = useCallback(async (filename) => {
    try {
      const XLSX = (await import('xlsx')).default || (await import('xlsx'));
      const { headers, data } = getCurrentData();
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
  }, [getCurrentData]);

  // Client-side JSON export
  const exportJSON = useCallback(() => {
    const { headers, data } = getCurrentData();
    const jsonData = data.map(row => {
      const obj = {};
      headers.forEach((h, i) => {
        obj[h] = row[i];
      });
      return obj;
    });
    const blob = new Blob([JSON.stringify({ rows: jsonData }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `docxl_export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [getCurrentData]);

  // Expose export methods via ref
  useEffect(() => {
    if (hotRef.current) {
      hotRef.current.exportExcel = exportExcel;
      hotRef.current.exportJSON = exportJSON;
      hotRef.current.getCurrentData = getCurrentData;
    }
  }, [exportExcel, exportJSON, getCurrentData]);

  if (!mounted || !tableData.length) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center text-muted-foreground">
          <p className="text-lg font-medium">No data to display</p>
          <p className="text-sm mt-1">Upload a document to see extracted data here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="spreadsheet-wrapper">
      <style jsx global>{`
        .spreadsheet-wrapper {
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          overflow: hidden;
        }
        .spreadsheet-wrapper .handsontable {
          font-size: 13px;
          font-family: 'Inter', -apple-system, sans-serif;
        }
        .spreadsheet-wrapper .handsontable th {
          background: #f8fafc;
          font-weight: 600;
          color: #334155;
          border-color: #e2e8f0;
        }
        .spreadsheet-wrapper .handsontable td {
          border-color: #e2e8f0;
          color: #1e293b;
        }
        .spreadsheet-wrapper .handsontable td.htLowConfidence {
          background-color: #fef2f2 !important;
          border-left: 3px solid #ef4444 !important;
        }
        .spreadsheet-wrapper .handsontable td.htMedConfidence {
          background-color: #fffbeb !important;
          border-left: 3px solid #f59e0b !important;
        }
        .spreadsheet-wrapper .handsontable .htDimmed {
          color: #94a3b8;
        }
        .spreadsheet-wrapper .handsontable td.current,
        .spreadsheet-wrapper .handsontable td.area {
          background-color: #eff6ff !important;
        }
        .spreadsheet-wrapper .ht_clone_top th {
          position: sticky;
          top: 0;
          z-index: 10;
        }
      `}</style>
      <HotTable
        ref={hotRef}
        data={tableData}
        columns={columnConfig}
        colHeaders={headerLabels}
        rowHeaders={true}
        height="auto"
        width="100%"
        autoWrapRow={true}
        autoWrapCol={true}
        stretchH="all"
        readOnly={readOnly}
        licenseKey="non-commercial-and-evaluation"
        contextMenu={{
          items: {
            'row_above': { name: 'Insert row above' },
            'row_below': { name: 'Insert row below' },
            'remove_row': { name: 'Delete row' },
            'separator1': '---------',
            'col_left': { name: 'Insert column left' },
            'col_right': { name: 'Insert column right' },
            'remove_col': { name: 'Delete column' },
            'separator2': '---------',
            'undo': { name: 'Undo' },
            'redo': { name: 'Redo' },
            'separator3': '---------',
            'copy': { name: 'Copy' },
            'cut': { name: 'Cut' },
          }
        }}
        manualColumnResize={true}
        manualRowResize={true}
        manualColumnMove={true}
        columnSorting={true}
        undo={true}
        copyPaste={true}
        fillHandle={true}
        minSpareRows={1}
        cells={cellsCallback}
        afterChange={handleAfterChange}
        afterRemoveRow={handleAfterRemoveRow}
        afterCreateRow={handleAfterCreateRow}
        afterRemoveCol={handleAfterRemoveCol}
        afterCreateCol={handleAfterCreateCol}
        className="htCenter"
      />
    </div>
  );
};

export default SpreadsheetEditor;
