import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Shield, ArrowLeft, Download, CheckCircle2, XCircle, 
  AlertCircle, Laptop, Printer, Monitor, Router, Camera,
  HardDrive, Cpu, Building2, User, Calendar, Package, Wrench
} from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const deviceIcons = {
  'Laptop': Laptop,
  'CCTV': Camera,
  'NVR': Camera,
  'DVR': Camera,
  'Printer': Printer,
  'Monitor': Monitor,
  'Router': Router,
  'Server': HardDrive,
  'Desktop': Cpu,
  'HDD': HardDrive,
  'SSD': HardDrive,
  'RAM': Cpu,
};

const WarrantyResult = () => {
  const { serialNumber } = useParams();
  const navigate = useNavigate();
  const { settings } = useSettings();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWarrantyData();
  }, [serialNumber]);

  const fetchWarrantyData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/warranty/search`, {
        params: { q: serialNumber }
      });
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch warranty information');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    window.open(`${API}/warranty/pdf/${encodeURIComponent(serialNumber)}`, '_blank');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const DeviceIcon = data?.search_type === 'part' 
    ? (deviceIcons[data?.part?.part_type] || HardDrive)
    : (data?.device?.device_type ? (deviceIcons[data.device.device_type] || Laptop) : Laptop);

  // Check if this is a part search result
  const isPart = data?.search_type === 'part';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500">Looking up warranty...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="w-full px-6 py-4 bg-white border-b border-slate-100">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3">
            {(settings.logo_base64 || settings.logo_url) ? (
              <img 
                src={settings.logo_base64 || settings.logo_url} 
                alt="Logo" 
                className="h-8 w-auto"
              />
            ) : (
              <Shield className="h-7 w-7 text-[#0F62FE]" />
            )}
            <span className="text-lg font-semibold text-slate-900">{settings.company_name}</span>
          </Link>
          <Button 
            variant="ghost" 
            onClick={() => navigate('/')}
            className="text-slate-500 hover:text-slate-700"
            data-testid="back-to-search-btn"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            New Search
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {error ? (
            /* Error State */
            <div className="receipt-card p-12 text-center animate-fade-in" data-testid="warranty-error">
              <div className="w-16 h-16 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertCircle className="h-8 w-8 text-amber-500" />
              </div>
              <h2 className="text-2xl font-semibold text-slate-900 mb-3">No Records Found</h2>
              <p className="text-slate-500 mb-8 max-w-md mx-auto">
                {error}. Please verify the Serial Number or Asset Tag and try again.
              </p>
              <Button 
                onClick={() => navigate('/')}
                className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                data-testid="try-again-btn"
              >
                Try Another Search
              </Button>
            </div>
          ) : data ? (
            /* Success State - The Receipt */
            <div className="animate-slide-up">
              {/* Part or Device Card */}
              <div className="receipt-card mb-6" data-testid="warranty-result-card">
                {/* Header Strip */}
                <div className={`${isPart ? 'bg-blue-900' : 'bg-slate-900'} px-8 py-6 text-white`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 bg-white/10 rounded-xl flex items-center justify-center">
                        <DeviceIcon className="h-7 w-7 text-white" />
                      </div>
                      <div>
                        {isPart ? (
                          <>
                            <p className="text-blue-300 text-xs uppercase tracking-wide mb-1">Component / Part</p>
                            <h1 className="text-xl font-semibold">{data.part.brand || ''} {data.part.part_name}</h1>
                            <p className="text-blue-300 text-sm mt-0.5">{data.part.part_type} {data.part.capacity ? `• ${data.part.capacity}` : ''}</p>
                          </>
                        ) : (
                          <>
                            <h1 className="text-xl font-semibold">{data.device.brand} {data.device.model}</h1>
                            <p className="text-slate-400 text-sm mt-0.5">{data.device.device_type}</p>
                          </>
                        )}
                      </div>
                    </div>
                    <div className={`px-4 py-1.5 rounded-full text-sm font-medium ${
                      (isPart ? data.part.warranty_active : data.device.warranty_active)
                        ? 'bg-emerald-500/20 text-emerald-300' 
                        : 'bg-slate-700 text-slate-400'
                    }`}>
                      {(isPart ? data.part.warranty_active : data.device.warranty_active) ? 'Under Warranty' : 'Warranty Expired'}
                    </div>
                  </div>
                </div>

                {/* Details */}
                <div className="p-8">
                  {isPart ? (
                    /* Part Details */
                    <>
                      <div className="grid sm:grid-cols-2 gap-6 mb-8">
                        <div className="space-y-4">
                          <div className="data-pair">
                            <span className="data-label">Serial Number</span>
                            <span className="data-value font-mono" data-testid="serial-number">{data.part.serial_number}</span>
                          </div>
                          {data.part.model_number && (
                            <div className="data-pair">
                              <span className="data-label">Model Number</span>
                              <span className="data-value font-mono">{data.part.model_number}</span>
                            </div>
                          )}
                          <div className="data-pair">
                            <span className="data-label">Installation Date</span>
                            <span className="data-value">{formatDate(data.part.replaced_date)}</span>
                          </div>
                        </div>
                        <div className="space-y-4">
                          <div className="data-pair">
                            <span className="data-label flex items-center gap-2">
                              <Building2 className="h-3.5 w-3.5" />
                              Company
                            </span>
                            <span className="data-value">{data.company_name}</span>
                          </div>
                          {data.part.vendor && (
                            <div className="data-pair">
                              <span className="data-label">Vendor</span>
                              <span className="data-value">{data.part.vendor}</span>
                            </div>
                          )}
                          <div className="data-pair">
                            <span className="data-label flex items-center gap-2">
                              <Calendar className="h-3.5 w-3.5" />
                              Warranty Until
                            </span>
                            <span className="data-value font-semibold">{formatDate(data.part.warranty_expiry_date)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Parent Device Info */}
                      {data.parent_device && (
                        <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                          <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Installed In Device</p>
                          <div className="flex items-center gap-3">
                            <Laptop className="h-5 w-5 text-slate-400" />
                            <div>
                              <p className="font-medium text-slate-900">{data.parent_device.brand} {data.parent_device.model}</p>
                              <p className="text-sm text-slate-500">SN: {data.parent_device.serial_number}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Warranty Status */}
                      <div className="mt-8 pt-6 border-t border-slate-200">
                        <div className="flex items-center gap-4">
                          {data.part.warranty_active ? (
                            <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                          ) : (
                            <XCircle className="h-8 w-8 text-slate-400" />
                          )}
                          <div>
                            <p className="text-lg font-semibold text-slate-900">
                              {data.part.warranty_active ? 'Part Under Warranty' : 'Part Warranty Expired'}
                            </p>
                            <p className="text-slate-500">
                              {data.part.warranty_months} months warranty • 
                              {data.part.warranty_active 
                                ? ` Valid until ${formatDate(data.part.warranty_expiry_date)}`
                                : ` Expired on ${formatDate(data.part.warranty_expiry_date)}`
                              }
                            </p>
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    /* Device Details - Original Code */
                    <>
                      <div className="grid sm:grid-cols-2 gap-6 mb-8">
                        <div className="space-y-4">
                          <div className="data-pair">
                            <span className="data-label">Serial Number</span>
                            <span className="data-value font-mono" data-testid="serial-number">{data.device.serial_number}</span>
                          </div>
                          {data.device.asset_tag && (
                            <div className="data-pair">
                              <span className="data-label">Asset Tag</span>
                              <span className="data-value font-mono">{data.device.asset_tag}</span>
                            </div>
                          )}
                          <div className="data-pair">
                            <span className="data-label">Purchase Date</span>
                            <span className="data-value">{formatDate(data.device.purchase_date)}</span>
                          </div>
                        </div>
                        <div className="space-y-4">
                          <div className="data-pair">
                            <span className="data-label flex items-center gap-2">
                              <Building2 className="h-3.5 w-3.5" />
                              Company
                            </span>
                            <span className="data-value">{data.company_name}</span>
                          </div>
                          {data.assigned_user && (
                            <div className="data-pair">
                              <span className="data-label flex items-center gap-2">
                                <User className="h-3.5 w-3.5" />
                                Assigned To
                              </span>
                              <span className="data-value">{data.assigned_user}</span>
                            </div>
                          )}
                          <div className="data-pair">
                            <span className="data-label flex items-center gap-2">
                              <Calendar className="h-3.5 w-3.5" />
                              Warranty Until
                            </span>
                        <span className="data-value">
                          {data.device.warranty_end_date ? formatDate(data.device.warranty_end_date) : 'Not specified'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Device Warranty Status */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {data.device.warranty_active ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-slate-400" />
                        )}
                        <span className="font-medium text-slate-900">Device Warranty</span>
                      </div>
                      <span className={data.device.warranty_active ? 'badge-active' : 'badge-expired'}>
                        {data.device.warranty_active ? 'Covered' : 'Not Covered'}
                      </span>
                    </div>
                    {!data.device.warranty_active && data.device.warranty_end_date && (
                      <p className="text-sm text-slate-500 mt-2 ml-8">
                        Warranty expired on {formatDate(data.device.warranty_end_date)}
                      </p>
                    )}
                  </div>

                  {/* Parts Warranty Section */}
                  {data.parts && data.parts.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">
                        Parts Warranty
                      </h3>
                      <div className="space-y-3" data-testid="parts-warranty-list">
                        {data.parts.map((part, index) => (
                          <div 
                            key={index} 
                            className="p-4 rounded-xl bg-slate-50 border border-slate-100"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-3">
                                {part.warranty_active ? (
                                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                ) : (
                                  <XCircle className="h-5 w-5 text-slate-400" />
                                )}
                                <span className="font-medium text-slate-900">{part.part_name}</span>
                              </div>
                              <span className={part.warranty_active ? 'badge-active' : 'badge-expired'}>
                                {part.warranty_active ? 'Covered' : 'Expired'}
                              </span>
                            </div>
                            <div className="ml-8 text-sm text-slate-500 space-y-1">
                              <p>Warranty: {part.warranty_months} Months</p>
                              <p>Expires: {formatDate(part.warranty_expiry_date)}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AMC Section - P0 Fix: Show AMC Contract with priority */}
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">
                      Service / AMC Coverage
                    </h3>
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100" data-testid="amc-status">
                      {/* Priority: AMC Contract > Legacy AMC > No Coverage */}
                      {data.amc_contract ? (
                        <>
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                              <span className="font-medium text-slate-900">{data.amc_contract.name || 'AMC Contract'}</span>
                            </div>
                            <span className="badge-active">
                              Active
                            </span>
                          </div>
                          <div className="ml-8 text-sm space-y-2">
                            <p className="text-slate-600">
                              <span className="text-slate-500">Coverage Type:</span>{' '}
                              <span className="font-medium capitalize">{data.amc_contract.amc_type || 'Standard'}</span>
                            </p>
                            <p className="text-slate-600">
                              <span className="text-slate-500">Valid Until:</span>{' '}
                              <span className="font-medium">{formatDate(data.amc_contract.coverage_end)}</span>
                            </p>
                            {data.coverage_source === 'amc_contract' && data.device?.device_warranty_active === false && (
                              <p className="text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded inline-block mt-2">
                                ✓ Device protected under AMC even after original warranty expired
                              </p>
                            )}
                          </div>
                        </>
                      ) : data.amc ? (
                        <>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              {data.amc.active ? (
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                              ) : (
                                <XCircle className="h-5 w-5 text-slate-400" />
                              )}
                              <span className="font-medium text-slate-900">Annual Maintenance Contract</span>
                            </div>
                            <span className={data.amc.active ? 'badge-active' : 'badge-expired'}>
                              {data.amc.active ? 'Active' : 'Expired'}
                            </span>
                          </div>
                          <div className="ml-8 text-sm text-slate-500 space-y-1">
                            <p>Valid: {formatDate(data.amc.start_date)} — {formatDate(data.amc.end_date)}</p>
                          </div>
                        </>
                      ) : (
                        <div className="flex items-center gap-3">
                          <XCircle className="h-5 w-5 text-slate-400" />
                          <span className="text-slate-500">No active AMC found for this device</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Download Button */}
                  <div className="pt-4 border-t border-slate-100">
                    <div className="flex flex-col sm:flex-row gap-3">
                      <Button 
                        onClick={handleDownloadPDF}
                        className="w-full sm:w-auto bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                        data-testid="download-pdf-btn"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Warranty Report (PDF)
                      </Button>
                      <a
                        href={`https://support.thegoodmen.in?source=warranty-portal&serial=${encodeURIComponent(data.device.serial_number)}&device_id=${encodeURIComponent(data.device.id || '')}&company=${encodeURIComponent(data.company_name || '')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full sm:w-auto"
                      >
                        <Button 
                          variant="outline"
                          className="w-full border-[#0F62FE] text-[#0F62FE] hover:bg-[#0F62FE]/5"
                          data-testid="request-support-btn"
                        >
                          <svg className="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
                          </svg>
                          Request Support
                        </Button>
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              {/* Disclaimer */}
              <p className="text-center text-sm text-slate-400">
                This report is auto-generated. For discrepancies, please contact support.
              </p>
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
};

export default WarrantyResult;
