import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function DependenciesTable({ search }) {
  const [dependencies, setDependencies] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    const fetchDependencies = async () => {
      setLoading(true);
      try {
        const response = await axios.get('http://localhost:8000/api/dependencies', {
          params: { search, page },
          headers: { Authorization: `Bearer ${token}` }
        });
        setDependencies(response.data.data);
        setTotalPages(response.data.totalPages);
        setTotal(response.data.total);
      } catch (error) {
        console.error('Failed to fetch dependencies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDependencies();
  }, [search, page, token]);

  return (
    <div className="animate-fade-in">
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-600"></div>
        </div>
      ) : dependencies.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-xl">No dependencies found</p>
          {search && <p className="text-sm mt-2">Try a different search term</p>}
        </div>
      ) : (
        <>
          <div className="mb-4 text-gray-600">
            {search ? (
              <p>Found {total} dependencies matching "{search}"</p>
            ) : (
              <p>Showing top 100 of {total} total dependencies</p>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dependencies.map((dep, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-4 hover:shadow-xl transition">
                <p className="text-gray-800">
                  <span className="font-semibold text-blue-600">{dep.package_name}</span> depends on{' '}
                  <span className="font-semibold text-green-600">{dep.dependency_name}</span>
                  {dep.version_constraint && (
                    <span className="text-sm text-gray-500"> ({dep.version_constraint})</span>
                  )}
                </p>
              </div>
            ))}
          </div>
          
          {totalPages > 1 && (
            <div className="flex justify-center items-center space-x-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-blue-700 transition"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-gray-700">Page {page} of {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-blue-700 transition"
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
