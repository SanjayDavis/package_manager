import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function PackageDownloadsTable({ search }) {
  const [downloads, setDownloads] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    const fetchDownloads = async () => {
      setLoading(true);
      try {
        const response = await axios.get('http://localhost:8000/api/packagedownloads', {
          params: { search, page },
          headers: { Authorization: `Bearer ${token}` }
        });
        setDownloads(response.data.data);
        setTotalPages(response.data.totalPages);
        setTotal(response.data.total);
      } catch (error) {
        console.error('Failed to fetch downloads:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDownloads();
  }, [search, page, token]);

  return (
    <div className="animate-fade-in">
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-green-600"></div>
        </div>
      ) : downloads.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-xl">No download records found</p>
          {search && <p className="text-sm mt-2">Try a different search term</p>}
        </div>
      ) : (
        <>
          <div className="mb-4 text-gray-600">
            {search ? (
              <p>Found {total} download records matching "{search}"</p>
            ) : (
              <p>Showing latest 100 of {total} total downloads</p>
            )}
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white rounded-lg shadow-md">
              <thead className="bg-gradient-to-r from-green-500 to-teal-500 text-white">
                <tr>
                  <th className="px-4 py-3">User ID</th>
                  <th className="px-4 py-3">Package</th>
                  <th className="px-4 py-3">Version</th>
                  <th className="px-4 py-3">Download Time</th>
                  <th className="px-4 py-3">Download (s)</th>
                  <th className="px-4 py-3">Install (s)</th>
                  <th className="px-4 py-3">IP</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {downloads.map((dl, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50 transition">
                    <td className="px-4 py-3 text-sm">{dl.user_id}</td>
                    <td className="px-4 py-3 text-sm font-semibold">{dl.package_name}</td>
                    <td className="px-4 py-3 text-sm">{dl.version}</td>
                    <td className="px-4 py-3 text-sm">{new Date(dl.download_timestamp).toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm">{dl.download_duration_seconds}</td>
                    <td className="px-4 py-3 text-sm">{dl.install_duration_seconds}</td>
                    <td className="px-4 py-3 text-sm">{dl.client_ip}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded ${dl.download_status === 'success' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                        {dl.download_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {totalPages > 1 && (
            <div className="flex justify-center items-center space-x-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-green-700 transition"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-gray-700">Page {page} of {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-green-700 transition"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
