import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./context/AuthContext";
import { SettingsProvider } from "./context/SettingsContext";

// Public Pages
import LandingPage from "./pages/public/LandingPage";
import WarrantyResult from "./pages/public/WarrantyResult";

// Admin Pages
import AdminLogin from "./pages/admin/AdminLogin";
import AdminSetup from "./pages/admin/AdminSetup";
import AdminLayout from "./layouts/AdminLayout";
import Dashboard from "./pages/admin/Dashboard";
import Companies from "./pages/admin/Companies";
import Users from "./pages/admin/Users";
import Devices from "./pages/admin/Devices";
import Parts from "./pages/admin/Parts";
import AMCManagement from "./pages/admin/AMCManagement";
import Settings from "./pages/admin/Settings";
import MasterData from "./pages/admin/MasterData";

function App() {
  return (
    <SettingsProvider>
      <AuthProvider>
        <BrowserRouter>
          <div className="noise-bg min-h-screen">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/warranty/:serialNumber" element={<WarrantyResult />} />
              
              {/* Admin Routes */}
              <Route path="/admin/login" element={<AdminLogin />} />
              <Route path="/admin/setup" element={<AdminSetup />} />
              
              {/* Protected Admin Routes */}
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="companies" element={<Companies />} />
                <Route path="users" element={<Users />} />
                <Route path="devices" element={<Devices />} />
                <Route path="parts" element={<Parts />} />
                <Route path="amc" element={<AMCManagement />} />
                <Route path="master-data" element={<MasterData />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </div>
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </SettingsProvider>
  );
}

export default App;
