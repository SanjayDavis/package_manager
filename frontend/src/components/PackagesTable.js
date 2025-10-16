import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function PackagesTable({ search }) {
  const [packages, setPackages] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    const fetchPackages = async () => {
      setLoading(true);
      try {
        const response = await axios.get('http://localhost:8000/api/packages', {
          params: { search, page },
          headers: { Authorization: `Bearer ${token}` }
        });
        setPackages(response.data.data);
        setTotalPages(response.data.totalPages);
        setTotal(response.data.total);
      } catch (error) {
        console.error('Failed to fetch packages:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPackages();
  }, [search, page, token]);

  return (
    <div className="animate-fade-in">
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-purple-600"></div>
        </div>
      ) : packages.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-xl">No packages found</p>
          {search && <p className="text-sm mt-2">Try a different search term</p>}
        </div>
      ) : (
        <>
          <div className="mb-4 text-gray-700 font-medium">
            {search ? (
              <p>Found <span className="text-purple-600 font-bold">{total}</span> packages matching "{search}"</p>
            ) : (
              <p>Showing top 100 of <span className="text-purple-600 font-bold">{total}</span> total packages</p>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {packages.map(pkg => (
              <div key={pkg.id} className="bg-white rounded-lg shadow-md p-4 hover:shadow-xl transition transform hover:-translate-y-1">
                <h3 className="font-bold text-lg text-purple-600 mb-2">{pkg.name}</h3>
                <p className="text-sm text-gray-600"><span className="font-semibold">Version:</span> {pkg.version}</p>
                <p className="text-sm text-gray-600"><span className="font-semibold">Architecture:</span> {pkg.architecture}</p>
                <p className="text-sm text-gray-600 truncate"><span className="font-semibold">File:</span> {pkg.filename}</p>
              </div>
            ))}
          </div>
          
          {totalPages > 1 && (
            <div className="flex justify-center items-center space-x-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-purple-700 transition"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-gray-700 font-medium">Page {page} of {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-purple-700 transition"
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
