import { useState } from 'react';
import axios from 'axios';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * QuickCreateEmployee - Minimal form for inline company employee creation
 * 
 * Props:
 * - initialValue: Pre-fill the employee name from search query
 * - companyId: Required - which company this employee belongs to
 * - onSuccess: Callback with newly created employee {id, name, ...}
 * - onCancel: Callback to close the form
 * - token: Auth token
 */
export const QuickCreateEmployee = ({ initialValue = "", companyId, onSuccess, onCancel, token }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: initialValue,
    email: "",
    department: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name) {
      toast.error("Name is required");
      return;
    }
    
    if (!companyId) {
      toast.error("Please select a company first");
      return;
    }

    setLoading(true);
    try {
      const submitData = new FormData();
      submitData.append('company_id', companyId);
      submitData.append('name', formData.name);
      if (formData.email) submitData.append('email', formData.email);
      if (formData.department) submitData.append('department', formData.department);
      
      const response = await axios.post(
        `${API}/admin/company-employees/quick-create`,
        submitData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Employee added");
      onSuccess?.(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add employee");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="employee-name">Full Name *</Label>
        <Input
          id="employee-name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="John Doe"
          autoFocus
        />
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="employee-email">Email (Optional)</Label>
          <Input
            id="employee-email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="john@company.com"
          />
        </div>
        <div>
          <Label htmlFor="employee-department">Department</Label>
          <Input
            id="employee-department"
            value={formData.department}
            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            placeholder="IT, Finance, HR..."
          />
        </div>
      </div>
      
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading} className="bg-[#0F62FE] hover:bg-[#0043CE]">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Adding...
            </>
          ) : (
            "Add Employee"
          )}
        </Button>
      </div>
    </form>
  );
};

export default QuickCreateEmployee;
