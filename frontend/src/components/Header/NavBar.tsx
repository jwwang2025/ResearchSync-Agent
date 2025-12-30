import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button, Drawer, Menu, Grid, Avatar } from 'antd';
import type { MenuProps } from 'antd';

const { useBreakpoint } = Grid;

const menuItems: MenuProps['items'] = [
  { key: 'home', label: <a href="#/">首页</a> },
  { key: 'tasks', label: <a href="#/tasks">任务</a> },
  { key: 'history', label: <a href="#/history">历史</a> },
  { key: 'docs', label: <a href="#/docs">文档</a> },
  { key: 'settings', label: <a href="#/settings">设置</a> },
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
          <div className="app-subtitle muted">研究任务 · 实时同步</div>
        </div>
      </div>

      <div className="nav-right">
        {screens.md ? (
          <Menu mode="horizontal" theme="dark" selectable={false} items={menuItems} className="nav-menu" />
        ) : (
          <>
            <Button type="text" className="nav-toggle" onClick={showDrawer} aria-label="打开菜单">
              ☰
            </Button>
            <Drawer placement="right" onClose={closeDrawer} open={open} bodyStyle={{ padding: 0 }}>
              <div style={{ padding: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <Avatar style={{ background: '#6c8cff' }}>RS</Avatar>
                  <div>
                    <div style={{ fontWeight: 700 }}>ResearchSync-Agent</div>
                    <div className="muted" style={{ fontSize: 12 }}>实时研究与任务管理</div>
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


