import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Checkbox } from '../../components/ui/checkbox';
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle 
} from '../../components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Users, UserPlus, Shield, Building2, Search, 
  MoreVertical, Mail, Phone, Trash2, Edit2, 
  CheckCircle, XCircle, Play, Pause, Archive,
  FolderTree, Key, History, Plus, ChevronRight,
  AlertTriangle, Lock, Unlock
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// User state badges
const STATE_BADGES = {
  created: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: AlertTriangle },
  active: { label: 'Active', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  suspended: { label: 'Suspended', color: 'bg-red-100 text-red-800', icon: Pause },
  archived: { label: 'Archived', color: 'bg-slate-100 text-slate-800', icon: Archive }
};

export default function StaffManagement() {
  const [activeTab, setActiveTab] = useState('users');
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  
  // Users state
  const [users, setUsers] = useState([]);
  const [usersPagination, setUsersPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [userFilters, setUserFilters] = useState({ search: '', state: '', role_id: '', department_id: '' });
  
  // Departments state
  const [departments, setDepartments] = useState([]);
  
  // Roles state
  const [roles, setRoles] = useState([]);
  
  // Permissions state
  const [permissions, setPermissions] = useState([]);
  const [permissionsGrouped, setPermissionsGrouped] = useState({});
  
  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditPagination, setAuditPagination] = useState({ page: 1, pages: 1, total: 0 });
  
  // Modal states
  const [showUserModal, setShowUserModal] = useState(false);
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showStateModal, setShowStateModal] = useState(false);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedDept, setSelectedDept] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [saving, setSaving] = useState(false);

  // Form states
  const [userForm, setUserForm] = useState({
    email: '', name: '', password: '', user_type: 'internal',
    phone: '', employee_id: '', job_title: '',
    department_ids: [], role_ids: [], assigned_company_ids: []
  });
  
  const [deptForm, setDeptForm] = useState({
    name: '', code: '', description: '', parent_id: '', manager_id: ''
  });
  
  const [roleForm, setRoleForm] = useState({
    name: '', description: '', level: 100, is_default: false
  });
  
  const [stateTransition, setStateTransition] = useState({
    new_state: '', reason: ''
  });

  const getAuthHeaders = () => {
    const token = localStorage.getItem('adminToken');
    return { Authorization: `Bearer ${token}` };
  };

  // Initialize staff module
  const initializeModule = useCallback(async () => {
    try {
      await axios.post(`${API}/api/admin/staff/initialize`, {}, { headers: getAuthHeaders() });
      setInitialized(true);
      toast.success('Staff module initialized');
      fetchAll();
    } catch (error) {
      if (error.response?.status !== 400) {
        toast.error('Failed to initialize staff module');
      }
    }
  }, []);

  // Fetch all data
  const fetchAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([
      fetchUsers(),
      fetchDepartments(),
      fetchRoles(),
      fetchPermissions()
    ]);
    setLoading(false);
  }, []);

  // Fetch users
  const fetchUsers = async (page = 1) => {
    try {
      const params = new URLSearchParams({ page, limit: 20 });
      if (userFilters.search) params.append('search', userFilters.search);
      if (userFilters.state) params.append('state', userFilters.state);
      if (userFilters.role_id) params.append('role_id', userFilters.role_id);
      if (userFilters.department_id) params.append('department_id', userFilters.department_id);
      
      const res = await axios.get(`${API}/api/admin/staff/users?${params}`, { headers: getAuthHeaders() });
      setUsers(res.data.users || []);
      setUsersPagination({ page: res.data.page, pages: res.data.pages, total: res.data.total });
      setInitialized(true);
    } catch (error) {
      if (error.response?.status === 404) {
        setInitialized(false);
      }
      console.error('Error fetching users:', error);
    }
  };

  // Fetch departments
  const fetchDepartments = async () => {
    try {
      const res = await axios.get(`${API}/api/admin/staff/departments`, { headers: getAuthHeaders() });
      setDepartments(res.data.departments || []);
    } catch (error) {
      console.error('Error fetching departments:', error);
    }
  };

  // Fetch roles
  const fetchRoles = async () => {
    try {
      const res = await axios.get(`${API}/api/admin/staff/roles`, { headers: getAuthHeaders() });
      setRoles(res.data.roles || []);
    } catch (error) {
      console.error('Error fetching roles:', error);
    }
  };

  // Fetch permissions
  const fetchPermissions = async () => {
    try {
      const res = await axios.get(`${API}/api/admin/staff/permissions`, { headers: getAuthHeaders() });
      setPermissions(res.data.permissions || []);
      setPermissionsGrouped(res.data.grouped || {});
    } catch (error) {
      console.error('Error fetching permissions:', error);
    }
  };

  // Fetch audit logs
  const fetchAuditLogs = async (page = 1) => {
    try {
      const res = await axios.get(`${API}/api/admin/staff/audit-logs?page=${page}&limit=50`, { headers: getAuthHeaders() });
      setAuditLogs(res.data.logs || []);
      setAuditPagination({ page: res.data.page, pages: res.data.pages, total: res.data.total });
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab]);

  useEffect(() => {
    const debounce = setTimeout(() => fetchUsers(), 300);
    return () => clearTimeout(debounce);
  }, [userFilters]);

  // User CRUD
  const handleSaveUser = async () => {
    setSaving(true);
    try {
      if (selectedUser) {
        await axios.put(`${API}/api/admin/staff/users/${selectedUser.id}`, userForm, { headers: getAuthHeaders() });
        toast.success('User updated');
      } else {
        await axios.post(`${API}/api/admin/staff/users`, userForm, { headers: getAuthHeaders() });
        toast.success('User created');
      }
      setShowUserModal(false);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save user');
    }
    setSaving(false);
  };

  const handleStateChange = async () => {
    if (!selectedUser || !stateTransition.new_state || !stateTransition.reason) {
      toast.error('Please provide state and reason');
      return;
    }
    setSaving(true);
    try {
      await axios.post(`${API}/api/admin/staff/users/${selectedUser.id}/state`, stateTransition, { headers: getAuthHeaders() });
      toast.success(`User ${stateTransition.new_state === 'active' ? 'activated' : stateTransition.new_state}`);
      setShowStateModal(false);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change state');
    }
    setSaving(false);
  };

  // Department CRUD
  const handleSaveDept = async () => {
    setSaving(true);
    try {
      if (selectedDept) {
        await axios.put(`${API}/api/admin/staff/departments/${selectedDept.id}`, deptForm, { headers: getAuthHeaders() });
        toast.success('Department updated');
      } else {
        await axios.post(`${API}/api/admin/staff/departments`, deptForm, { headers: getAuthHeaders() });
        toast.success('Department created');
      }
      setShowDeptModal(false);
      fetchDepartments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save department');
    }
    setSaving(false);
  };

  const handleDeleteDept = async (dept) => {
    if (!window.confirm(`Delete department "${dept.name}"?`)) return;
    try {
      await axios.delete(`${API}/api/admin/staff/departments/${dept.id}`, { headers: getAuthHeaders() });
      toast.success('Department deleted');
      fetchDepartments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete department');
    }
  };

  // Role CRUD
  const handleSaveRole = async () => {
    setSaving(true);
    try {
      if (selectedRole) {
        await axios.put(`${API}/api/admin/staff/roles/${selectedRole.id}`, roleForm, { headers: getAuthHeaders() });
        toast.success('Role updated');
      } else {
        await axios.post(`${API}/api/admin/staff/roles`, roleForm, { headers: getAuthHeaders() });
        toast.success('Role created');
      }
      setShowRoleModal(false);
      fetchRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save role');
    }
    setSaving(false);
  };

  const handleDeleteRole = async (role) => {
    if (!window.confirm(`Delete role "${role.name}"?`)) return;
    try {
      await axios.delete(`${API}/api/admin/staff/roles/${role.id}`, { headers: getAuthHeaders() });
      toast.success('Role deleted');
      fetchRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete role');
    }
  };

  // Open modals
  const openUserModal = (user = null) => {
    setSelectedUser(user);
    setUserForm(user ? {
      email: user.email || '',
      name: user.name || '',
      password: '',
      user_type: user.user_type || 'internal',
      phone: user.phone || '',
      employee_id: user.employee_id || '',
      job_title: user.job_title || '',
      department_ids: user.department_ids || [],
      role_ids: user.role_ids || [],
      assigned_company_ids: user.assigned_company_ids || []
    } : {
      email: '', name: '', password: '', user_type: 'internal',
      phone: '', employee_id: '', job_title: '',
      department_ids: [], role_ids: [], assigned_company_ids: []
    });
    setShowUserModal(true);
  };

  const openStateModal = (user, targetState) => {
    setSelectedUser(user);
    setStateTransition({ new_state: targetState, reason: '' });
    setShowStateModal(true);
  };

  const openDeptModal = (dept = null) => {
    setSelectedDept(dept);
    setDeptForm(dept ? {
      name: dept.name || '',
      code: dept.code || '',
      description: dept.description || '',
      parent_id: dept.parent_id || '',
      manager_id: dept.manager_id || ''
    } : { name: '', code: '', description: '', parent_id: '', manager_id: '' });
    setShowDeptModal(true);
  };

  const openRoleModal = (role = null) => {
    setSelectedRole(role);
    setRoleForm(role ? {
      name: role.name || '',
      description: role.description || '',
      level: role.level || 100,
      is_default: role.is_default || false
    } : { name: '', description: '', level: 100, is_default: false });
    setShowRoleModal(true);
  };

  // Not initialized view
  if (!initialized && !loading) {
    return (
      <div className="p-6" data-testid="staff-not-initialized">
        <Card className="max-w-lg mx-auto">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <CardTitle>Staff Module Setup</CardTitle>
            <CardDescription>
              Initialize the staff module to start managing users, roles, departments, and permissions.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button onClick={initializeModule} className="gap-2">
              <Play className="h-4 w-4" />
              Initialize Staff Module
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="staff-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Staff Management</h1>
          <p className="text-slate-500">Manage users, roles, departments, and permissions</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full max-w-2xl">
          <TabsTrigger value="users" className="gap-2">
            <Users className="h-4 w-4" />
            Users
          </TabsTrigger>
          <TabsTrigger value="departments" className="gap-2">
            <FolderTree className="h-4 w-4" />
            Departments
          </TabsTrigger>
          <TabsTrigger value="roles" className="gap-2">
            <Shield className="h-4 w-4" />
            Roles
          </TabsTrigger>
          <TabsTrigger value="permissions" className="gap-2">
            <Key className="h-4 w-4" />
            Permissions
          </TabsTrigger>
          <TabsTrigger value="audit" className="gap-2">
            <History className="h-4 w-4" />
            Audit
          </TabsTrigger>
        </TabsList>

        {/* USERS TAB */}
        <TabsContent value="users" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search users..."
                      value={userFilters.search}
                      onChange={(e) => setUserFilters(f => ({ ...f, search: e.target.value }))}
                      className="pl-10"
                      data-testid="user-search"
                    />
                  </div>
                </div>
                <Select value={userFilters.state} onValueChange={(v) => setUserFilters(f => ({ ...f, state: v }))}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="All States" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All States</SelectItem>
                    <SelectItem value="created">Pending</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={userFilters.role_id} onValueChange={(v) => setUserFilters(f => ({ ...f, role_id: v }))}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="All Roles" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Roles</SelectItem>
                    {roles.map(role => (
                      <SelectItem key={role.id} value={role.id}>{role.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={() => openUserModal()} className="gap-2" data-testid="add-user-btn">
                  <UserPlus className="h-4 w-4" />
                  Add User
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Users List */}
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-slate-600">User</th>
                      <th className="text-left p-4 font-medium text-slate-600">Roles</th>
                      <th className="text-left p-4 font-medium text-slate-600">Departments</th>
                      <th className="text-left p-4 font-medium text-slate-600">State</th>
                      <th className="text-left p-4 font-medium text-slate-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {users.map(user => {
                      const state = STATE_BADGES[user.state] || STATE_BADGES.created;
                      const StateIcon = state.icon;
                      return (
                        <tr key={user.id} className="hover:bg-slate-50" data-testid={`user-row-${user.id}`}>
                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center font-medium text-slate-600">
                                {user.name?.charAt(0)?.toUpperCase()}
                              </div>
                              <div>
                                <div className="font-medium text-slate-900">{user.name}</div>
                                <div className="text-sm text-slate-500 flex items-center gap-2">
                                  <Mail className="h-3 w-3" />
                                  {user.email}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex flex-wrap gap-1">
                              {(user.roles || []).map(role => (
                                <Badge key={role.id} variant="secondary" className="text-xs">
                                  {role.name}
                                </Badge>
                              ))}
                              {(!user.roles || user.roles.length === 0) && (
                                <span className="text-slate-400 text-sm">No roles</span>
                              )}
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex flex-wrap gap-1">
                              {(user.departments || []).map(dept => (
                                <Badge key={dept.id} variant="outline" className="text-xs">
                                  {dept.name}
                                </Badge>
                              ))}
                              {(!user.departments || user.departments.length === 0) && (
                                <span className="text-slate-400 text-sm">No dept</span>
                              )}
                            </div>
                          </td>
                          <td className="p-4">
                            <Badge className={`${state.color} gap-1`}>
                              <StateIcon className="h-3 w-3" />
                              {state.label}
                            </Badge>
                          </td>
                          <td className="p-4">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => openUserModal(user)}>
                                  <Edit2 className="h-4 w-4 mr-2" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                {user.state === 'created' && (
                                  <DropdownMenuItem onClick={() => openStateModal(user, 'active')}>
                                    <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                                    Activate
                                  </DropdownMenuItem>
                                )}
                                {user.state === 'active' && (
                                  <DropdownMenuItem onClick={() => openStateModal(user, 'suspended')}>
                                    <Pause className="h-4 w-4 mr-2 text-yellow-600" />
                                    Suspend
                                  </DropdownMenuItem>
                                )}
                                {user.state === 'suspended' && (
                                  <DropdownMenuItem onClick={() => openStateModal(user, 'active')}>
                                    <Play className="h-4 w-4 mr-2 text-green-600" />
                                    Reactivate
                                  </DropdownMenuItem>
                                )}
                                {user.state !== 'archived' && (
                                  <DropdownMenuItem onClick={() => openStateModal(user, 'archived')} className="text-red-600">
                                    <Archive className="h-4 w-4 mr-2" />
                                    Archive
                                  </DropdownMenuItem>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </td>
                        </tr>
                      );
                    })}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={5} className="p-8 text-center text-slate-500">
                          No users found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {usersPagination.pages > 1 && (
                <div className="p-4 border-t flex items-center justify-between">
                  <span className="text-sm text-slate-500">
                    Showing {users.length} of {usersPagination.total} users
                  </span>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      disabled={usersPagination.page <= 1}
                      onClick={() => fetchUsers(usersPagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      disabled={usersPagination.page >= usersPagination.pages}
                      onClick={() => fetchUsers(usersPagination.page + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* DEPARTMENTS TAB */}
        <TabsContent value="departments" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Departments</h2>
              <p className="text-sm text-slate-500">Organize users into departments for reporting and filtering</p>
            </div>
            <Button onClick={() => openDeptModal()} className="gap-2" data-testid="add-dept-btn">
              <Plus className="h-4 w-4" />
              Add Department
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {departments.map(dept => (
              <Card key={dept.id} data-testid={`dept-card-${dept.id}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                        <FolderTree className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{dept.name}</CardTitle>
                        {dept.code && (
                          <span className="text-xs text-slate-500">{dept.code}</span>
                        )}
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openDeptModal(dept)}>
                          <Edit2 className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleDeleteDept(dept)} className="text-red-600">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent>
                  {dept.description && (
                    <p className="text-sm text-slate-600 mb-3">{dept.description}</p>
                  )}
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <Users className="h-4 w-4" />
                    {dept.user_count || 0} users
                  </div>
                </CardContent>
              </Card>
            ))}
            {departments.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="p-8 text-center text-slate-500">
                  No departments created yet
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* ROLES TAB */}
        <TabsContent value="roles" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Roles</h2>
              <p className="text-sm text-slate-500">Define roles with specific permissions</p>
            </div>
            <Button onClick={() => openRoleModal()} className="gap-2" data-testid="add-role-btn">
              <Plus className="h-4 w-4" />
              Add Role
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {roles.map(role => (
              <Card key={role.id} data-testid={`role-card-${role.id}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                        <Shield className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base flex items-center gap-2">
                          {role.name}
                          {role.is_system && (
                            <Badge variant="outline" className="text-xs">System</Badge>
                          )}
                          {role.is_default && (
                            <Badge className="bg-blue-100 text-blue-800 text-xs">Default</Badge>
                          )}
                        </CardTitle>
                        <span className="text-xs text-slate-500">Level: {role.level}</span>
                      </div>
                    </div>
                    {!role.is_system && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openRoleModal(role)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDeleteRole(role)} className="text-red-600">
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {role.description && (
                    <p className="text-sm text-slate-600 mb-3">{role.description}</p>
                  )}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500 flex items-center gap-1">
                      <Key className="h-4 w-4" />
                      {(role.permissions || []).length} permissions
                    </span>
                    <span className="text-slate-500 flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {role.user_count || 0} users
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
            {roles.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="p-8 text-center text-slate-500">
                  No roles created yet
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* PERMISSIONS TAB */}
        <TabsContent value="permissions" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Permissions</h2>
              <p className="text-sm text-slate-500">View and manage permission definitions</p>
            </div>
          </div>

          {Object.entries(permissionsGrouped).map(([category, perms]) => (
            <Card key={category}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{category}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                  {perms.map(perm => (
                    <div 
                      key={perm.id}
                      className="p-3 border rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      <div className="font-medium text-sm">{perm.name}</div>
                      <div className="text-xs text-slate-500 font-mono">
                        {perm.module}.{perm.resource}.{perm.action}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* AUDIT TAB */}
        <TabsContent value="audit" className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold">Audit Logs</h2>
            <p className="text-sm text-slate-500">Track all changes to users, roles, and permissions</p>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-slate-600">Timestamp</th>
                      <th className="text-left p-4 font-medium text-slate-600">Action</th>
                      <th className="text-left p-4 font-medium text-slate-600">Entity</th>
                      <th className="text-left p-4 font-medium text-slate-600">Changed By</th>
                      <th className="text-left p-4 font-medium text-slate-600">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {auditLogs.map(log => (
                      <tr key={log.id} className="hover:bg-slate-50">
                        <td className="p-4 text-sm text-slate-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="p-4">
                          <Badge variant={log.severity === 'warning' ? 'destructive' : 'secondary'}>
                            {log.action}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <span className="font-medium">{log.entity_type}</span>
                          {log.entity_name && (
                            <span className="text-slate-500 ml-1">({log.entity_name})</span>
                          )}
                        </td>
                        <td className="p-4 text-sm">{log.performed_by_name}</td>
                        <td className="p-4 text-sm text-slate-500 max-w-xs truncate">
                          {JSON.stringify(log.changes)}
                        </td>
                      </tr>
                    ))}
                    {auditLogs.length === 0 && (
                      <tr>
                        <td colSpan={5} className="p-8 text-center text-slate-500">
                          No audit logs found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* USER MODAL */}
      <Dialog open={showUserModal} onOpenChange={setShowUserModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedUser ? 'Edit User' : 'Add New User'}</DialogTitle>
            <DialogDescription>
              {selectedUser ? 'Update user details and assignments' : 'Create a new staff user'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Name *</Label>
                <Input
                  value={userForm.name}
                  onChange={(e) => setUserForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="Full name"
                  data-testid="user-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Email *</Label>
                <Input
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm(f => ({ ...f, email: e.target.value }))}
                  placeholder="email@example.com"
                  disabled={!!selectedUser}
                  data-testid="user-email-input"
                />
              </div>
            </div>
            {!selectedUser && (
              <div className="space-y-2">
                <Label>Password</Label>
                <Input
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm(f => ({ ...f, password: e.target.value }))}
                  placeholder="Leave blank to send invite"
                />
                <p className="text-xs text-slate-500">If blank, user will receive an invite email</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input
                  value={userForm.phone}
                  onChange={(e) => setUserForm(f => ({ ...f, phone: e.target.value }))}
                  placeholder="+91..."
                />
              </div>
              <div className="space-y-2">
                <Label>Employee ID</Label>
                <Input
                  value={userForm.employee_id}
                  onChange={(e) => setUserForm(f => ({ ...f, employee_id: e.target.value }))}
                  placeholder="EMP001"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Job Title</Label>
              <Input
                value={userForm.job_title}
                onChange={(e) => setUserForm(f => ({ ...f, job_title: e.target.value }))}
                placeholder="e.g., Senior Technician"
              />
            </div>
            <div className="space-y-2">
              <Label>Roles</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-lg max-h-32 overflow-y-auto">
                {roles.map(role => (
                  <label key={role.id} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={userForm.role_ids.includes(role.id)}
                      onCheckedChange={(checked) => {
                        setUserForm(f => ({
                          ...f,
                          role_ids: checked 
                            ? [...f.role_ids, role.id]
                            : f.role_ids.filter(id => id !== role.id)
                        }));
                      }}
                    />
                    <span className="text-sm">{role.name}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label>Departments</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-lg max-h-32 overflow-y-auto">
                {departments.map(dept => (
                  <label key={dept.id} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={userForm.department_ids.includes(dept.id)}
                      onCheckedChange={(checked) => {
                        setUserForm(f => ({
                          ...f,
                          department_ids: checked 
                            ? [...f.department_ids, dept.id]
                            : f.department_ids.filter(id => id !== dept.id)
                        }));
                      }}
                    />
                    <span className="text-sm">{dept.name}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUserModal(false)}>Cancel</Button>
            <Button onClick={handleSaveUser} disabled={saving || !userForm.name || !userForm.email}>
              {saving ? 'Saving...' : selectedUser ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* STATE TRANSITION MODAL */}
      <Dialog open={showStateModal} onOpenChange={setShowStateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {stateTransition.new_state === 'active' ? 'Activate' : 
               stateTransition.new_state === 'suspended' ? 'Suspend' : 'Archive'} User
            </DialogTitle>
            <DialogDescription>
              {selectedUser?.name} ({selectedUser?.email})
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Reason *</Label>
              <Textarea
                value={stateTransition.reason}
                onChange={(e) => setStateTransition(s => ({ ...s, reason: e.target.value }))}
                placeholder="Provide a reason for this action (required for audit)"
                rows={3}
              />
            </div>
            {stateTransition.new_state === 'archived' && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                <strong>Warning:</strong> Archiving a user is permanent. They will not be able to log in and cannot be reactivated.
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStateModal(false)}>Cancel</Button>
            <Button 
              onClick={handleStateChange} 
              disabled={saving || !stateTransition.reason}
              variant={stateTransition.new_state === 'archived' ? 'destructive' : 'default'}
            >
              {saving ? 'Processing...' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* DEPARTMENT MODAL */}
      <Dialog open={showDeptModal} onOpenChange={setShowDeptModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedDept ? 'Edit Department' : 'Add Department'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Name *</Label>
                <Input
                  value={deptForm.name}
                  onChange={(e) => setDeptForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g., Engineering"
                  data-testid="dept-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Code</Label>
                <Input
                  value={deptForm.code}
                  onChange={(e) => setDeptForm(f => ({ ...f, code: e.target.value }))}
                  placeholder="e.g., ENG"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={deptForm.description}
                onChange={(e) => setDeptForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Department description..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeptModal(false)}>Cancel</Button>
            <Button onClick={handleSaveDept} disabled={saving || !deptForm.name}>
              {saving ? 'Saving...' : selectedDept ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ROLE MODAL */}
      <Dialog open={showRoleModal} onOpenChange={setShowRoleModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedRole ? 'Edit Role' : 'Add Role'}</DialogTitle>
            <DialogDescription>
              Roles start with zero permissions. Assign permissions after creating.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Name *</Label>
              <Input
                value={roleForm.name}
                onChange={(e) => setRoleForm(f => ({ ...f, name: e.target.value }))}
                placeholder="e.g., Field Technician"
                data-testid="role-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={roleForm.description}
                onChange={(e) => setRoleForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Role description..."
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Level</Label>
                <Input
                  type="number"
                  value={roleForm.level}
                  onChange={(e) => setRoleForm(f => ({ ...f, level: parseInt(e.target.value) || 100 }))}
                  min={0}
                  max={100}
                />
                <p className="text-xs text-slate-500">Lower = higher authority (0=admin, 100=default)</p>
              </div>
              <div className="space-y-2 flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={roleForm.is_default}
                    onCheckedChange={(checked) => setRoleForm(f => ({ ...f, is_default: checked }))}
                  />
                  <span className="text-sm">Default role for new users</span>
                </label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRoleModal(false)}>Cancel</Button>
            <Button onClick={handleSaveRole} disabled={saving || !roleForm.name}>
              {saving ? 'Saving...' : selectedRole ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
