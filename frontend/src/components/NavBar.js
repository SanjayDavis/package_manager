import React from 'react';

export default function NavBar({ onLogout }) {
  const username = localStorage.getItem('username') || 'Admin';
  const role = localStorage.getItem('userRole');

  return (
    <nav className="bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="text-xl font-bold">Package Manager</div>
        <div className="flex items-center space-x-4">
          <span>Logged in as: <span className="font-semibold">{username}</span> ({role})</span>
          <button
            onClick={() => {
              onLogout();
              localStorage.clear();
            }}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg transition transform hover:scale-105"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
