import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';

const Layout = () => {
  return (
    <div className="container">
      <Header />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
