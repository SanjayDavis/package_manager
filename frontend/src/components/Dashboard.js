import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const API_URL = 'http://localhost:8000';

function Dashboard({ token, onLogout }) {
  const [activeTab, setActiveTab] = useState('packages');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [updating, setUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState('');

  useEffect(() => {
    fetchData();
  }, [activeTab, page, search]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const endpoint = activeTab === 'packages' ? '/api/packages' 
                     : activeTab === 'dependencies' ? '/api/dependencies'
                     : '/api/packagedownloads';
      
      const response = await fetch(
        `${API_URL}${endpoint}?page=${page}&search=${search}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const result = await response.json();
        setData(result.data);
        setTotalPages(result.totalPages);
        setTotal(result.total);
      }
    } catch (error) {
      console.error('Fetch error:', error);
    }
    setLoading(false);
  };

  const handleUpdatePackages = async () => {
    if (!window.confirm('This will update all packages from Ubuntu repositories. Continue?')) {
      return;
    }

    setUpdating(true);
    setUpdateMessage('Downloading packages from Ubuntu repositories...');

    try {
      const response = await fetch(`${API_URL}/api/update-packages`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });

      const result = await response.json();
      
      if (response.ok) {
        setUpdateMessage(result.status);
        setTimeout(() => {
          setUpdateMessage('');
          fetchData();
        }, 3000);
      } else {
        setUpdateMessage('Update failed: ' + result.error);
      }
    } catch (error) {
      setUpdateMessage('Update failed: ' + error.message);
    }
    
    setUpdating(false);
  };

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const renderTable = () => {
    if (loading) {
      return (
        <div className="table-loading">
          <div className="loading-spinner-small">
            <div className="spinner-ring-small"></div>
          </div>
          <p>Loading data...</p>
        </div>
      );
    }

    if (data.length === 0) {
      return (
        <div className="no-data">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
            <path d="M9 2L7 7H2L7 11L5 16L10 12L15 16L13 11L18 7H13L11 2H9Z" 
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <h3>No data found</h3>
          <p>Try adjusting your search or check back later</p>
        </div>
      );
    }

    return (
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              {activeTab === 'packages' && (
                <>
                  <th>Name</th>
                  <th>Version</th>
                  <th>Architecture</th>
                  <th>Filename</th>
                </>
              )}
              {activeTab === 'dependencies' && (
                <>
                  <th>Package</th>
                  <th>Dependency</th>
                  <th>Version Constraint</th>
                </>
              )}
              {activeTab === 'downloads' && (
                <>
                  <th>User</th>
                  <th>Package</th>
                  <th>Version</th>
                  <th>Download Time</th>
                  <th>Install Time</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                {activeTab === 'packages' && (
                  <>
                    <td><span className="package-name">{row.name}</span></td>
                    <td><span className="version-badge">{row.version}</span></td>
                    <td><span className="arch-badge">{row.architecture}</span></td>
                    <td className="filename-cell">{row.filename}</td>
                  </>
                )}
                {activeTab === 'dependencies' && (
                  <>
                    <td><span className="package-name">{row.package_name}</span></td>
                    <td>{row.dependency_name}</td>
                    <td><span className="constraint-badge">{row.version_constraint || 'any'}</span></td>
                  </>
                )}
                {activeTab === 'downloads' && (
                  <>
                    <td><span className="user-badge">{row.user_id}</span></td>
                    <td><span className="package-name">{row.package_name}</span></td>
                    <td><span className="version-badge">{row.version}</span></td>
                    <td>{row.download_duration_seconds}s</td>
                    <td>{row.install_duration_seconds}s</td>
                    <td>
                      <span className={`status-badge ${row.install_status === 'success' ? 'success' : 'failed'}`}>
                        {row.install_status}
                      </span>
                    </td>
                    <td className="timestamp">{new Date(row.download_timestamp).toLocaleString()}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-container">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
              <path d="M20 7L12 3L4 7M20 7L12 11M20 7V17L12 21M12 11L4 7M12 11V21M4 7V17L12 21" 
                    stroke="url(#gradient2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <defs>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
            </svg>
            <h2>Package<br/>Manager</h2>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeTab === 'packages' ? 'active' : ''}`}
            onClick={() => { setActiveTab('packages'); setPage(1); }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M20 7L12 3L4 7M20 7L12 11M20 7V17L12 21M12 11L4 7M12 11V21M4 7V17L12 21" 
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Packages</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'dependencies' ? 'active' : ''}`}
            onClick={() => { setActiveTab('dependencies'); setPage(1); }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2"/>
              <circle cx="5" cy="12" r="2" stroke="currentColor" strokeWidth="2"/>
              <circle cx="19" cy="12" r="2" stroke="currentColor" strokeWidth="2"/>
              <path d="M7 12H9M15 12H17" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span>Dependencies</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'downloads' ? 'active' : ''}`}
            onClick={() => { setActiveTab('downloads'); setPage(1); }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 15V3M12 15L8 11M12 15L16 11M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19L22 17" 
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Package Downloads</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <button className="logout-button" onClick={onLogout}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9M16 17L21 12M21 12L16 7M21 12H9" 
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="dashboard-header">
          <div className="header-content">
            <div>
              <h1>
                {activeTab === 'packages' && 'Packages'}
                {activeTab === 'dependencies' && 'Dependencies'}
                {activeTab === 'downloads' && 'Package Downloads'}
              </h1>
              <p className="total-count">{total.toLocaleString()} total items</p>
            </div>
            
            {activeTab === 'packages' && (
              <button 
                className="update-button" 
                onClick={handleUpdatePackages}
                disabled={updating}
              >
                {updating ? (
                  <>
                    <div className="button-spinner"></div>
                    Updating...
                  </>
                ) : (
                  <>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M4 4V9H4.58152M19.9381 11C19.446 7.05369 16.0796 4 12 4C8.64262 4 5.76829 6.06817 4.58152 9M4.58152 9H9M20 20V15H19.4185M19.4185 15C18.2317 17.9318 15.3574 20 12 20C7.92038 20 4.55399 16.9463 4.06189 13M19.4185 15H15" 
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    Update Packages
                  </>
                )}
              </button>
            )}
          </div>

          {updateMessage && (
            <div className={`update-message ${updating ? 'loading' : 'success'}`}>
              {updateMessage}
            </div>
          )}
        </header>

        <div className="content-body">
          <div className="search-bar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
              <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={search}
              onChange={handleSearchChange}
            />
            {search && (
              <button className="clear-search" onClick={() => setSearch('')}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>
            )}
          </div>

          {renderTable()}

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="pagination-button"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M15 18L9 12L15 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Previous
              </button>

              <div className="pagination-info">
                Page <span className="current-page">{page}</span> of <span>{totalPages}</span>
              </div>

              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="pagination-button"
              >
                Next
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
