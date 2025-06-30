import React, { useState, useEffect } from 'react';
import { api, dbApi, endpoints } from '../services/api';

interface TableData {
  table_name: string;
  columns: string[];
  row_count: number;
  column_count: number;
  data: any[];
  total_rows: number;
  displayed_rows: number;
}

interface DatabaseInspectionProps {
  isOpen: boolean;
  onClose: () => void;
}

const DatabaseInspection: React.FC<DatabaseInspectionProps> = ({ isOpen, onClose }) => {
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingTables, setLoadingTables] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      fetchTables();
    }
  }, [isOpen]);

  useEffect(() => {
    if (selectedTable) {
      fetchTableData(selectedTable);
    } else {
      setTableData(null);
    }
  }, [selectedTable]);

  const fetchTables = async () => {
    setLoadingTables(true);
    setError('');
    try {
      const response = await dbApi.get(endpoints.databaseTables);
      setTables(response.data.tables);
      setError('');
    } catch (error: any) {
      console.error('Error fetching tables:', error);
      if (error.code === 'ECONNABORTED') {
        setError('Database operation timed out. Please try again or check if the backend is busy.');
      } else {
        setError('Failed to fetch database tables. Please check if the backend is running.');
      }
    } finally {
      setLoadingTables(false);
    }
  };

  const fetchTableData = async (tableName: string) => {
    setLoading(true);
    setError('');
    try {
      const response = await dbApi.get(endpoints.databaseTable(tableName));
      setTableData(response.data);
    } catch (error: any) {
      console.error('Error fetching table data:', error);
      if (error.code === 'ECONNABORTED') {
        setError('Database operation timed out. The table might be large or the backend is busy.');
      } else {
        setError('Failed to fetch table data. Please try again.');
      }
      setTableData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: any): string | JSX.Element => {
    if (value === null || value === undefined) {
      return 'NULL';
    }

    // Check if it's a JSON string containing an array
    if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed) && parsed.length > 10 && parsed.every(item => typeof item === 'number')) {
          // This is likely an embedding - show compact format
          const firstFew = parsed.slice(0, 3);
          const lastFew = parsed.slice(-3);
          return <span className="array-content embedding-content" data-array-content="true" title={`Full embedding: ${parsed.length} values`}>
            [{firstFew.join(', ')} ... {lastFew.join(', ')}] ({parsed.length} values)
          </span>;
        }
      } catch (e) {
        // Not valid JSON, continue with normal processing
      }
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return '[]';
      }

      // Special handling for embedding arrays (large arrays of numbers)
      if (value.length > 10 && value.every(item => typeof item === 'number')) {
        const firstFew = value.slice(0, 3);
        const lastFew = value.slice(-3);
        return <span className="array-content embedding-content" data-array-content="true" title={`Full embedding: ${value.length} values`}>
          [{firstFew.join(', ')} ... {lastFew.join(', ')}] ({value.length} values)
        </span>;
      }

      if (value.length <= 4) {
        return <span className="array-content" data-array-content="true">
          {JSON.stringify(value)}
        </span>;
      }
      // Limit to 4 items and show count
      const limited = value.slice(0, 4);
      return <span className="array-content" data-array-content="true">
        {JSON.stringify(limited)} (+{value.length - 4} more)
      </span>;
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal database-inspection-modal">
        <div className="modal-header">
          <h3>Database Inspection</h3>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-content">
          {/* Table Selection */}
          <div className="table-selection">
            <label htmlFor="table-select">Select Table:</label>
            {loadingTables ? (
              <div className="loading">Loading tables...</div>
            ) : (
              <select
                id="table-select"
                value={selectedTable}
                onChange={(e) => setSelectedTable(e.target.value)}
                className="input"
              >
                <option value="">Choose a table...</option>
                {tables.map((table) => (
                  <option key={table} value={table}>
                    {table}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="error-message">
              {error}
              <button
                className="btn btn-outline retry-btn"
                onClick={loadingTables ? fetchTables : () => selectedTable && fetchTableData(selectedTable)}
                disabled={loadingTables || loading}
              >
                Retry
              </button>
            </div>
          )}

          {/* Table Information */}
          {tableData && (
            <div className="table-info">
              <div className="table-stats">
                <span className="stat">
                  <strong>Table:</strong> {tableData.table_name}
                </span>
                <span className="stat">
                  <strong>Size:</strong> {tableData.row_count} rows × {tableData.column_count} columns
                </span>
                {tableData.total_rows > tableData.displayed_rows && (
                  <span className="stat">
                    <strong>Showing:</strong> {tableData.displayed_rows} of {tableData.total_rows} rows
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="loading">
              Loading table data...
            </div>
          )}

          {/* Table Data */}
          {tableData && !loading && (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    {tableData.columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableData.data.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {tableData.columns.map((column) => (
                        <td key={column} className="table-cell">
                          {formatValue(row[column])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* No Data Message */}
          {tableData && !loading && tableData.data.length === 0 && (
            <div className="no-data">
              No data found in this table.
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatabaseInspection;