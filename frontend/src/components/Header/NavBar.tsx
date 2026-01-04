import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button, Drawer, Menu, Grid, Avatar } from 'antd';
import type { MenuProps } from 'antd';

const { useBreakpoint } = Grid;

const menuItems: MenuProps['items'] = [
  { key: 'home', label: <Link to="/">首页</Link> },
  { key: 'tasks', label: <Link to="/tasks">任务</Link> },
  { key: 'knowledge', label: <Link to="/knowledge">知识库</Link> },
  { key: 'history', label: <Link to="/history">历史</Link> },
  { key: 'settings', label: <Link to="/settings">设置</Link> },
];

const NavBar: React.FC = () => {
  const [open, setOpen] = useState(false);
  const screens = useBreakpoint();

  const showDrawer = () => setOpen(true);
  const closeDrawer = () => setOpen(false);

  return (
    <div className="nav">
      <div className="nav-left">
        <div className="app-logo">RS</div>
        <div className="nav-brand">
          <div className="app-title-text">ResearchSync-Agent</div>
          <div className="app-subtitle">AI 研究助手</div>
        </div>
      </div>

      <div className="nav-right">
        {screens.md ? (
          <Menu mode="horizontal" selectable={false} items={menuItems} className="nav-menu" />
        ) : (
          <>
            <Button type="text" className="nav-toggle" onClick={showDrawer} aria-label="打开菜单">
              ☰
            </Button>
            <Drawer placement="right" onClose={closeDrawer} open={open} bodyStyle={{ padding: 0 }}>
              <div style={{ padding: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <Avatar style={{ background: 'var(--accent-primary)' }}>RS</Avatar>
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>ResearchSync-Agent</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>实时研究与任务管理</div>
                  </div>
                </div>
                <Menu mode="vertical" selectable={false} items={menuItems} onClick={closeDrawer} />
              </div>
            </Drawer>
          </>
        )}
      </div>
    </div>
  );
};

export default NavBar;


