import { useState, useEffect } from 'react';
import { Clipboard, Trash2, RefreshCw, Save, Download, Link2 } from 'lucide-react';

type ParaphraseMode = 'academic' | 'casual' | 'creative' | 'simple';

interface QualityMetrics {
    uniqueness: number;
    readability: number;
    naturalFlow: number;
    aiDetection: number;
}

interface ParaphraseVersion {
    id: number;
    mode: ParaphraseMode;
    text: string;
    quality: number;
}

interface AIParaphraserProps {
    initialText?: string;
}

export default function AIParaphraser({ initialText }: AIParaphraserProps) {
    const [originalText, setOriginalText] = useState(initialText || '');

    useEffect(() => {
        if (initialText) {
            setOriginalText(initialText);
        }
    }, [initialText]);

    const [paraphrasedText, setParaphrasedText] = useState('');
    const [selectedMode, setSelectedMode] = useState<ParaphraseMode>('academic');
    const [isParaphrasing, setIsParaphrasing] = useState(false);
    const [metrics, setMetrics] = useState<QualityMetrics | null>(null);
    const [versions, setVersions] = useState<ParaphraseVersion[]>([]);
    const [improvements, setImprovements] = useState<string[]>([]);

    const modes = [
        { id: 'academic' as ParaphraseMode, icon: '📚', label: 'Academic', desc: 'Formal, scholarly tone' },
        { id: 'casual' as ParaphraseMode, icon: '💬', label: 'Casual', desc: 'Natural, conversational' },
        { id: 'creative' as ParaphraseMode, icon: '🎨', label: 'Creative', desc: 'Unique phrasing' },
        { id: 'simple' as ParaphraseMode, icon: '📖', label: 'Simple', desc: 'Easy to understand' },
    ];

    // Mock paraphrasing logic
    const paraphraseText = async (text: string, mode: ParaphraseMode): Promise<string> => {
        await new Promise(resolve => setTimeout(resolve, 1500));

        const templates: Record<ParaphraseMode, (text: string) => string> = {
            academic: (t) => t
                .replace(/demonstrates/gi, 'illustrates')
                .replace(/efficacy/gi, 'effectiveness')
                .replace(/The research/gi, 'This study')
                .replace(/novel/gi, 'innovative'),
            casual: (t) => t
                .replace(/demonstrates/gi, 'shows')
                .replace(/efficacy/gi, 'how well it works')
                .replace(/The research/gi, 'Our study')
                .replace(/novel/gi, 'new'),
            creative: (t) => t
                .replace(/demonstrates/gi, 'reveals')
                .replace(/efficacy/gi, 'power')
                .replace(/The research/gi, 'Our investigation')
                .replace(/novel/gi, 'groundbreaking'),
            simple: (t) => t
                .replace(/demonstrates/gi, 'shows')
                .replace(/efficacy/gi, 'effectiveness')
                .replace(/The research/gi, 'The study')
                .replace(/novel/gi, 'new'),
        };

        return templates[mode](text) + ' [Paraphrased in ' + mode + ' mode]';
    };

    const calculateMetrics = (): QualityMetrics => {
        return {
            uniqueness: 75 + Math.random() * 20,
            readability: 65 + Math.random() * 25,
            naturalFlow: 80 + Math.random() * 15,
            aiDetection: 20 + Math.random() * 15,
        };
    };

    const handleParaphrase = async () => {
        if (!originalText.trim()) return;

        setIsParaphrasing(true);
        const result = await paraphraseText(originalText, selectedMode);
        setParaphrasedText(result);

        const newMetrics = calculateMetrics();
        setMetrics(newMetrics);

        setImprovements([
            'Added personal pronouns ("our", "we")',
            'Varied sentence structure (3 patterns)',
            'Improved word choice',
            'Enhanced readability (Flesch: 62 → 78)',
            'Reduced AI patterns (73% → 28%)',
        ]);

        // Add to version history
        const newVersion: ParaphraseVersion = {
            id: versions.length + 1,
            mode: selectedMode,
            text: result,
            quality: Math.round((newMetrics.uniqueness + newMetrics.readability + newMetrics.naturalFlow) / 3),
        };
        setVersions([newVersion, ...versions].slice(0, 5));

        setIsParaphrasing(false);
    };

    const handlePaste = async () => {
        try {
            const text = await navigator.clipboard.readText();
            setOriginalText(text);
        } catch (error) {
            console.error('Failed to read clipboard:', error);
        }
    };

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(paraphrasedText);
        } catch (error) {
            console.error('Failed to copy:', error);
        }
    };

    const handleClear = () => {
        setOriginalText('');
        setParaphrasedText('');
        setMetrics(null);
        setImprovements([]);
    };

    return (
        <div className="h-full w-full flex flex-col bg-white">


            {/* Main Content - Side by Side */}
            <div className="flex-1 flex overflow-hidden">
                {/* LEFT PANEL - Original Text */}
                <div className="w-1/2 border-r border-gray-200 flex flex-col bg-gray-50">
                    {/* Textarea */}
                    <div className="flex-1 p-4">
                        <textarea
                            value={originalText}
                            onChange={(e) => setOriginalText(e.target.value)}
                            placeholder="Paste your text here...&#10;&#10;The research demonstrates the efficacy of machine learning algorithms in medical diagnostics."
                            className="w-full h-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-sm leading-relaxed"
                        />
                    </div>

                    {/* Mode Selector & Actions */}
                    <div className="p-4 border-t border-gray-200 bg-white space-y-3">
                        {/* Mode Selector */}
                        <div className="flex items-center gap-3">
                            <span className="text-xs font-semibold text-gray-600 shrink-0">Mode:</span>
                            <div className="flex gap-2 flex-1 overflow-x-auto no-scrollbar">
                                {modes.map((mode) => (
                                    <button
                                        key={mode.id}
                                        onClick={() => setSelectedMode(mode.id)}
                                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all whitespace-nowrap ${selectedMode === mode.id
                                            ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md'
                                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        <span className="mr-1">{mode.icon}</span>
                                        {mode.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2">
                            <button
                                onClick={handlePaste}
                                className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-1"
                            >
                                <Clipboard className="w-3.5 h-3.5" />
                                Paste
                            </button>
                            <button
                                onClick={handleClear}
                                className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-1"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                                Clear
                            </button>
                            <button className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-1">
                                <Link2 className="w-3.5 h-3.5" />
                                From Detector
                            </button>
                        </div>

                        {/* Paraphrase Button */}
                        <button
                            onClick={handleParaphrase}
                            disabled={!originalText.trim() || isParaphrasing}
                            className="w-full px-4 py-3 text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 rounded-lg hover:from-indigo-700 hover:to-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                        >
                            <RefreshCw className="w-4 h-4" />
                            {isParaphrasing ? 'Paraphrasing...' : '✨ Paraphrase'}
                        </button>
                    </div>
                </div>

                {/* RIGHT PANEL - Paraphrased Text */}
                <div className="w-1/2 flex flex-col bg-white">
                    {/* Content */}
                    <div className="flex-1 overflow-y-auto">
                        {!paraphrasedText ? (
                            <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4">
                                <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mb-3">
                                    <RefreshCw className="w-8 h-8 text-gray-300" />
                                </div>
                                <p className="text-sm font-medium">No paraphrase yet</p>
                                <p className="text-xs text-gray-400 mt-1">Enter text and click "Paraphrase"</p>
                            </div>
                        ) : (
                            <div className="p-4 space-y-4">
                                {/* Paraphrased Text */}
                                <div className="p-4 bg-gradient-to-br from-indigo-50 to-violet-50 rounded-xl border border-indigo-200">
                                    <p className="text-sm text-gray-800 leading-relaxed">{paraphrasedText}</p>
                                    <div className="flex gap-2 mt-3">
                                        <button
                                            onClick={handleParaphrase}
                                            className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-white border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors flex items-center gap-1"
                                        >
                                            <RefreshCw className="w-3.5 h-3.5" />
                                            Regenerate
                                        </button>
                                        <button
                                            onClick={handleCopy}
                                            className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-white border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors flex items-center gap-1"
                                        >
                                            <Clipboard className="w-3.5 h-3.5" />
                                            Copy
                                        </button>
                                        <button className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-white border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors flex items-center gap-1">
                                            <Save className="w-3.5 h-3.5" />
                                            Save to Notes
                                        </button>
                                    </div>
                                </div>

                                {/* Quality Metrics */}
                                {metrics && (
                                    <div className="bg-white border border-gray-200 rounded-xl p-4">
                                        <h4 className="text-sm font-semibold text-gray-900 mb-3">Quality Metrics</h4>
                                        <div className="space-y-2">
                                            {[
                                                { label: 'Uniqueness', value: metrics.uniqueness, target: 80 },
                                                { label: 'Readability', value: metrics.readability, target: 70 },
                                                { label: 'Natural Flow', value: metrics.naturalFlow, target: 85 },
                                                { label: 'AI Detection', value: metrics.aiDetection, target: 30, inverse: true },
                                            ].map((metric, i) => (
                                                <div key={i}>
                                                    <div className="flex justify-between text-xs mb-1">
                                                        <span className="text-gray-600">{metric.label}:</span>
                                                        <span className="font-semibold text-gray-900">{Math.round(metric.value)}%</span>
                                                    </div>
                                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                                        <div
                                                            className={`h-2 rounded-full transition-all ${metric.inverse
                                                                ? metric.value < metric.target ? 'bg-green-500' : 'bg-yellow-500'
                                                                : metric.value >= metric.target ? 'bg-green-500' : 'bg-yellow-500'
                                                                }`}
                                                            style={{ width: `${metric.value}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Improvements */}
                                {improvements.length > 0 && (
                                    <div className="bg-white border border-gray-200 rounded-xl p-4">
                                        <h4 className="text-sm font-semibold text-gray-900 mb-3">📊 Improvements Made</h4>
                                        <div className="space-y-1.5">
                                            {improvements.map((improvement, i) => (
                                                <div key={i} className="flex items-start gap-2 text-xs text-gray-700">
                                                    <span className="text-green-600">✅</span>
                                                    <span>{improvement}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Version History */}
                                {versions.length > 0 && (
                                    <div className="bg-white border border-gray-200 rounded-xl p-4">
                                        <h4 className="text-sm font-semibold text-gray-900 mb-3">🔄 Version History</h4>
                                        <div className="space-y-2">
                                            {versions.map((version, i) => (
                                                <div
                                                    key={version.id}
                                                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-medium text-gray-600">v{version.id}</span>
                                                        <span className="text-xs text-gray-500">-</span>
                                                        <span className="text-xs text-gray-700 capitalize">{version.mode}</span>
                                                        {i === 0 && <span className="text-xs text-indigo-600">⭐ current</span>}
                                                    </div>
                                                    <span className="text-xs text-gray-500">{version.quality}% quality</span>
                                                </div>
                                            ))}
                                        </div>
                                        <button className="w-full mt-2 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-1">
                                            <Download className="w-3.5 h-3.5" />
                                            Export All Versions
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Bottom Actions */}
            {paraphrasedText && (
                <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex gap-2">
                    <button className="px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                        <Download className="w-3.5 h-3.5" />
                        Export as Word
                    </button>
                    <button className="px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                        <Download className="w-3.5 h-3.5" />
                        Export as PDF
                    </button>
                    <button className="px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                        <Clipboard className="w-3.5 h-3.5" />
                        Copy Both Versions
                    </button>
                </div>
            )}
        </div>
    );
}
