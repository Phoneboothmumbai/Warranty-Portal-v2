import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./context/AuthContext";
import { SettingsProvider } from "./context/SettingsContext";
import { CompanyAuthProvider } from "./context/CompanyAuthContext";
import { EngineerAuthProvider } from "./context/EngineerAuthContext";
import { TenantProvider } from "./context/TenantContext";

// Public Pages
import LandingPage from "./pages/public/LandingPage";
import FeaturesPage from "./pages/public/FeaturesPage";
import PricingPage from "./pages/public/PricingPage";
import AboutPage from "./pages/public/AboutPage";
import WarrantyResult from "./pages/public/WarrantyResult";
import PublicDevicePage from "./pages/public/PublicDevicePage";
import PublicSupportPortal from "./pages/public/PublicSupportPortal";

// Admin Pages
import AdminLogin from "./pages/admin/AdminLogin";
import AdminSetup from "./pages/admin/AdminSetup";
import AdminLayout from "./layouts/AdminLayout";
import Dashboard from "./pages/admin/Dashboard";
import Companies from "./pages/admin/Companies";
import CompanyDetails from "./pages/admin/CompanyDetails";
import Users from "./pages/admin/Users";
import Devices from "./pages/admin/Devices";
import Parts from "./pages/admin/Parts";
import AMCManagement from "./pages/admin/AMCManagement";
import Settings from "./pages/admin/Settings";
import MasterData from "./pages/admin/MasterData";
import ServiceHistory from "./pages/admin/ServiceHistory";
import AMCContracts from "./pages/admin/AMCContracts";
import Sites from "./pages/admin/Sites";
import Deployments from "./pages/admin/Deployments";
import Licenses from "./pages/admin/Licenses";
import SupplyProducts from "./pages/admin/SupplyProducts";
import SupplyOrders from "./pages/admin/SupplyOrders";
import Employees from "./pages/admin/Employees";
import EmployeeDetails from "./pages/admin/EmployeeDetails";
import AdminDeviceDetails from "./pages/admin/AdminDeviceDetails";
import Subscriptions from "./pages/admin/Subscriptions";
import Accessories from "./pages/admin/Accessories";
import AssetGroups from "./pages/admin/AssetGroups";
import RenewalAlerts from "./pages/admin/RenewalAlerts";
import InternetServices from "./pages/admin/InternetServices";
import Credentials from "./pages/admin/Credentials";
import DeviceModelCatalog from "./pages/admin/DeviceModelCatalog";
import AdminAMCRequests from "./pages/admin/AdminAMCRequests";
import AdminAMCRequestDetail from "./pages/admin/AdminAMCRequestDetail";
import OrganizationSettings from "./pages/admin/OrganizationSettings";
import WatchTowerIntegration from "./pages/admin/WatchTowerIntegration";
import MoltBotIntegration from "./pages/admin/MoltBotIntegration";
import KnowledgeBase from "./pages/admin/KnowledgeBase";
import TeamMembers from "./pages/admin/TeamMembers";
import StaffManagement from "./pages/admin/StaffManagement";
import CustomDomains from "./pages/admin/CustomDomains";
import EmailWhitelabel from "./pages/admin/EmailWhitelabel";
import ServiceRequests from "./pages/admin/ServiceRequestsV2";
import ServiceTicketDetail from "./pages/admin/ServiceTicketDetailV2";
import TicketingConfig from "./pages/admin/TicketingConfigV2";
import TGMSIntegration from "./pages/admin/TGMSIntegration";

// Platform Super Admin Pages
import PlatformLogin from "./pages/platform/PlatformLogin";
import PlatformLayout from "./layouts/PlatformLayout";
import PlatformDashboard from "./pages/platform/PlatformDashboard";
import PlatformOrganizations from "./pages/platform/PlatformOrganizations";
import PlatformAdmins from "./pages/platform/PlatformAdmins";
import PlatformSettings from "./pages/platform/PlatformSettings";
import PlatformBilling from "./pages/platform/PlatformBilling";
import PlatformAuditLogs from "./pages/platform/PlatformAuditLogs";
import PlatformPlans from "./pages/platform/PlatformPlans";

// Signup Page
import SignupPage from "./pages/SignupPage";

// Static Pages
import StaticPage from "./pages/StaticPage";
import StaticPages from "./pages/admin/StaticPages";
import UsageDashboard from "./pages/admin/UsageDashboard";
import CompanyDomains from "./pages/admin/CompanyDomains";

// Company Portal Pages
import CompanyLayout from "./layouts/CompanyLayout";
import CompanyLogin from "./pages/company/CompanyLogin";
import CompanyRegister from "./pages/company/CompanyRegister";
import CompanyDashboard from "./pages/company/CompanyDashboard";
import CompanyDevices from "./pages/company/CompanyDevices";
import CompanyDeviceDetails from "./pages/company/CompanyDeviceDetails";
import DeviceDashboard from "./pages/company/DeviceDashboard";
import CompanyAMC from "./pages/company/CompanyAMC";
import CompanyDeployments from "./pages/company/CompanyDeployments";
import CompanyUsers from "./pages/company/CompanyUsers";
import CompanySites from "./pages/company/CompanySites";
import CompanyProfile from "./pages/company/CompanyProfile";
import CompanyWarranty from "./pages/company/CompanyWarranty";
import CompanyQuotations from "./pages/company/CompanyQuotations";
import CompanyTickets from "./pages/company/CompanyTicketsV2";
import CompanyTicketDetail from "./pages/company/CompanyTicketDetailV2";
import CompanyOfficeSupplies from "./pages/company/CompanyOfficeSupplies";
import CompanyCredentials from "./pages/company/CompanyCredentials";
import CompanyAMCRequests from "./pages/company/CompanyAMCRequests";
import NewAMCRequest from "./pages/company/NewAMCRequest";
import CompanyAMCOnboarding from "./pages/company/CompanyAMCOnboarding";

// Engineer Portal - Login only (V2 uses task-based system)
import EngineerLogin from "./pages/engineer/EngineerLogin";

// Contexts
import { BrandingProvider } from "./contexts/BrandingContext";

function App() {
  return (
    <SettingsProvider>
      <TenantProvider>
        <AuthProvider>
          <BrandingProvider>
            <CompanyAuthProvider>
              <EngineerAuthProvider>
                <BrowserRouter>
                  <div className="noise-bg min-h-screen">
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/features" element={<FeaturesPage />} />
                  <Route path="/pricing" element={<PricingPage />} />
                  <Route path="/about" element={<AboutPage />} />
                  <Route path="/signup" element={<SignupPage />} />
                  <Route path="/page/:slug" element={<StaticPage />} />
                  <Route path="/warranty/:serialNumber" element={<WarrantyResult />} />
                  <Route path="/device/:identifier" element={<PublicDevicePage />} />
                  <Route path="/support" element={<PublicSupportPortal />} />
                  
                  {/* Admin Routes */}
                  <Route path="/admin/login" element={<AdminLogin />} />
                  <Route path="/admin/setup" element={<AdminSetup />} />
                  
                  {/* Platform Super Admin Routes */}
                  <Route path="/platform/login" element={<PlatformLogin />} />
                  <Route path="/platform" element={<PlatformLayout />}>
                    <Route index element={<PlatformDashboard />} />
                    <Route path="dashboard" element={<PlatformDashboard />} />
                    <Route path="organizations" element={<PlatformOrganizations />} />
                    <Route path="admins" element={<PlatformAdmins />} />
                    <Route path="plans" element={<PlatformPlans />} />
                    <Route path="settings" element={<PlatformSettings />} />
                    <Route path="billing" element={<PlatformBilling />} />
                    <Route path="audit-logs" element={<PlatformAuditLogs />} />
                  </Route>
                  
                  {/* Protected Admin Routes */}
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="companies" element={<Companies />} />
                    <Route path="companies/:companyId" element={<CompanyDetails />} />
                    <Route path="users" element={<Users />} />
                    <Route path="employees" element={<Employees />} />
                    <Route path="employees/:employeeId" element={<EmployeeDetails />} />
                    <Route path="subscriptions" element={<Subscriptions />} />
                    <Route path="devices" element={<Devices />} />
                    <Route path="devices/:deviceId" element={<AdminDeviceDetails />} />
                    <Route path="accessories" element={<Accessories />} />
                    <Route path="asset-groups" element={<AssetGroups />} />
                    <Route path="renewal-alerts" element={<RenewalAlerts />} />
                    <Route path="device-catalog" element={<DeviceModelCatalog />} />
                    <Route path="parts" element={<Parts />} />
                    <Route path="amc" element={<AMCManagement />} />
                    <Route path="amc-contracts" element={<AMCContracts />} />
                    <Route path="amc-requests" element={<AdminAMCRequests />} />
                    <Route path="amc-requests/:requestId" element={<AdminAMCRequestDetail />} />
                    <Route path="service-requests" element={<ServiceRequests />} />
                    <Route path="service-requests/:ticketId" element={<ServiceTicketDetail />} />
                    <Route path="quotations" element={<Quotations />} />
                    <Route path="sites" element={<Sites />} />
                    <Route path="deployments" element={<Deployments />} />
                    <Route path="licenses" element={<Licenses />} />
                    <Route path="service-history" element={<ServiceHistory />} />
                    <Route path="internet-services" element={<InternetServices />} />
                    <Route path="credentials" element={<Credentials />} />
                    <Route path="supply-products" element={<SupplyProducts />} />
                    <Route path="supply-orders" element={<SupplyOrders />} />
                    <Route path="master-data" element={<MasterData />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="organization" element={<OrganizationSettings />} />
                    <Route path="static-pages" element={<StaticPages />} />
                    <Route path="usage" element={<UsageDashboard />} />
                    <Route path="company-domains" element={<CompanyDomains />} />
                    <Route path="integrations/watchtower" element={<WatchTowerIntegration />} />
                    <Route path="integrations/moltbot" element={<MoltBotIntegration />} />
                    <Route path="integrations/tgms" element={<TGMSIntegration />} />
                    <Route path="knowledge-base" element={<KnowledgeBase />} />
                    <Route path="team" element={<TeamMembers />} />
                    <Route path="staff" element={<StaffManagement />} />
                    <Route path="custom-domains" element={<CustomDomains />} />
                    <Route path="email-whitelabel" element={<EmailWhitelabel />} />
                    <Route path="ticketing-config" element={<TicketingConfig />} />
                    <Route path="ticket-types" element={<TicketTypesManagement />} />
                  </Route>

                  {/* Company Portal Routes */}
                  <Route path="/company/login" element={<CompanyLogin />} />
                  <Route path="/company/register" element={<CompanyRegister />} />
                  
                  {/* Protected Company Routes */}
                  <Route path="/company" element={<CompanyLayout />}>
                    <Route index element={<Navigate to="/company/dashboard" replace />} />
                    <Route path="dashboard" element={<CompanyDashboard />} />
                    <Route path="devices" element={<CompanyDevices />} />
                    <Route path="devices/:deviceId" element={<DeviceDashboard />} />
                    <Route path="credentials" element={<CompanyCredentials />} />
                    <Route path="warranty" element={<CompanyWarranty />} />
                    <Route path="quotations" element={<CompanyQuotations />} />
                    <Route path="tickets" element={<CompanyTickets />} />
                    <Route path="tickets/:ticketId" element={<CompanyTicketDetail />} />
                    <Route path="amc" element={<CompanyAMC />} />
                    <Route path="amc-onboarding" element={<CompanyAMCOnboarding />} />
                    <Route path="amc-requests" element={<CompanyAMCRequests />} />
                    <Route path="amc-requests/new" element={<NewAMCRequest />} />
                    <Route path="amc-requests/:requestId" element={<CompanyAMCRequests />} />
                    <Route path="deployments" element={<CompanyDeployments />} />
                    <Route path="users" element={<CompanyUsers />} />
                    <Route path="sites" element={<CompanySites />} />
                    <Route path="office-supplies" element={<CompanyOfficeSupplies />} />
                    <Route path="profile" element={<CompanyProfile />} />
                  </Route>

                  {/* Engineer/Technician Portal Routes */}
                  <Route path="/engineer" element={<EngineerLogin />} />
                  <Route path="/engineer/dashboard" element={<TechnicianDashboard />} />
                  <Route path="/engineer/ticket/:ticketId" element={<EngineerTicketDetail />} />
                  <Route path="/engineer/visit/:visitId" element={<TechnicianVisitDetail />} />
                </Routes>
              </div>
              <Toaster position="top-right" richColors />
            </BrowserRouter>
          </EngineerAuthProvider>
        </CompanyAuthProvider>
      </BrandingProvider>
    </AuthProvider>
  </TenantProvider>
  </SettingsProvider>
);
}

export default App;
