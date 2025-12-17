import { useState, useEffect } from 'react';
import { Brain, Clipboard, Trash2, Sparkles, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

interface SentenceAnalysis {
    text: string;
    score: number;
    issues: string[];
}

interface DetectionResult {
    overallScore: number;
    confidence: number;
    sentences: SentenceAnalysis[];
    patterns: string[];
    recommendations: string[];
}

interface AIDetectorProps {
    onParaphrase?: (text: string) => void;
}

export default function AIDetector({ onParaphrase }: AIDetectorProps) {
    const [textInput, setTextInput] = useState('');
    const [result, setResult] = useState<DetectionResult | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [animatedScore, setAnimatedScore] = useState(0);

    // Animate score on result change
    useEffect(() => {
        if (result) {
            let start = 0;
            const end = result.overallScore;
            const duration = 1000;
            const increment = end / (duration / 16);

            const timer = setInterval(() => {
                start += increment;
                if (start >= end) {
                    setAnimatedScore(end);
                    clearInterval(timer);
                } else {
                    setAnimatedScore(Math.floor(start));
                }
            }, 16);
            return () => clearInterval(timer);
        } else {
            setAnimatedScore(0);
        }
    }, [result]);

    // Mock AI detection logic
    const analyzeText = async (text: string): Promise<DetectionResult> => {
        await new Promise(resolve => setTimeout(resolve, 1500));

        const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
        const sentenceAnalyses: SentenceAnalysis[] = sentences.map(sentence => {
            const trimmed = sentence.trim();
            let score = 50;
            const issues: string[] = [];

            // Check for AI patterns
            if (trimmed.toLowerCase().includes('demonstrates') || trimmed.toLowerCase().includes('efficacy')) {
                score += 20;
                issues.push('Formal vocabulary');
            }
            if (trimmed.toLowerCase().includes('novel') || trimmed.toLowerCase().includes('presents')) {
                score += 15;
                issues.push('Generic phrasing');
            }
            if (!trimmed.includes("'") && !trimmed.includes("n't")) {
                score += 10;
                issues.push('No contractions');
            }
            if (trimmed.split(' ').length > 15) {
                score += 5;
                issues.push('Long sentence');
            }

            return { text: trimmed, score: Math.min(score, 95), issues };
        });

        const overallScore = Math.round(
            sentenceAnalyses.reduce((sum, s) => sum + s.score, 0) / sentenceAnalyses.length
        );

        const patterns: string[] = [];
        if (overallScore > 70) {
            patterns.push('Repetitive sentence structure');
            patterns.push('Overly formal vocabulary');
            patterns.push('Lack of contractions');
            patterns.push('Passive voice usage');
        }

        const recommendations = [
            'Add personal pronouns (we, our)',
            'Use contractions naturally',
            'Vary sentence structure',
            'Add specific examples',
            'Use active voice',
        ];

        return {
            overallScore,
            confidence: 92,
            sentences: sentenceAnalyses,
            patterns,
            recommendations,
        };
    };

    const handleAnalyze = async () => {
        if (!textInput.trim()) return;
        setIsAnalyzing(true);
        const analysis = await analyzeText(textInput);
        setResult(analysis);
        setIsAnalyzing(false);
    };

    const handlePaste = async () => {
        try {
            const text = await navigator.clipboard.readText();
            setTextInput(text);
        } catch (error) {
            console.error('Failed to read clipboard:', error);
        }
    };

    const handleClear = () => {
        setTextInput('');
        setResult(null);
    };

    const getScoreColor = (score: number) => {
        if (score < 30) return 'text-emerald-600';
        if (score < 70) return 'text-amber-600';
        return 'text-rose-600';
    };

    const getScoreGradient = (score: number) => {
        if (score < 30) return 'from-emerald-500 to-teal-500';
        if (score < 70) return 'from-amber-500 to-orange-500';
        return 'from-rose-500 to-red-500';
    };

    const getScoreLabel = (score: number) => {
        if (score < 30) return { icon: '🟢', text: 'Likely Human', sub: 'Content appears natural', color: 'text-emerald-700', bg: 'bg-emerald-50' };
        if (score < 70) return { icon: '🟡', text: 'Mixed Signals', sub: 'Contains AI patterns', color: 'text-amber-700', bg: 'bg-amber-50' };
        return { icon: '🔴', text: 'Likely AI-Generated', sub: 'High probability of AI', color: 'text-rose-700', bg: 'bg-rose-50' };
    };

    const wordCount = textInput.trim().split(/\s+/).filter(w => w).length;
    const charCount = textInput.length;

    // Circular Progress Component
    const CircularProgress = ({ score }: { score: number }) => {
        const radius = 80;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (score / 100) * circumference;

        let strokeColor = '#f43f5e'; // rose-500
        if (score < 70) strokeColor = '#f59e0b'; // amber-500
        if (score < 30) strokeColor = '#10b981'; // emerald-500

        return (
            <div className="relative flex items-center justify-center">
                <svg className="transform -rotate-90 w-48 h-48">
                    <circle
                        cx="96"
                        cy="96"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="12"
                        fill="transparent"
                        className="text-slate-100"
                    />
                    <circle
                        cx="96"
                        cy="96"
                        r={radius}
                        stroke={strokeColor}
                        strokeWidth="12"
                        fill="transparent"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out"
                    />
                </svg>
                <div className="absolute flex flex-col items-center">
                    <span className={`text-5xl font-bold ${getScoreColor(score)}`}>{score}%</span>
                    <span className="text-xs font-medium text-slate-400 uppercase tracking-wider mt-1">AI Score</span>
                </div>
            </div>
        );
    };

    return (
        <div className="h-full w-full flex flex-col bg-slate-50 font-sans">
            {/* Header */}
            <div className="h-16 border-b border-slate-200 flex items-center justify-between px-6 bg-white shadow-sm z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                        <Brain className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-slate-900 tracking-tight">AI Writing Detector</h2>
                        <p className="text-xs text-slate-500 font-medium">Advanced Pattern Analysis</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className="px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold border border-indigo-100 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" />
                        Pro Model Active
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* LEFT PANEL - Input */}
                <div className="w-5/12 min-w-[400px] border-r border-slate-200 flex flex-col bg-white">
                    <div className="flex-1 p-6">
                        <div className="h-full flex flex-col relative group">
                            <textarea
                                value={textInput}
                                onChange={(e) => setTextInput(e.target.value)}
                                placeholder="Paste your text here to analyze..."
                                className="flex-1 w-full p-6 bg-slate-50 rounded-2xl border-2 border-transparent focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 transition-all resize-none text-base leading-relaxed text-slate-700 placeholder:text-slate-400 outline-none"
                            />

                            {/* Floating Action Bar */}
                            <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between bg-white/90 backdrop-blur-sm p-2 rounded-xl border border-slate-200 shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
                                <div className="flex gap-1">
                                    <button onClick={handlePaste} className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors tooltip" title="Paste">
                                        <Clipboard className="w-4 h-4" />
                                    </button>
                                    <button onClick={handleClear} className="p-2 hover:bg-rose-50 hover:text-rose-600 rounded-lg text-slate-600 transition-colors" title="Clear">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="flex items-center gap-3 px-2">
                                    <span className="text-xs font-medium text-slate-500">{wordCount} words</span>
                                    <div className="w-px h-3 bg-slate-300" />
                                    <span className="text-xs font-medium text-slate-500">{charCount} chars</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 border-t border-slate-100 bg-white">
                        <button
                            onClick={handleAnalyze}
                            disabled={!textInput.trim() || isAnalyzing}
                            className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-bold text-lg shadow-xl shadow-indigo-500/20 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all transform active:scale-[0.99] flex items-center justify-center gap-3"
                        >
                            {isAnalyzing ? (
                                <>
                                    <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                                    Analyzing Patterns...
                                </>
                            ) : (
                                <>
                                    <Brain className="w-5 h-5" />
                                    Analyze Text
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* RIGHT PANEL - Results */}
                <div className="flex-1 bg-slate-50/50 overflow-y-auto p-8">
                    {!result ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400">
                            <div className="w-24 h-24 bg-white rounded-3xl shadow-sm border border-slate-100 flex items-center justify-center mb-6">
                                <Brain className="w-10 h-10 text-slate-300" />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-600 mb-2">Ready to Analyze</h3>
                            <p className="text-sm text-slate-400 max-w-xs text-center">
                                Paste your text on the left to detect AI-generated content patterns and writing style.
                            </p>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            {/* Main Score Card */}
                            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 flex items-center gap-12 relative overflow-hidden">
                                <div className={`absolute top-0 left-0 w-2 h-full bg-gradient-to-b ${getScoreGradient(result.overallScore)}`} />

                                <div className="shrink-0">
                                    <CircularProgress score={animatedScore} />
                                </div>

                                <div className="flex-1">
                                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold mb-3 ${getScoreLabel(result.overallScore).bg} ${getScoreLabel(result.overallScore).color}`}>
                                        {getScoreLabel(result.overallScore).icon}
                                        {getScoreLabel(result.overallScore).text}
                                    </div>
                                    <h3 className="text-2xl font-bold text-slate-900 mb-2">
                                        {getScoreLabel(result.overallScore).sub}
                                    </h3>
                                    <p className="text-slate-500 leading-relaxed mb-4">
                                        Our analysis indicates a <strong className="text-slate-700">{result.confidence}% confidence</strong> level in this result.
                                        {result.overallScore > 50
                                            ? " Several patterns typical of AI language models were detected."
                                            : " The writing style appears natural and human-like."}
                                    </p>

                                    {/* Paraphrase Button */}
                                    {onParaphrase && result.overallScore > 30 && (
                                        <button
                                            onClick={() => onParaphrase(textInput)}
                                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-lg transition-colors flex items-center gap-2 shadow-md shadow-indigo-500/20"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                            Paraphrase with AI
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                {/* Patterns */}
                                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                                    <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                                        Detected Patterns
                                    </h4>
                                    {result.patterns.length > 0 ? (
                                        <div className="space-y-3">
                                            {result.patterns.map((pattern, i) => (
                                                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-amber-50/50 border border-amber-100/50">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                                                    <span className="text-sm text-slate-700 font-medium">{pattern}</span>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-8 text-slate-400 text-sm">
                                            No suspicious patterns detected
                                        </div>
                                    )}
                                </div>

                                {/* Recommendations */}
                                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                                    <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                                        <Sparkles className="w-4 h-4 text-indigo-500" />
                                        Suggestions
                                    </h4>
                                    <div className="space-y-3">
                                        {result.recommendations.slice(0, 3).map((rec, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-indigo-50/50 border border-indigo-100/50">
                                                <CheckCircle2 className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                                                <span className="text-sm text-slate-700 font-medium">{rec}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Sentence Analysis */}
                            <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">
                                <div className="flex items-center justify-between mb-6">
                                    <h4 className="text-lg font-bold text-slate-900">Detailed Analysis</h4>
                                    <div className="flex gap-4 text-xs font-medium text-slate-500">
                                        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-rose-500" /> AI</div>
                                        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-500" /> Mixed</div>
                                        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-500" /> Human</div>
                                    </div>
                                </div>

                                <div className="space-y-1 leading-loose">
                                    {result.sentences.map((sentence, i) => (
                                        <span
                                            key={i}
                                            className={`
                                                inline relative group cursor-help px-1 py-0.5 rounded transition-colors
                                                ${sentence.score > 70 ? 'bg-rose-100/80 text-rose-900 hover:bg-rose-200' :
                                                    sentence.score > 30 ? 'bg-amber-100/50 text-amber-900 hover:bg-amber-200' :
                                                        'hover:bg-emerald-50 text-slate-700'}
                                            `}
                                        >
                                            {sentence.text}{' '}

                                            {/* Tooltip */}
                                            <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 bg-slate-900 text-white text-xs rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 shadow-xl">
                                                <div className="font-bold mb-1 flex justify-between">
                                                    <span>AI Score</span>
                                                    <span>{sentence.score}%</span>
                                                </div>
                                                <div className="text-slate-300">
                                                    {sentence.issues.length > 0 ? sentence.issues.join(', ') : 'Natural phrasing'}
                                                </div>
                                                <div className="absolute bottom-[-6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-slate-900 rotate-45" />
                                            </span>
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
