/**
 * App Component
 *
 * 应用根组件
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import NavBar from './components/Header/NavBar';
import Home from './pages/Home';
import Tasks from './pages/Tasks';
import History from './pages/History';
import Settings from './pages/Settings';

const { Header, Content } = Layout;

function App() {
  return (
    <Router>
      <Layout className="app-root">
        <Header className="app-header">
          <NavBar />
        </Header>
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            {/* 重定向其他路径到首页 */}
            <Route path="*" element={<Home />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
}

export default App;