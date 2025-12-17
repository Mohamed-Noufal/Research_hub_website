import {
    PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import type { ResearchPaper } from './types';

export default function AnalysisView({ papers }: { papers: ResearchPaper[] }) {
    const methodData = Object.entries(
        papers.reduce((acc, p) => {
            acc[p.methodology] = (acc[p.methodology] || 0) + 1;
            return acc;
        }, {} as Record<string, number>)
    ).map(([name, value]) => ({ name, value }));

    const yearData = Object.entries(
        papers.reduce((acc, p) => {
            acc[p.year] = (acc[p.year] || 0) + 1;
            return acc;
        }, {} as Record<string, number>)
    ).map(([year, count]) => ({ year, count })).sort((a, b) => parseInt(a.year) - parseInt(b.year));

    const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#10b981'];

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
                {/* Methodology Chart */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Methodology Distribution</h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                            <PieChart>
                                <Pie
                                    data={methodData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {methodData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Timeline Chart */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Publication Timeline</h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                            <BarChart data={yearData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis dataKey="year" />
                                <YAxis allowDecimals={false} />
                                <Tooltip />
                                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Quality Overview */}
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Assessment Overview</h3>
                <div className="grid grid-cols-4 gap-4">
                    <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                        <div className="text-sm text-green-800 font-medium">High Quality (5★)</div>
                        <div className="text-2xl font-bold text-green-900 mt-1">
                            {papers.filter(p => p.qualityScore === 5).length}
                        </div>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                        <div className="text-sm text-blue-800 font-medium">Good Quality (4★)</div>
                        <div className="text-2xl font-bold text-blue-900 mt-1">
                            {papers.filter(p => p.qualityScore === 4).length}
                        </div>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-100">
                        <div className="text-sm text-yellow-800 font-medium">Moderate (3★)</div>
                        <div className="text-2xl font-bold text-yellow-900 mt-1">
                            {papers.filter(p => p.qualityScore === 3).length}
                        </div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                        <div className="text-sm text-gray-800 font-medium">Avg Score</div>
                        <div className="text-2xl font-bold text-gray-900 mt-1">
                            {(papers.reduce((acc, p) => acc + p.qualityScore, 0) / papers.length).toFixed(1)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
