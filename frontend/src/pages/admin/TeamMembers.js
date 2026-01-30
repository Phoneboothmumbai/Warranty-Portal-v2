import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle, DialogTrigger 
} from '../../components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Users, UserPlus, Shield, Building2, UserCog, Search, 
  MoreVertical, Mail, Phone, Calendar, Trash2, Edit2, 
  CheckCircle, XCircle, UserCheck, RefreshCw
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Role definitions matching backend TENANT_ROLES
const ROLES = {
  msp_admin: {
    name: 'MSP Admin',
    description: 'Full access to tenant workspace',
    color: 'bg-purple-100 text-purple-800',
    icon: Shield,
    level: 1
  },
  msp_technician: {
    name: 'MSP Technician',
    description: 'Access to assigned companies only',
    color: 'bg-blue-100 text-blue-800',
    icon: UserCog,
    level: 1
  },
  company_admin: {
    name: 'Company Admin',
    description: 'Admin of a specific company',
    color: 'bg-green-100 text-green-800',
    icon: Building2,
    level: 2
  },
  company_employee: {
    name: 'Company Employee',
    description: 'Regular company user',
    color: 'bg-slate-100 text-slate-800',
    icon: Users,
    level: 2
  },
  external_customer: {
    name: 'External Customer',
    description: 'Limited external access',
    color: 'bg-amber-100 text-amber-800',
    icon: UserCheck,
    level: 3
  },
  // Legacy roles (for backward compatibility)
  owner: {
    name: 'Owner',
    description: 'Organization owner with full access',
    color: 'bg-indigo-100 text-indigo-800',
    icon: Shield,
    level: 0
  },
  admin: {
    name: 'Admin',
    description: 'Administrator with full access',
    color: 'bg-purple-100 text-purple-800',
    icon: Shield,
    level: 1
  },
  member: {
    name: 'Member',
    description: 'Team member',
    color: 'bg-blue-100 text-blue-800',
    icon: UserCog,
    level: 1
  }
};

export default function TeamMembers() {
  const [members, setMembers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [activeTab, setActiveTab] = useState('members');
  
  // Modal states
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Form states
  const [inviteForm, setInviteForm] = useState({
    email: '',
    name: '',
    role: 'company_employee',
    company_id: '',
    phone: ''
  });

  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [membersRes, companiesRes] = await Promise.all([
        axios.get(`${API}/api/org/members`, { headers }),
        axios.get(`${API}/api/admin/companies`, { headers })
      ]);
      
      setMembers(membersRes.data || []);
      setCompanies(companiesRes.data || []);
      
      // Fetch assignments for technicians
      try {
        const assignmentsRes = await axios.get(`${API}/api/org/technician-assignments`, { headers });
        setAssignments(assignmentsRes.data || []);
      } catch {
        // Endpoint might not exist yet
        setAssignments([]);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteForm.email || !inviteForm.name) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Validate company selection for company-level roles
    if (['company_admin', 'company_employee', 'external_customer'].includes(inviteForm.role) && !inviteForm.company_id) {
      toast.error('Please select a company for this role');
      return;
    }

    setSaving(true);
    try {
      await axios.post(`${API}/api/org/members`, inviteForm, { headers });
      toast.success('Team member invited successfully');
      setShowInviteModal(false);
      setInviteForm({ email: '', name: '', role: 'company_employee', company_id: '', phone: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to invite member');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateMember = async () => {
    if (!selectedMember) return;
    
    setSaving(true);
    try {
      await axios.put(`${API}/api/org/members/${selectedMember.id}`, {
        name: selectedMember.name,
        role: selectedMember.role,
        company_id: selectedMember.company_id,
        phone: selectedMember.phone,
        is_active: selectedMember.is_active
      }, { headers });
      
      toast.success('Member updated successfully');
      setShowEditModal(false);
      setSelectedMember(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update member');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteMember = async (memberId) => {
    if (!confirm('Are you sure you want to remove this team member?')) return;
    
    try {
      await axios.delete(`${API}/api/org/members/${memberId}`, { headers });
      toast.success('Member removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove member');
    }
  };

  const handleAssignCompany = async (technicianId, companyId) => {
    try {
      await axios.post(`${API}/api/org/technician-assignments`, {
        technician_id: technicianId,
        company_id: companyId
      }, { headers });
      toast.success('Company assigned');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign company');
    }
  };

  const handleUnassignCompany = async (assignmentId) => {
    try {
      await axios.delete(`${API}/api/org/technician-assignments/${assignmentId}`, { headers });
      toast.success('Company unassigned');
      fetchData();
    } catch (error) {
      toast.error('Failed to unassign company');
    }
  };

  // Filter members
  const filteredMembers = members.filter(m => {
    const matchesSearch = 
      m.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.email?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = filterRole === 'all' || m.role === filterRole;
    return matchesSearch && matchesRole;
  });

  // Get technicians for assignment tab
  const technicians = members.filter(m => m.role === 'msp_technician');

  const getRoleBadge = (role) => {
    const roleInfo = ROLES[role] || ROLES.company_employee;
    return (
      <Badge className={`${roleInfo.color} font-medium`}>
        {roleInfo.name}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="team-members-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Team Members</h1>
          <p className="text-slate-500 mt-1">Manage your organization's team and roles</p>
        </div>
        <Button onClick={() => setShowInviteModal(true)} data-testid="invite-member-btn">
          <UserPlus className="w-4 h-4 mr-2" />
          Invite Member
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="members">
            <Users className="w-4 h-4 mr-2" />
            All Members ({members.length})
          </TabsTrigger>
          <TabsTrigger value="assignments">
            <Building2 className="w-4 h-4 mr-2" />
            Technician Assignments
          </TabsTrigger>
        </TabsList>

        {/* Members Tab */}
        <TabsContent value="members" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={filterRole} onValueChange={setFilterRole}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                {Object.entries(ROLES).map(([key, role]) => (
                  <SelectItem key={key} value={key}>{role.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Members Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredMembers.map((member) => {
              const roleInfo = ROLES[member.role] || ROLES.company_employee;
              const RoleIcon = roleInfo.icon;
              const company = companies.find(c => c.id === member.company_id);
              
              return (
                <Card key={member.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${roleInfo.color}`}>
                          <RoleIcon className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-medium text-slate-900">{member.name}</h3>
                          <p className="text-sm text-slate-500">{member.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            setSelectedMember(member);
                            setShowEditModal(true);
                          }}
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteMember(member.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center justify-between">
                        {getRoleBadge(member.role)}
                        <Badge variant={member.is_active ? 'default' : 'secondary'}>
                          {member.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      
                      {company && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <Building2 className="w-3.5 h-3.5" />
                          <span>{company.name}</span>
                        </div>
                      )}
                      
                      {member.phone && (
                        <div className="flex items-center gap-2 text-sm text-slate-500">
                          <Phone className="w-3.5 h-3.5" />
                          <span>{member.phone}</span>
                        </div>
                      )}
                      
                      {member.last_login && (
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <Calendar className="w-3 h-3" />
                          <span>Last login: {new Date(member.last_login).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {filteredMembers.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No members found</h3>
              <p className="text-slate-500 mt-1">
                {searchQuery || filterRole !== 'all' 
                  ? 'Try adjusting your filters' 
                  : 'Invite your first team member to get started'}
              </p>
            </div>
          )}
        </TabsContent>

        {/* Assignments Tab */}
        <TabsContent value="assignments" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Technician Company Assignments</CardTitle>
              <CardDescription>
                Assign MSP technicians to specific client companies they can manage
              </CardDescription>
            </CardHeader>
            <CardContent>
              {technicians.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <UserCog className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p>No MSP technicians found. Invite a team member with the "MSP Technician" role first.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {technicians.map((tech) => {
                    const techAssignments = assignments.filter(a => a.technician_id === tech.id);
                    const assignedCompanyIds = techAssignments.map(a => a.company_id);
                    const availableCompanies = companies.filter(c => !assignedCompanyIds.includes(c.id));
                    
                    return (
                      <div key={tech.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                              <UserCog className="w-5 h-5 text-blue-700" />
                            </div>
                            <div>
                              <h3 className="font-medium text-slate-900">{tech.name}</h3>
                              <p className="text-sm text-slate-500">{tech.email}</p>
                            </div>
                          </div>
                          
                          {availableCompanies.length > 0 && (
                            <Select
                              onValueChange={(companyId) => handleAssignCompany(tech.id, companyId)}
                            >
                              <SelectTrigger className="w-[200px]">
                                <SelectValue placeholder="Assign company..." />
                              </SelectTrigger>
                              <SelectContent>
                                {availableCompanies.map((company) => (
                                  <SelectItem key={company.id} value={company.id}>
                                    {company.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        </div>
                        
                        {/* Assigned companies */}
                        {techAssignments.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {techAssignments.map((assignment) => {
                              const company = companies.find(c => c.id === assignment.company_id);
                              return (
                                <Badge 
                                  key={assignment.id}
                                  variant="secondary"
                                  className="flex items-center gap-2 py-1.5 px-3"
                                >
                                  <Building2 className="w-3.5 h-3.5" />
                                  {company?.name || 'Unknown'}
                                  <button
                                    onClick={() => handleUnassignCompany(assignment.id)}
                                    className="ml-1 hover:bg-slate-200 rounded-full p-0.5"
                                  >
                                    <XCircle className="w-3.5 h-3.5 text-slate-500 hover:text-red-500" />
                                  </button>
                                </Badge>
                              );
                            })}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500 italic">
                            No companies assigned yet
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Invite Modal */}
      <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Invite Team Member</DialogTitle>
            <DialogDescription>
              Send an invitation to join your organization
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="invite-name">Name *</Label>
              <Input
                id="invite-name"
                value={inviteForm.name}
                onChange={(e) => setInviteForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="John Doe"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="invite-email">Email *</Label>
              <Input
                id="invite-email"
                type="email"
                value={inviteForm.email}
                onChange={(e) => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                placeholder="john@example.com"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="invite-phone">Phone</Label>
              <Input
                id="invite-phone"
                value={inviteForm.phone}
                onChange={(e) => setInviteForm(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="+91 98765 43210"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role *</Label>
              <Select 
                value={inviteForm.role} 
                onValueChange={(value) => setInviteForm(prev => ({ ...prev, role: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ROLES).map(([key, role]) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-2">
                        <role.icon className="w-4 h-4" />
                        <span>{role.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">
                {ROLES[inviteForm.role]?.description}
              </p>
            </div>
            
            {/* Company selection for company-level roles */}
            {['company_admin', 'company_employee', 'external_customer'].includes(inviteForm.role) && (
              <div className="space-y-2">
                <Label htmlFor="invite-company">Company *</Label>
                <Select 
                  value={inviteForm.company_id} 
                  onValueChange={(value) => setInviteForm(prev => ({ ...prev, company_id: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select company" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((company) => (
                      <SelectItem key={company.id} value={company.id}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInviteModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleInvite} disabled={saving}>
              {saving ? 'Inviting...' : 'Send Invitation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Team Member</DialogTitle>
            <DialogDescription>
              Update member details and role
            </DialogDescription>
          </DialogHeader>
          
          {selectedMember && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input value={selectedMember.email} disabled className="bg-slate-50" />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  value={selectedMember.name}
                  onChange={(e) => setSelectedMember(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="edit-phone">Phone</Label>
                <Input
                  id="edit-phone"
                  value={selectedMember.phone || ''}
                  onChange={(e) => setSelectedMember(prev => ({ ...prev, phone: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="edit-role">Role</Label>
                <Select 
                  value={selectedMember.role} 
                  onValueChange={(value) => setSelectedMember(prev => ({ ...prev, role: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ROLES).map(([key, role]) => (
                      <SelectItem key={key} value={key}>
                        {role.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {['company_admin', 'company_employee', 'external_customer'].includes(selectedMember.role) && (
                <div className="space-y-2">
                  <Label htmlFor="edit-company">Company</Label>
                  <Select 
                    value={selectedMember.company_id || ''} 
                    onValueChange={(value) => setSelectedMember(prev => ({ ...prev, company_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select company" />
                    </SelectTrigger>
                    <SelectContent>
                      {companies.map((company) => (
                        <SelectItem key={company.id} value={company.id}>
                          {company.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              <div className="flex items-center justify-between pt-2">
                <Label htmlFor="edit-active">Active Status</Label>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-500">
                    {selectedMember.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <Button
                    variant={selectedMember.is_active ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedMember(prev => ({ ...prev, is_active: !prev.is_active }))}
                  >
                    {selectedMember.is_active ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateMember} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
