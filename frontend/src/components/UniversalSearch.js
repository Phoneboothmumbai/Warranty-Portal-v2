import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { 
  Search, X, Building2, MapPin, User, Laptop, Package, 
  FileText, Wrench, Loader2, Command
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ICONS = {
  building: Building2,
  'map-pin': MapPin,
  user: User,
  laptop: Laptop,
  package: Package,
  'file-text': FileText,
  wrench: Wrench,
};

const CATEGORY_LABELS = {
  companies: 'Companies',
  sites: 'Sites',
  users: 'Users',
  assets: 'Assets',
  deployments: 'Deployments',
  amcs: 'AMC Contracts',
  services: 'Service History',
};

const CATEGORY_COLORS = {
  companies: 'bg-blue-50 text-blue-600',
  sites: 'bg-emerald-50 text-emerald-600',
  users: 'bg-purple-50 text-purple-600',
  assets: 'bg-amber-50 text-amber-600',
  deployments: 'bg-cyan-50 text-cyan-600',
  amcs: 'bg-rose-50 text-rose-600',
  services: 'bg-slate-100 text-slate-600',
};

const UniversalSearch = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const containerRef = useRef(null);
  const debounceRef = useRef(null);

  // Flatten results for keyboard navigation
  const flatResults = results ? [
    ...results.companies,
    ...results.sites,
    ...results.users,
    ...results.assets,
    ...results.deployments,
    ...results.amcs,
    ...results.services,
  ] : [];

  // Keyboard shortcut to open search
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K or Cmd+K to open
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      // / to open (when not typing)
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
        e.preventDefault();
        setIsOpen(true);
      }
      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setQuery('');
        setResults(null);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Focus input when opening
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Debounced search
  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 1) {
      setResults(null);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${API}/search`, {
        params: { q: searchQuery, limit: 5 },
        headers: { Authorization: `Bearer ${token}` }
      });
      setResults(response.data);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Search error:', error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Handle query change with debounce
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.length >= 1) {
      debounceRef.current = setTimeout(() => {
        performSearch(query);
      }, 300);
    } else {
      setResults(null);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, performSearch]);

  // Handle result click
  const handleResultClick = (result) => {
    navigate(result.link);
    setIsOpen(false);
    setQuery('');
    setResults(null);
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!results || flatResults.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev < flatResults.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : flatResults.length - 1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      handleResultClick(flatResults[selectedIndex]);
    }
  };

  // Highlight matching text
  const highlightMatch = (text, query) => {
    if (!text || !query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() 
        ? <mark key={i} className="bg-yellow-200 px-0.5 rounded">{part}</mark>
        : part
    );
  };

  const hasResults = results && results.total_count > 0;

  return (
    <>
      {/* Search Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-500 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
        data-testid="universal-search-trigger"
      >
        <Search className="h-4 w-4" />
        <span className="hidden sm:inline">Search...</span>
        <kbd className="hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 text-xs bg-white rounded border border-slate-200">
          <Command className="h-3 w-3" />
          <span>K</span>
        </kbd>
      </button>

      {/* Search Modal Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-[10vh]">
          <div 
            ref={containerRef}
            className="w-full max-w-2xl bg-white rounded-xl shadow-2xl overflow-hidden mx-4"
            data-testid="universal-search-modal"
          >
            {/* Search Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200">
              {loading ? (
                <Loader2 className="h-5 w-5 text-slate-400 animate-spin" />
              ) : (
                <Search className="h-5 w-5 text-slate-400" />
              )}
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search companies, assets, sites, AMC..."
                className="flex-1 text-lg outline-none placeholder-slate-400"
                data-testid="universal-search-input"
              />
              {query && (
                <button 
                  onClick={() => { setQuery(''); setResults(null); }}
                  className="p-1 hover:bg-slate-100 rounded"
                >
                  <X className="h-4 w-4 text-slate-400" />
                </button>
              )}
              <button 
                onClick={() => setIsOpen(false)}
                className="text-xs text-slate-400 px-2 py-1 bg-slate-100 rounded"
              >
                ESC
              </button>
            </div>

            {/* Results */}
            <div className="max-h-[60vh] overflow-y-auto">
              {loading && !results && (
                <div className="p-8 text-center text-slate-500">
                  <Loader2 className="h-6 w-6 mx-auto mb-2 animate-spin" />
                  <p>Searching...</p>
                </div>
              )}

              {!loading && query && !hasResults && (
                <div className="p-8 text-center text-slate-500">
                  <Search className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  <p>No results found for &quot;{query}&quot;</p>
                  <p className="text-sm text-slate-400 mt-1">Try a different keyword</p>
                </div>
              )}

              {hasResults && (
                <div className="py-2">
                  {Object.entries(CATEGORY_LABELS).map(([key, label]) => {
                    const items = results[key];
                    if (!items || items.length === 0) return null;

                    return (
                      <div key={key} className="mb-2">
                        <div className="px-4 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wide bg-slate-50">
                          {label} ({items.length})
                        </div>
                        {items.map((item, idx) => {
                          const Icon = ICONS[item.icon] || Search;
                          const globalIdx = flatResults.findIndex(r => r.id === item.id && r.type === item.type);
                          const isSelected = globalIdx === selectedIndex;

                          return (
                            <button
                              key={`${item.type}-${item.id}`}
                              onClick={() => handleResultClick(item)}
                              className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 transition-colors ${
                                isSelected ? 'bg-blue-50' : ''
                              }`}
                              data-testid={`search-result-${item.type}-${item.id}`}
                            >
                              <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${CATEGORY_COLORS[key]}`}>
                                <Icon className="h-4 w-4" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-slate-900 truncate">
                                  {highlightMatch(item.title, query)}
                                </p>
                                <p className="text-xs text-slate-500 truncate">
                                  {highlightMatch(item.subtitle, query)}
                                </p>
                              </div>
                              {item.status && (
                                <span className={`text-xs px-2 py-0.5 rounded-full ${
                                  item.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'
                                }`}>
                                  {item.status}
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Empty state when no query */}
              {!query && (
                <div className="p-6">
                  <p className="text-sm text-slate-500 mb-4">Quick search tips:</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Building2 className="h-4 w-4 text-blue-500" />
                      <span>Company names</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <Laptop className="h-4 w-4 text-amber-500" />
                      <span>Serial numbers</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <MapPin className="h-4 w-4 text-emerald-500" />
                      <span>Site / location</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <User className="h-4 w-4 text-purple-500" />
                      <span>Phone / email</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <FileText className="h-4 w-4 text-rose-500" />
                      <span>AMC contracts</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <Package className="h-4 w-4 text-cyan-500" />
                      <span>Deployments</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            {hasResults && (
              <div className="px-4 py-2 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
                <span>{results.total_count} results found</span>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-white rounded border">↑↓</kbd>
                    Navigate
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-white rounded border">↵</kbd>
                    Open
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default UniversalSearch;
