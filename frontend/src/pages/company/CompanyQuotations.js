import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileText, Send, Check, X, Clock, 
  Package, Building2, Phone, Mail, Calendar,
  IndianRupee, RefreshCw, Eye
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
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
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700 border-slate-300', icon: FileText },
  sent: { label: 'Awaiting Response', color: 'bg-blue-100 text-blue-700 border-blue-300', icon: Send },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-700 border-emerald-300', icon: Check },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700 border-red-300', icon: X },
  expired: { label: 'Expired', color: 'bg-amber-100 text-amber-700 border-amber-300', icon: Clock }
};

const CompanyQuotations = () => {
  const { token } = useCompanyAuth();
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedQuotation, setSelectedQuotation] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [responseAction, setResponseAction] = useState('approve');
  const [responseNotes, setResponseNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchQuotations = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/company/quotations`, { 
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuotations(response.data.quotations || []);
    } catch (err) {
      console.error('Failed to fetch quotations:', err);
      toast.error('Failed to load quotations');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchQuotations();
  }, [fetchQuotations]);

  const handleViewQuotation = (quotation) => {
    setSelectedQuotation(quotation);
    setShowDetailModal(true);
  };

  const handleOpenResponse = (quotation) => {
    setSelectedQuotation(quotation);
    setResponseAction('approve');
    setResponseNotes('');
    setShowResponseModal(true);
  };

  const handleSubmitResponse = async () => {
    if (responseAction === 'reject' && !responseNotes.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }

    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/company/quotations/${selectedQuotation.id}/respond`,
        null,
        { 
          headers,
          params: {
            approved: responseAction === 'approve',
            notes: responseNotes || null
          }
        }
      );
      toast.success(responseAction === 'approve' ? 'Quotation approved!' : 'Quotation rejected');
      fetchQuotations();
      setShowResponseModal(false);
      setShowDetailModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit response');
    } finally {
      setActionLoading(false);
    }
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

  // Counts
  const pendingCount = quotations.filter(q => q.status === 'sent').length;
  const approvedCount = quotations.filter(q => q.status === 'approved').length;

  return (
    <div data-testid="company-quotations-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Quotations</h1>
          <p className="text-slate-500 text-sm mt-1">Review and respond to service quotations</p>
        </div>
        <Button onClick={fetchQuotations} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-blue-50 border-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Pending Response</p>
                <p className="text-3xl font-bold text-blue-700">{pendingCount}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Send className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-emerald-50 border-emerald-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Approved</p>
                <p className="text-3xl font-bold text-emerald-700">{approvedCount}</p>
              </div>
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                <Check className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-3xl font-bold text-slate-900">{quotations.length}</p>
              </div>
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center">
                <FileText className="h-6 w-6 text-slate-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Quotations Alert */}
      {pendingCount > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Send className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="font-medium text-blue-900">
                You have {pendingCount} quotation{pendingCount > 1 ? 's' : ''} awaiting your response
              </p>
              <p className="text-sm text-blue-700">
                Please review and approve or reject to proceed with service.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quotations List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : quotations.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No quotations found</p>
              <p className="text-slate-400 text-sm mt-1">
                Quotations will appear here when service requires parts approval.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Quotation #</TableHead>
                  <TableHead>Ticket</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Sent Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {quotations.map((quotation) => {
                  const StatusIcon = STATUS_CONFIG[quotation.status]?.icon || FileText;
                  const statusConfig = STATUS_CONFIG[quotation.status] || STATUS_CONFIG.sent;
                  
                  return (
                    <TableRow key={quotation.id} className="cursor-pointer hover:bg-slate-50">
                      <TableCell className="font-mono font-medium text-emerald-600">
                        {quotation.quotation_number}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-slate-600">#{quotation.ticket_number}</span>
                      </TableCell>
                      <TableCell className="font-medium text-lg">
                        {formatCurrency(quotation.total_amount)}
                      </TableCell>
                      <TableCell>
                        <Badge className={`${statusConfig.color} border`}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-slate-500">
                        {formatDate(quotation.sent_at)}
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
                          {quotation.status === 'sent' && (
                            <Button 
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700"
                              onClick={() => handleOpenResponse(quotation)}
                            >
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
                selectedQuotation.status === 'sent' ? 'bg-blue-50 border border-blue-200' :
                selectedQuotation.status === 'approved' ? 'bg-emerald-50 border border-emerald-200' :
                selectedQuotation.status === 'rejected' ? 'bg-red-50 border border-red-200' :
                'bg-slate-50 border border-slate-200'
              }`}>
                <div className="flex items-center justify-between">
                  <Badge className={`${STATUS_CONFIG[selectedQuotation.status]?.color} border`}>
                    {STATUS_CONFIG[selectedQuotation.status]?.label}
                  </Badge>
                  <span className="text-sm text-slate-500">
                    Sent: {formatDate(selectedQuotation.sent_at)}
                  </span>
                </div>
                {selectedQuotation.status === 'sent' && (
                  <p className="text-sm text-blue-700 mt-2">
                    Please review the items and approve or reject this quotation.
                  </p>
                )}
              </div>

              {/* Ticket Reference */}
              <div className="bg-slate-50 rounded-lg p-4">
                <Label className="text-xs text-slate-500 mb-1 block">Related Service Ticket</Label>
                <p className="font-mono text-lg font-medium">#{selectedQuotation.ticket_number}</p>
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
                <div className="flex justify-between font-bold text-xl border-t pt-2">
                  <span>Total</span>
                  <span className="text-emerald-600">{formatCurrency(selectedQuotation.total_amount)}</span>
                </div>
              </div>

              {/* Notes from engineer */}
              {selectedQuotation.engineer_remarks && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <Label className="text-xs text-amber-700 mb-1 block">Engineer Remarks</Label>
                  <p className="text-sm text-amber-800">{selectedQuotation.engineer_remarks}</p>
                </div>
              )}

              {/* Terms */}
              {selectedQuotation.terms_and_conditions && (
                <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded">
                  <p className="font-medium mb-1">Terms & Conditions:</p>
                  <p>{selectedQuotation.terms_and_conditions}</p>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowDetailModal(false)}>Close</Button>
            {selectedQuotation?.status === 'sent' && (
              <Button 
                className="bg-emerald-600 hover:bg-emerald-700"
                onClick={() => {
                  setShowDetailModal(false);
                  handleOpenResponse(selectedQuotation);
                }}
              >
                <Check className="h-4 w-4 mr-2" />
                Respond to Quotation
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Response Modal */}
      <Dialog open={showResponseModal} onOpenChange={setShowResponseModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Respond to Quotation</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-sm text-slate-600">
                Quotation <span className="font-mono font-medium">{selectedQuotation?.quotation_number}</span>
              </p>
              <p className="text-2xl font-bold text-emerald-600 mt-2">
                {formatCurrency(selectedQuotation?.total_amount)}
              </p>
            </div>

            <div className="space-y-2">
              <Label>Your Response</Label>
              <div className="flex gap-2">
                <Button
                  variant={responseAction === 'approve' ? 'default' : 'outline'}
                  className={responseAction === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700 flex-1' : 'flex-1'}
                  onClick={() => setResponseAction('approve')}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Approve
                </Button>
                <Button
                  variant={responseAction === 'reject' ? 'default' : 'outline'}
                  className={responseAction === 'reject' ? 'bg-red-600 hover:bg-red-700 flex-1' : 'flex-1'}
                  onClick={() => setResponseAction('reject')}
                >
                  <X className="h-4 w-4 mr-2" />
                  Reject
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>{responseAction === 'reject' ? 'Reason for Rejection *' : 'Additional Notes (Optional)'}</Label>
              <Textarea
                placeholder={responseAction === 'reject' ? 'Please explain why you are rejecting...' : 'Any comments or notes...'}
                value={responseNotes}
                onChange={(e) => setResponseNotes(e.target.value)}
                rows={3}
              />
            </div>

            {responseAction === 'approve' && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-800">
                <p className="font-medium">By approving this quotation:</p>
                <ul className="mt-1 list-disc list-inside text-emerald-700">
                  <li>Parts will be ordered and the service will proceed</li>
                  <li>You agree to the quoted amount of {formatCurrency(selectedQuotation?.total_amount)}</li>
                </ul>
              </div>
            )}
          </div>
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowResponseModal(false)}>Cancel</Button>
            <Button 
              onClick={handleSubmitResponse} 
              disabled={actionLoading}
              className={responseAction === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'}
            >
              {actionLoading ? 'Submitting...' : responseAction === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CompanyQuotations;
