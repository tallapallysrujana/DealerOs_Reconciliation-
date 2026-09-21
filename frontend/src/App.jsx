import { useState, useEffect } from 'react';
import { getDisagreements } from './api';
import './App.css';

function App() {
  const [disagreements, setDisagreements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filter and sort states
  const [filterType, setFilterType] = useState('');
  const [filterOrg, setFilterOrg] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => {
    fetchDisagreements();
  }, [filterType, filterOrg, sortBy, sortOrder]);

  const fetchDisagreements = async () => {
    try {
      setLoading(true);
      const params = {};
      
      if (filterType) params.disagreement_type = filterType;
      if (filterOrg) params.org_id = filterOrg;
      if (sortBy) params.ordering = `${sortOrder === 'desc' ? '-' : ''}${sortBy}`;
      
      const data = await getDisagreements(params);
      setDisagreements(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch disagreements. Make sure the Django backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return parseFloat(value).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const getDisagreementTypeLabel = (type) => {
    const labels = {
      'MISSING_IN_B': 'Missing in System B',
      'ORPHAN_ENTRY': 'Orphan Entry',
      'DUPLICATE_ENTRY': 'Duplicate Entry',
      'VALUE_MISMATCH': 'Value Mismatch'
    };
    return labels[type] || type;
  };

  if (loading) {
    return <div className="container">Loading disagreements...</div>;
  }

  if (error) {
    return <div className="container error">{error}</div>;
  }

  return (
    <div className="container">
      <h1>Dealer Os Reconciliation</h1>
      
      <div className="filters">
        <div className="filter-group">
          <label htmlFor="filterType">Filter by Type:</label>
          <select
            id="filterType"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="MISSING_IN_B">Missing in System B</option>
            <option value="ORPHAN_ENTRY">Orphan Entry</option>
            <option value="DUPLICATE_ENTRY">Duplicate Entry</option>
            <option value="VALUE_MISMATCH">Value Mismatch</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filterOrg">Filter by Organization:</label>
          <select
            id="filterOrg"
            value={filterOrg}
            onChange={(e) => setFilterOrg(e.target.value)}
          >
            <option value="">All Organizations</option>
            <option value="ORG-A">ORG-A</option>
            <option value="ORG-B">ORG-B</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="sortBy">Sort by:</label>
          <select
            id="sortBy"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="created_at">Date Created</option>
            <option value="system_a_value">System A Value</option>
            <option value="system_b_value">System B Value</option>
            <option value="record_id">Record ID</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="sortOrder">Order:</label>
          <select
            id="sortOrder"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      <div className="summary">
        <p>Total disagreements: <strong>{disagreements.length}</strong></p>
      </div>

      {disagreements.length === 0 ? (
        <p className="no-data">No disagreements found with current filters.</p>
      ) : (
        <table className="disagreements-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('record_id')} className="sortable">
                Record ID {sortBy === 'record_id' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Location</th>
              <th>Organization</th>
              <th onClick={() => handleSort('disagreement_type')} className="sortable">
                Type {sortBy === 'disagreement_type' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('system_a_value')} className="sortable">
                System A Value {sortBy === 'system_a_value' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('system_b_value')} className="sortable">
                System B Value {sortBy === 'system_b_value' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {disagreements.map((disagreement) => (
              <tr key={disagreement.id}>
                <td>{disagreement.record_id}</td>
                <td>{disagreement.location_name}</td>
                <td>{disagreement.org_id}</td>
                <td>{getDisagreementTypeLabel(disagreement.disagreement_type)}</td>
                <td>{formatValue(disagreement.system_a_value)}</td>
                <td>{formatValue(disagreement.system_b_value)}</td>
                <td className="details-cell">{disagreement.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;