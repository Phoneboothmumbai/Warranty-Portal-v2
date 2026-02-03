import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function StaticPage() {
  const { slug } = useParams();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPage();
  }, [slug]);

  const fetchPage = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/pages/${slug}`);
      setPage(response.data);
      setError(null);
    } catch (err) {
      setError('Page not found');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-3xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">Page Not Found</h1>
          <p className="text-slate-600 mb-8">The page you're looking for doesn't exist.</p>
          <Link to="/" className="text-blue-600 hover:text-blue-700 font-medium">
            ← Back to Home
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Header />
      
      <main className="flex-1 py-12">
        <div className="max-w-3xl mx-auto px-4">
          {/* Breadcrumb */}
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>

          {/* Page Title */}
          <h1 className="text-3xl font-bold text-slate-900 mb-8">{page.title}</h1>

          {/* Page Content */}
          <div 
            className="prose prose-slate max-w-none
              prose-headings:text-slate-900 prose-headings:font-semibold
              prose-h2:text-xl prose-h2:mt-8 prose-h2:mb-4
              prose-p:text-slate-600 prose-p:leading-relaxed
              prose-ul:text-slate-600
              prose-li:marker:text-slate-400
              prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
            "
            dangerouslySetInnerHTML={{ __html: page.content }}
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-900">Warranty Portal</span>
        </Link>
      </div>
    </header>
  );
}

function Footer() {
  const [pages, setPages] = useState([]);

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const response = await axios.get(`${API}/api/pages`);
      setPages(response.data);
    } catch (err) {
      console.log('Failed to fetch pages');
    }
  };

  return (
    <footer className="bg-slate-900 text-slate-400 py-12">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Logo & Description */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold text-white">Warranty Portal</span>
            </div>
            <p className="text-sm">
              Enterprise warranty and asset tracking solution for modern businesses.
            </p>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              {pages.map(p => (
                <li key={p.slug}>
                  <Link 
                    to={`/page/${p.slug}`}
                    className="hover:text-white transition-colors"
                  >
                    {p.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/signup" className="hover:text-white transition-colors">Get Started</Link></li>
              <li><Link to="/admin/login" className="hover:text-white transition-colors">MSP Login</Link></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-sm">
              <li>support@yourcompany.com</li>
              <li>+91 98765 43210</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 mt-8 pt-8 text-sm text-center">
          <p>© {new Date().getFullYear()} Warranty Portal. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
