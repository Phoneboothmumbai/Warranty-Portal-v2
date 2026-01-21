import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./context/AuthContext";
import { SettingsProvider } from "./context/SettingsContext";
import { CompanyAuthProvider } from "./context/CompanyAuthContext";
import { EngineerAuthProvider } from "./context/EngineerAuthContext";

// Public Pages
import LandingPage from "./pages/public/LandingPage";
import WarrantyResult from "./pages/public/WarrantyResult";
import PublicDevicePage from "./pages/public/PublicDevicePage";

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

// Company Portal Pages
import CompanyLayout from "./layouts/CompanyLayout";
import CompanyLogin from "./pages/company/CompanyLogin";
import CompanyRegister from "./pages/company/CompanyRegister";
import CompanyDashboard from "./pages/company/CompanyDashboard";
import CompanyDevices from "./pages/company/CompanyDevices";
import CompanyDeviceDetails from "./pages/company/CompanyDeviceDetails";
import CompanyTickets from "./pages/company/CompanyTickets";
import CompanyTicketDetails from "./pages/company/CompanyTicketDetails";
import CompanyAMC from "./pages/company/CompanyAMC";
import CompanyDeployments from "./pages/company/CompanyDeployments";
import CompanyUsers from "./pages/company/CompanyUsers";
import CompanySites from "./pages/company/CompanySites";
import CompanyProfile from "./pages/company/CompanyProfile";
import CompanyWarranty from "./pages/company/CompanyWarranty";
import CompanyOfficeSupplies from "./pages/company/CompanyOfficeSupplies";

// Engineer Portal Pages
import EngineerLogin from "./pages/engineer/EngineerLogin";
import EngineerDashboard from "./pages/engineer/EngineerDashboard";
import EngineerVisitDetail from "./pages/engineer/EngineerVisitDetail";

function App() {
  return (
    <SettingsProvider>
      <AuthProvider>
        <CompanyAuthProvider>
          <EngineerAuthProvider>
            <BrowserRouter>
              <div className="noise-bg min-h-screen">
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/warranty/:serialNumber" element={<WarrantyResult />} />
                  <Route path="/device/:identifier" element={<PublicDevicePage />} />
                  
                  {/* Admin Routes */}
                  <Route path="/admin/login" element={<AdminLogin />} />
                  <Route path="/admin/setup" element={<AdminSetup />} />
                  
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
                    <Route path="parts" element={<Parts />} />
                    <Route path="amc" element={<AMCManagement />} />
                    <Route path="amc-contracts" element={<AMCContracts />} />
                    <Route path="sites" element={<Sites />} />
                    <Route path="deployments" element={<Deployments />} />
                    <Route path="licenses" element={<Licenses />} />
                    <Route path="service-history" element={<ServiceHistory />} />
                    <Route path="supply-products" element={<SupplyProducts />} />
                    <Route path="supply-orders" element={<SupplyOrders />} />
                    <Route path="master-data" element={<MasterData />} />
                    <Route path="settings" element={<Settings />} />
                  </Route>

                  {/* Company Portal Routes */}
                  <Route path="/company/login" element={<CompanyLogin />} />
                  <Route path="/company/register" element={<CompanyRegister />} />
                  
                  {/* Protected Company Routes */}
                  <Route path="/company" element={<CompanyLayout />}>
                    <Route index element={<Navigate to="/company/dashboard" replace />} />
                    <Route path="dashboard" element={<CompanyDashboard />} />
                    <Route path="devices" element={<CompanyDevices />} />
                    <Route path="devices/:deviceId" element={<CompanyDeviceDetails />} />
                    <Route path="warranty" element={<CompanyWarranty />} />
                    <Route path="amc" element={<CompanyAMC />} />
                    <Route path="tickets" element={<CompanyTickets />} />
                    <Route path="tickets/:ticketId" element={<CompanyTicketDetails />} />
                    <Route path="deployments" element={<CompanyDeployments />} />
                    <Route path="users" element={<CompanyUsers />} />
                    <Route path="sites" element={<CompanySites />} />
                    <Route path="office-supplies" element={<CompanyOfficeSupplies />} />
                    <Route path="profile" element={<CompanyProfile />} />
                  </Route>

                  {/* Engineer Portal Routes */}
                  <Route path="/engineer" element={<EngineerLogin />} />
                  <Route path="/engineer/dashboard" element={<EngineerDashboard />} />
                  <Route path="/engineer/visit/:visitId" element={<EngineerVisitDetail />} />
                </Routes>
              </div>
              <Toaster position="top-right" richColors />
            </BrowserRouter>
          </EngineerAuthProvider>
        </CompanyAuthProvider>
      </AuthProvider>
    </SettingsProvider>
  );
}

export default App;
