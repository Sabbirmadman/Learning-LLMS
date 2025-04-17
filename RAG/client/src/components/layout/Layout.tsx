import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';


const Layout: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="w-full mx-auto ">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
