import { useState, useEffect } from 'react';
import { Clock, Search, Trash2, History } from 'lucide-react';
import { papersApi } from '../../api/papers';

interface HistoryPanelProps {
  onSearch: (query: string, category?: string) => void;
}

export default function HistoryPanel({ onSearch }: HistoryPanelProps) {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await papersApi.getSearchHistory();
      // Backend returns { history: [], total: number }
      if (data && Array.isArray(data.history)) {
        setHistory(data.history);
      } else if (Array.isArray(data)) {
        // Fallback if API changes to return direct array
        setHistory(data);
      } else {
        console.error('Unexpected history data format:', data);
        setHistory([]);
      }
    } catch (error) {
      console.error('Failed to load history:', error);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = (item: any) => {
    onSearch(item.query, item.category);
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await papersApi.deleteSearchEntry(id);
      setHistory(prev => prev.filter(h => h.id !== id));
    } catch (error) {
      console.error('Failed to delete entry:', error);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear your search history?')) return;
    try {
      await papersApi.clearSearchHistory();
      setHistory([]);
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading history...</div>;

  if (history.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <History className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>No search history yet</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 h-full flex flex-col">
      <div className="flex justify-between items-center mb-2 shrink-0">
        <h3 className="text-sm font-semibold text-gray-700">Recent Searches</h3>
        <button
          onClick={handleClearAll}
          className="text-xs text-red-600 hover:text-red-700 hover:underline"
        >
          Clear All
        </button>
      </div>
      <div className="space-y-2 flex-1 overflow-y-auto">
        {history.map((item) => (
          <div
            key={item.id}
            onClick={() => handleRestore(item)}
            className="group p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all cursor-pointer relative"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Search className="w-3 h-3 text-blue-500" />
                  <span className="font-medium text-gray-900">{item.query}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600">
                    {item.category}
                  </span>
                  <span>•</span>
                  <span>{item.results_count} results</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(item.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-all"
                title="Delete from history"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

