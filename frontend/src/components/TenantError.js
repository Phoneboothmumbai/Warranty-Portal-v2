import { AlertTriangle, Building2, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';

export function TenantSuspended({ tenantName }) {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-500/20 mb-6">
          <AlertTriangle className="w-8 h-8 text-amber-500" />
        </div>
        
        <h1 className="text-2xl font-bold text-white mb-2">
          Workspace Suspended
        </h1>
        
        <p className="text-slate-400 mb-6">
          {tenantName ? (
            <>The workspace <span className="text-white font-medium">{tenantName}</span> has been suspended.</>
          ) : (
            'This workspace has been suspended.'
          )}
        </p>
        
        <p className="text-slate-500 text-sm mb-8">
          Please contact your administrator or support team for assistance.
        </p>
        
        <Button
          onClick={() => window.location.href = '/'}
          variant="outline"
          className="border-slate-600 text-slate-300 hover:bg-slate-800"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Button>
      </div>
    </div>
  );
}

export function TenantNotFound({ slug }) {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-700 mb-6">
          <Building2 className="w-8 h-8 text-slate-400" />
        </div>
        
        <h1 className="text-2xl font-bold text-white mb-2">
          Workspace Not Found
        </h1>
        
        <p className="text-slate-400 mb-6">
          {slug ? (
            <>The workspace <span className="font-mono text-white bg-slate-700 px-2 py-0.5 rounded">{slug}</span> does not exist.</>
          ) : (
            'This workspace does not exist or has been removed.'
          )}
        </p>
        
        <p className="text-slate-500 text-sm mb-8">
          Please check the URL and try again, or contact the workspace administrator.
        </p>
        
        <div className="flex gap-3 justify-center">
          <Button
            onClick={() => window.location.href = '/'}
            variant="outline"
            className="border-slate-600 text-slate-300 hover:bg-slate-800"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <Button
            onClick={() => window.location.href = '/signup'}
            className="bg-purple-600 hover:bg-purple-700"
          >
            Create Workspace
          </Button>
        </div>
      </div>
    </div>
  );
}

export function TenantLoading() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500 mx-auto mb-4"></div>
        <p className="text-slate-400">Loading workspace...</p>
      </div>
    </div>
  );
}

export default function TenantError({ error, tenantName, slug }) {
  if (!error) return null;
  
  switch (error.type) {
    case 'suspended':
      return <TenantSuspended tenantName={tenantName} />;
    case 'not_found':
      return <TenantNotFound slug={slug} />;
    default:
      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/20 mb-6">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>
            <p className="text-slate-400 mb-6">{error.message}</p>
            <Button
              onClick={() => window.location.reload()}
              className="bg-purple-600 hover:bg-purple-700"
            >
              Try Again
            </Button>
          </div>
        </div>
      );
  }
}
