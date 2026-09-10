/**
 * Admin User Management Page
 * --------------------------
 * Implements Screenshot 2 design reference.
 * Allows Administrator to view, create, activate, deactivate, edit, and delete users.
 * Passwords in table are strictly masked as "••••••" per Section 3 & 10.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';

const AdminUserManagement = () => {
  const navigate = useNavigate();
  const { logout, currentAdmin } = useAuth();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({ employee_id: '', name: '', password: '' });

  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', status: 'ACTIVE', password: '' });

  const [deletingUser, setDeletingUser] = useState(null);

  // Fetch users list
  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await authService.getUsers();
      setUsers(data);
    } catch (err) {
      setErrorMsg('Failed to load users. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/admin-login');
  };

  // Create User Handler
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!createForm.employee_id.trim() || !createForm.name.trim() || !createForm.password) {
      setErrorMsg('Please fill in all fields.');
      return;
    }

    try {
      await authService.createUser(
        createForm.employee_id.trim(),
        createForm.name.trim(),
        createForm.password
      );
      setSuccessMsg(`User ${createForm.employee_id} created successfully as INACTIVE.`);
      setShowCreateModal(false);
      setCreateForm({ employee_id: '', name: '', password: '' });
      await loadUsers();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create user.');
    }
  };

  // Edit User Handler
  const openEditModal = (user) => {
    setEditingUser(user);
    setEditForm({
      name: user.name,
      status: user.status,
      password: '',
    });
    setErrorMsg('');
    setSuccessMsg('');
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editingUser) return;

    try {
      const payload = {
        name: editForm.name.trim(),
        status: editForm.status,
      };
      if (editForm.password.trim()) {
        payload.password = editForm.password.trim();
      }

      await authService.updateUser(editingUser.id, payload);
      setSuccessMsg(`User ${editingUser.employee_id} updated successfully.`);
      setEditingUser(null);
      await loadUsers();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to update user.');
    }
  };

  // Delete User Handler
  const confirmDelete = async () => {
    if (!deletingUser) return;

    try {
      await authService.deleteUser(deletingUser.id);
      setSuccessMsg(`User ${deletingUser.employee_id} deleted successfully.`);
      setDeletingUser(null);
      await loadUsers();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to delete user.');
    }
  };

  return (
    <div className="admin-layout-container">
      {/* 1. Left Dark Sidebar Matching Screenshot 2 */}
      <aside className="admin-sidebar">
        {/* Top Brand Info */}
        <div className="admin-sidebar-brand">
          <div className="admin-brand-logo-symbol">
            <svg viewBox="0 0 40 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="admin-mountain-svg">
              <path d="M14 2L2 28H18L24 16L14 2Z" fill="#0ea5e9" />
              <path d="M24 10L14 28H38L24 10Z" fill="#10b981" />
            </svg>
          </div>
          <div className="admin-brand-text">
            <h2 className="admin-brand-title">MOIL</h2>
            <h3 className="admin-brand-product">ManganeseInsight</h3>
            <p className="admin-brand-motto">Predict Today, Mine Tomorrow</p>
          </div>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="admin-sidebar-nav">
          <button className="admin-nav-item active" type="button">
            <svg viewBox="0 0 24 24" fill="currentColor" className="admin-nav-icon">
              <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
            </svg>
            <span>User Management</span>
          </button>

          <button className="admin-nav-item logout-item" onClick={handleLogout} type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="admin-nav-icon">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span>Logout</span>
          </button>
        </nav>
      </aside>

      {/* 2. Main Area */}
      <div className="admin-main-viewport">
        {/* Top Header with Admin Profile */}
        <header className="admin-topbar">
          <div className="admin-topbar-right">
            <div className="admin-profile-pill">
              <div className="admin-avatar-circle">
                <svg viewBox="0 0 24 24" fill="currentColor" className="avatar-svg">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              </div>
              <span className="admin-username">{currentAdmin?.name || 'Admin'}</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="chevron-svg">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="admin-content-area">
          {/* Notifications */}
          {errorMsg && (
            <div className="admin-alert-error" role="alert">
              <span>{errorMsg}</span>
              <button type="button" onClick={() => setErrorMsg('')} className="alert-dismiss-btn">×</button>
            </div>
          )}
          {successMsg && (
            <div className="admin-alert-success" role="alert">
              <span>{successMsg}</span>
              <button type="button" onClick={() => setSuccessMsg('')} className="alert-dismiss-btn">×</button>
            </div>
          )}

          {/* Title Header & Create Button */}
          <div className="admin-section-header">
            <div className="admin-title-group">
              <h1 className="admin-page-title">User Management</h1>
              <p className="admin-page-subtitle">Create and manage user accounts for MOIL ManganeseInsight</p>
            </div>
            <button
              type="button"
              className="admin-create-btn"
              onClick={() => setShowCreateModal(true)}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="plus-icon">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>Create User</span>
            </button>
          </div>

          {/* User Table Matching Screenshot 2 */}
          <div className="admin-table-container">
            <table className="admin-users-table">
              <thead>
                <tr>
                  <th style={{ width: '48px' }}>#</th>
                  <th>Employee ID</th>
                  <th>Name</th>
                  <th>Password</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'center', width: '110px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="table-loading-cell">Loading users...</td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="table-empty-cell">No users registered yet.</td>
                  </tr>
                ) : (
                  users.map((u, index) => (
                    <tr key={u.id}>
                      <td className="col-num">{index + 1}</td>
                      <td className="col-emp-id">{u.employee_id}</td>
                      <td className="col-name">{u.name}</td>
                      <td className="col-password">••••••</td>
                      <td className="col-status">
                        <span className={`status-badge ${u.status === 'ACTIVE' ? 'badge-active' : 'badge-inactive'}`}>
                          {u.status === 'ACTIVE' ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="col-actions">
                        <div className="action-buttons-group">
                          {/* Edit Pencil Button */}
                          <button
                            type="button"
                            className="btn-icon-action btn-edit"
                            title={`Edit ${u.employee_id}`}
                            onClick={() => openEditModal(u)}
                          >
                            <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                          </button>

                          {/* Delete Trash Button */}
                          <button
                            type="button"
                            className="btn-icon-action btn-delete"
                            title={`Delete ${u.employee_id}`}
                            onClick={() => setDeletingUser(u)}
                          >
                            <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                              <polyline points="3 6 5 6 21 6" />
                              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer Total Count */}
          <div className="admin-table-footer">
            <span className="total-users-label">Total Users: {users.length}</span>
          </div>
        </main>
      </div>

      {/* CREATE USER MODAL */}
      {showCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3 className="modal-title">Create New User</h3>
              <button type="button" className="modal-close-btn" onClick={() => setShowCreateModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="modal-field">
                <label className="modal-label">Employee ID *</label>
                <input
                  type="text"
                  className="modal-input"
                  placeholder="e.g. MOIL006"
                  value={createForm.employee_id}
                  onChange={(e) => setCreateForm({ ...createForm, employee_id: e.target.value })}
                  required
                />
              </div>

              <div className="modal-field">
                <label className="modal-label">Full Name *</label>
                <input
                  type="text"
                  className="modal-input"
                  placeholder="e.g. Rahul Sharma"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="modal-field">
                <label className="modal-label">Password *</label>
                <input
                  type="password"
                  className="modal-input"
                  placeholder="Initial password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  required
                />
              </div>

              <div className="modal-notice-box">
                <span className="modal-notice-text">
                  Note: Newly created accounts are assigned <strong>INACTIVE</strong> status by default and require administrator activation.
                </span>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT USER MODAL */}
      {editingUser && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3 className="modal-title">Edit User ({editingUser.employee_id})</h3>
              <button type="button" className="modal-close-btn" onClick={() => setEditingUser(null)}>×</button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="modal-field">
                <label className="modal-label">Employee ID</label>
                <input
                  type="text"
                  className="modal-input"
                  value={editingUser.employee_id}
                  disabled
                  readOnly
                />
              </div>

              <div className="modal-field">
                <label className="modal-label">Full Name</label>
                <input
                  type="text"
                  className="modal-input"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="modal-field">
                <label className="modal-label">Account Approval Status</label>
                <select
                  className="modal-select"
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                >
                  <option value="ACTIVE">ACTIVE (Approved - Can Login)</option>
                  <option value="INACTIVE">INACTIVE (Pending Approval - Blocked)</option>
                </select>
              </div>

              <div className="modal-field">
                <label className="modal-label">Change Password (Optional)</label>
                <input
                  type="password"
                  className="modal-input"
                  placeholder="Leave blank to keep unchanged"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setEditingUser(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {deletingUser && (
        <div className="modal-backdrop">
          <div className="modal-card modal-delete-card">
            <div className="modal-header">
              <h3 className="modal-title text-danger">Delete User Account</h3>
              <button type="button" className="modal-close-btn" onClick={() => setDeletingUser(null)}>×</button>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to permanently delete user account:</p>
              <p className="delete-user-highlight">
                <strong>{deletingUser.name}</strong> ({deletingUser.employee_id})
              </p>
              <p className="delete-warning-subtext">This action cannot be undone.</p>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setDeletingUser(null)}>
                Cancel
              </button>
              <button type="button" className="btn-danger" onClick={confirmDelete}>
                Delete User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUserManagement;
