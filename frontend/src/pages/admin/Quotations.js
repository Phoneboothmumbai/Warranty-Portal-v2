import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FileText, Send, Check, X, Clock, AlertCircle,
  ChevronRight, RefreshCw, Filter, Eye, Edit,
  Package, Building2, Phone, Mail, Calendar,
  IndianRupee, Plus, Trash2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import { toast } from 'sonner';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700 border-slate-300', icon: FileText },
  sent: { label: 'Sent', color: 'bg-blue-100 text-blue-700 border-blue-300', icon: Send },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-700 border-emerald-300', icon: Check },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700 border-red-300', icon: X },
  expired: { label: 'Expired', color: 'bg-amber-100 text-amber-700 border-amber-300', icon: Clock }
};

const Quotations = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal states
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedQuotation, setSelectedQuotation] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Edit form state
  const [editItems, setEditItems] = useState([]);
  const [editTaxRate, setEditTaxRate] = useState(18);
  const [newItem, setNewItem] = useState({ description: '', quantity: 1, unit_price: 0 });
  
  // Approval state
  const [approvalAction, setApprovalAction] = useState('approve');
  const [rejectionReason, setRejectionReason] = useState('');
  const [customerNotes, setCustomerNotes] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  const fetchQuotations = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      const response = await axios.get(`${API}/api/admin/quotations?${params}`, { headers });
      setQuotations(response.data.quotations || []);
    } catch (err) {
      console.error('Failed to fetch quotations:', err);
      toast.error('Failed to load quotations');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, token]);

  useEffect(() => {
    fetchQuotations();
  }, [fetchQuotations]);

  const handleViewQuotation = async (quotation) => {
    setSelectedQuotation(quotation);
    setShowDetailModal(true);
  };

  const handleEditQuotation = (quotation) => {
    setSelectedQuotation(quotation);
    setEditItems(quotation.items || []);
    setEditTaxRate(quotation.tax_rate || 18);
    setShowEditModal(true);
  };

  const handleSendQuotation = async (quotationId) => {
    setActionLoading(true);
    try {
      await axios.post(`${API}/api/admin/quotations/${quotationId}/send`, {}, { headers });
      toast.success('Quotation sent to customer!');
      fetchQuotations();
      setShowDetailModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send quotation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenApproval = (quotation) => {
    setSelectedQuotation(quotation);
    setApprovalAction('approve');
    setRejectionReason('');
    setCustomerNotes('');
    setShowApprovalModal(true);
  };

  const handleApproveReject = async () => {
    if (approvalAction === 'reject' && !rejectionReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/admin/quotations/${selectedQuotation.id}/approve`,
        {
          approved: approvalAction === 'approve',
          rejection_reason: rejectionReason,
          customer_notes: customerNotes
        },
        { headers }
      );
      toast.success(approvalAction === 'approve' ? 'Quotation approved!' : 'Quotation rejected');
      fetchQuotations();
      setShowApprovalModal(false);
      setShowDetailModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to process approval');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (editItems.length === 0) {
      toast.error('Please add at least one item');
      return;
    }
    
    setActionLoading(true);
    try {
      const formattedItems = editItems.map(item => ({
        item_type: item.item_type || 'part',
        description: item.description,
        quantity: parseInt(item.quantity) || 1,
        unit_price: parseFloat(item.unit_price) || 0,
        part_id: item.part_id,
        part_number: item.part_number
      }));
      
      await axios.put(
        `${API}/api/admin/quotations/${selectedQuotation.id}`,
        { items: formattedItems, tax_rate: editTaxRate },
        { headers }
      );
      toast.success('Quotation updated!');
      fetchQuotations();
      setShowEditModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update quotation');
    } finally {
      setActionLoading(false);
    }
  };

  const addItem = () => {
    if (!newItem.description.trim()) {
      toast.error('Please enter item description');
      return;
    }
    setEditItems([...editItems, { 
      ...newItem, 
      id: `new-${Date.now()}`,
      total_price: newItem.quantity * newItem.unit_price
    }]);
    setNewItem({ description: '', quantity: 1, unit_price: 0 });
  };

  const removeItem = (index) => {
    setEditItems(editItems.filter((_, i) => i !== index));
  };

  const calculateTotals = (items, taxRate) => {
    const subtotal = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
    const tax = subtotal * (taxRate / 100);
    return { subtotal, tax, total: subtotal + tax };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric' 
    });
  };

  const filteredQuotations = quotations.filter(q => {
    if (!searchQuery) return true;
    const search = searchQuery.toLowerCase();
    return (
      q.quotation_number?.toLowerCase().includes(search) ||
      q.ticket_number?.toLowerCase().includes(search) ||
      q.company_name?.toLowerCase().includes(search)
    );
  });

  // Summary counts
  const draftCount = quotations.filter(q => q.status === 'draft').length;
  const sentCount = quotations.filter(q => q.status === 'sent').length;
  const approvedCount = quotations.filter(q => q.status === 'approved').length;

  return (
    <div data-testid="quotations-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Quotations</h1>
          <p className="text-slate-500 text-sm mt-1">Manage parts quotations for service tickets</p>
        </div>
        <Button onClick={fetchQuotations} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:shadow-md" onClick={() => setStatusFilter('draft')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Draft</p>
                <p className="text-2xl font-bold text-slate-700">{draftCount}</p>
              </div>
              <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                <FileText className="h-5 w-5 text-slate-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="cursor-pointer hover:shadow-md" onClick={() => setStatusFilter('sent')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Awaiting Response</p>
                <p className="text-2xl font-bold text-blue-600">{sentCount}</p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Send className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="cursor-pointer hover:shadow-md" onClick={() => setStatusFilter('approved')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Approved</p>
                <p className="text-2xl font-bold text-emerald-600">{approvedCount}</p>
              </div>
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <Check className="h-5 w-5 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="cursor-pointer hover:shadow-md" onClick={() => setStatusFilter('all')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-2xl font-bold text-slate-900">{quotations.length}</p>
              </div>
              <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                <Package className="h-5 w-5 text-slate-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by quotation #, ticket #, or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="sent">Sent</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Quotations Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : filteredQuotations.length === 0 ? (
            <div className="text-center py-12">
              <Package className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No quotations found</p>
              <p className="text-slate-400 text-sm mt-1">
                Quotations are auto-created when engineers request parts
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Quotation #</TableHead>
                  <TableHead>Ticket</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredQuotations.map((quotation) => {
                  const StatusIcon = STATUS_CONFIG[quotation.status]?.icon || FileText;
                  const statusConfig = STATUS_CONFIG[quotation.status] || STATUS_CONFIG.draft;
                  
                  return (
                    <TableRow key={quotation.id} className="cursor-pointer hover:bg-slate-50">
                      <TableCell className="font-mono font-medium text-blue-600">
                        {quotation.quotation_number}
                      </TableCell>
                      <TableCell>
                        <button 
                          className="text-blue-600 hover:underline font-mono text-sm"
                          onClick={() => navigate(`/admin/service-requests/${quotation.ticket_id}`)}
                        >
                          #{quotation.ticket_number}
                        </button>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">{quotation.company_name}</p>
                          <p className="text-xs text-slate-500">{quotation.contact_name}</p>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(quotation.total_amount)}
                      </TableCell>
                      <TableCell>
                        <Badge className={`${statusConfig.color} border`}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-slate-500">
                        {formatDate(quotation.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleViewQuotation(quotation)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {quotation.status === 'draft' && (
                            <>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleEditQuotation(quotation)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button 
                                variant="default" 
                                size="sm"
                                onClick={() => handleSendQuotation(quotation.id)}
                              >
                                <Send className="h-4 w-4 mr-1" />
                                Send
                              </Button>
                            </>
                          )}
                          {quotation.status === 'sent' && (
                            <Button 
                              variant="default" 
                              size="sm"
                              className="bg-emerald-500 hover:bg-emerald-600"
                              onClick={() => handleOpenApproval(quotation)}
                            >
                              <Check className="h-4 w-4 mr-1" />
                              Respond
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Quotation {selectedQuotation?.quotation_number}
            </DialogTitle>
          </DialogHeader>
          
          {selectedQuotation && (
            <div className="space-y-6 mt-4">
              {/* Status Banner */}
              <div className={`rounded-lg p-4 ${
                selectedQuotation.status === 'draft' ? 'bg-slate-50 border border-slate-200' :
                selectedQuotation.status === 'sent' ? 'bg-blue-50 border border-blue-200' :
                selectedQuotation.status === 'approved' ? 'bg-emerald-50 border border-emerald-200' :
                'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <Badge className={`${STATUS_CONFIG[selectedQuotation.status]?.color} border`}>
                    {STATUS_CONFIG[selectedQuotation.status]?.label}
                  </Badge>
                  <span className="text-sm text-slate-500">
                    Created: {formatDate(selectedQuotation.created_at)}
                  </span>
                </div>
              </div>

              {/* Customer Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-500">Customer</Label>
                  <p className="font-medium">{selectedQuotation.company_name}</p>
                  <p className="text-sm text-slate-600">{selectedQuotation.contact_name}</p>
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Contact</Label>
                  <p className="text-sm flex items-center gap-1">
                    <Phone className="h-3 w-3" /> {selectedQuotation.contact_phone || '-'}
                  </p>
                  <p className="text-sm flex items-center gap-1">
                    <Mail className="h-3 w-3" /> {selectedQuotation.contact_email || '-'}
                  </p>
                </div>
              </div>

              {/* Items Table */}
              <div>
                <Label className="text-xs text-slate-500 mb-2 block">Items</Label>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedQuotation.items?.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{item.description || item.item_name}</TableCell>
                        <TableCell className="text-right">{item.quantity}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.total_price)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Totals */}
              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Subtotal</span>
                  <span>{formatCurrency(selectedQuotation.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Tax ({selectedQuotation.tax_rate}%)</span>
                  <span>{formatCurrency(selectedQuotation.tax_amount)}</span>
                </div>
                <div className="flex justify-between font-bold text-lg border-t pt-2">
                  <span>Total</span>
                  <span className="text-emerald-600">{formatCurrency(selectedQuotation.total_amount)}</span>
                </div>
              </div>

              {/* Engineer Remarks */}
              {selectedQuotation.engineer_remarks && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <Label className="text-xs text-amber-700 mb-1 block">Engineer Remarks</Label>
                  <p className="text-sm text-amber-800">{selectedQuotation.engineer_remarks}</p>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowDetailModal(false)}>Close</Button>
            {selectedQuotation?.status === 'draft' && (
              <>
                <Button variant="outline" onClick={() => {
                  setShowDetailModal(false);
                  handleEditQuotation(selectedQuotation);
                }}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                <Button onClick={() => handleSendQuotation(selectedQuotation.id)} disabled={actionLoading}>
                  <Send className="h-4 w-4 mr-2" />
                  {actionLoading ? 'Sending...' : 'Send to Customer'}
                </Button>
              </>
            )}
            {selectedQuotation?.status === 'sent' && (
              <Button 
                className="bg-emerald-500 hover:bg-emerald-600"
                onClick={() => {
                  setShowDetailModal(false);
                  handleOpenApproval(selectedQuotation);
                }}
              >
                <Check className="h-4 w-4 mr-2" />
                Record Response
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Quotation</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            {/* Current Items */}
            <div>
              <Label className="text-sm mb-2 block">Items</Label>
              <div className="space-y-2">
                {editItems.map((item, idx) => (
                  <div key={item.id || idx} className="flex items-center gap-2 bg-slate-50 rounded-lg p-2">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{item.description || item.item_name}</p>
                      <p className="text-xs text-slate-500">
                        Qty: {item.quantity} × {formatCurrency(item.unit_price)} = {formatCurrency(item.quantity * item.unit_price)}
                      </p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => removeItem(idx)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Add New Item */}
            <div className="border rounded-lg p-4 bg-slate-50">
              <Label className="text-sm mb-2 block">Add Item</Label>
              <div className="grid grid-cols-12 gap-2">
                <div className="col-span-6">
                  <Input
                    placeholder="Description"
                    value={newItem.description}
                    onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                  />
                </div>
                <div className="col-span-2">
                  <Input
                    type="number"
                    placeholder="Qty"
                    min="1"
                    value={newItem.quantity}
                    onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                  />
                </div>
                <div className="col-span-3">
                  <Input
                    type="number"
                    placeholder="Unit Price"
                    min="0"
                    value={newItem.unit_price}
                    onChange={(e) => setNewItem({ ...newItem, unit_price: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="col-span-1">
                  <Button onClick={addItem} size="icon">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Tax Rate */}
            <div className="flex items-center gap-4">
              <Label className="text-sm">Tax Rate (%)</Label>
              <Input
                type="number"
                className="w-24"
                value={editTaxRate}
                onChange={(e) => setEditTaxRate(parseFloat(e.target.value) || 0)}
              />
            </div>

            {/* Calculated Totals */}
            {editItems.length > 0 && (
              <div className="border-t pt-4 space-y-1">
                {(() => {
                  const { subtotal, tax, total } = calculateTotals(editItems, editTaxRate);
                  return (
                    <>
                      <div className="flex justify-between text-sm">
                        <span>Subtotal</span>
                        <span>{formatCurrency(subtotal)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Tax ({editTaxRate}%)</span>
                        <span>{formatCurrency(tax)}</span>
                      </div>
                      <div className="flex justify-between font-bold">
                        <span>Total</span>
                        <span className="text-emerald-600">{formatCurrency(total)}</span>
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </div>
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowEditModal(false)}>Cancel</Button>
            <Button onClick={handleSaveEdit} disabled={actionLoading}>
              {actionLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Approval Modal */}
      <Dialog open={showApprovalModal} onOpenChange={setShowApprovalModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Record Customer Response</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-sm text-slate-600">
                Quotation <span className="font-mono font-medium">{selectedQuotation?.quotation_number}</span>
              </p>
              <p className="font-medium">{selectedQuotation?.company_name}</p>
              <p className="text-lg font-bold text-emerald-600 mt-2">
                {formatCurrency(selectedQuotation?.total_amount)}
              </p>
            </div>

            <div className="space-y-2">
              <Label>Customer Response</Label>
              <div className="flex gap-2">
                <Button
                  variant={approvalAction === 'approve' ? 'default' : 'outline'}
                  className={approvalAction === 'approve' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}
                  onClick={() => setApprovalAction('approve')}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Approved
                </Button>
                <Button
                  variant={approvalAction === 'reject' ? 'default' : 'outline'}
                  className={approvalAction === 'reject' ? 'bg-red-500 hover:bg-red-600' : ''}
                  onClick={() => setApprovalAction('reject')}
                >
                  <X className="h-4 w-4 mr-2" />
                  Rejected
                </Button>
              </div>
            </div>

            {approvalAction === 'reject' && (
              <div className="space-y-2">
                <Label>Rejection Reason *</Label>
                <Textarea
                  placeholder="Why did the customer reject?"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  rows={3}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label>Customer Notes (Optional)</Label>
              <Textarea
                placeholder="Any additional notes from customer..."
                value={customerNotes}
                onChange={(e) => setCustomerNotes(e.target.value)}
                rows={2}
              />
            </div>
          </div>
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowApprovalModal(false)}>Cancel</Button>
            <Button 
              onClick={handleApproveReject} 
              disabled={actionLoading}
              className={approvalAction === 'approve' ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-red-500 hover:bg-red-600'}
            >
              {actionLoading ? 'Processing...' : approvalAction === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Quotations;
