import React from 'react';
import { Download } from 'lucide-react';

interface SearchStatsProps {
    filteredCount: number;
    searchQuery: string;
}

export const SearchStats: React.FC<SearchStatsProps> = ({
    filteredCount,
    searchQuery,
}) => {
    return (
        <div className="mb-6 backdrop-blur-md bg-white/60 rounded-xl border border-white/30 p-4 shadow-sm">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-blue-900 bg-clip-text text-transparent mb-1">
                        {filteredCount} Research Papers Found
                    </h2>
                    <p className="text-sm text-gray-600">for "{searchQuery}"</p>
                </div>
                <div className="flex gap-2">
                    <button className="px-3 py-2 backdrop-blur-sm bg-white/60 rounded-lg text-xs font-medium text-gray-700 hover:bg-white transition-all">
                        <Download className="w-4 h-4 inline mr-1" />
                        Export
                    </button>
                </div>
            </div>
        </div>
    );
};
