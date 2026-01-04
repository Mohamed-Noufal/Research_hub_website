import { useState, useRef } from 'react';
import {
  ExternalLink, FileText,
  ChevronLeft, Eye, Network, Highlighter, MessageSquare,
  Calendar, Building2, Award, TrendingUp, Quote, Upload
} from 'lucide-react';

import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import type { Paper } from '../../App';
import { toast } from 'sonner';

interface PaperViewerProps {
  paper?: Paper;
  onPdfUpload?: () => void;
}

type TabType = 'abstract' | 'pdf' | 'notes' | 'citations' | 'related';

export default function PaperViewer({ paper, onPdfUpload }: PaperViewerProps) {
  const [activeTab, setActiveTab] = useState<TabType>('abstract');
  const [localPdfUrl, setLocalPdfUrl] = useState<string | undefined>(undefined);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use local URL if available, otherwise paper.pdfUrl
  const displayPdfUrl = localPdfUrl || paper?.pdfUrl;

  // Check if PDF is external (not localhost/127.0.0.1)
  // We treat anything that doesn't explicitly look like our local server as external
  const isLocalPdf = displayPdfUrl && (
    displayPdfUrl.trim().startsWith('http://localhost') ||
    displayPdfUrl.trim().startsWith('http://127.0.0.1') ||
    displayPdfUrl.trim().startsWith('/uploads/')
  );

  const isExternalPdf = displayPdfUrl && !isLocalPdf;

  const handleDownloadPdf = async () => {
    if (!paper) return;

    setIsDownloading(true);
    const toastId = toast.loading('Downloading PDF from external source...');

    try {
      const { apiService } = await import('../../services/api');
      const response = await apiService.downloadPaperPdf(paper.id);

      if (response.already_local) {
        toast.info('PDF is already stored locally', { id: toastId });
      } else {
        setLocalPdfUrl(response.pdf_url);
        const sizeKB = response.file_size ? (response.file_size / 1024).toFixed(2) : 'unknown';
        toast.success(`PDF downloaded successfully (${sizeKB} KB)`, { id: toastId });

        // Refresh library to show updated PDF
        if (onPdfUpload) {
          onPdfUpload();
        }
      }
    } catch (error) {
      console.error('Download failed:', error);
      toast.error('Failed to download PDF. The link may be broken or restricted.', { id: toastId });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleUploadPdf = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!paper || !event.target.files || event.target.files.length === 0) return;

    const file = event.target.files[0];

    // Validate file type
    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('File too large. Maximum size is 50MB');
      return;
    }

    setIsUploading(true);
    const toastId = toast.loading(`Uploading ${file.name}...`);

    try {
      const { apiService } = await import('../../services/api');
      const response = await apiService.uploadPaperPdf(paper.id, file);

      setLocalPdfUrl(response.pdf_url);
      toast.success('PDF uploaded successfully!', { id: toastId });

      // Refresh library
      if (onPdfUpload) {
        onPdfUpload();
      }
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload PDF', { id: toastId });
    } finally {
      setIsUploading(false);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  if (!paper) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-10 h-10 text-gray-300" />
          </div>
          <p className="text-sm font-medium text-gray-600">No paper selected</p>
          <p className="text-xs text-gray-400 mt-1">Select a paper from your library to view</p>
        </div>
      </div>
    );
  }

  const formatAuthors = (authors: string[]) => {
    if (authors.length === 0) return 'Unknown';
    if (authors.length <= 3) return authors.join(', ');
    return `${authors.slice(0, 3).join(', ')} +${authors.length - 3} more`;
  };

  const tabs: { id: TabType; label: string; icon: any }[] = [
    { id: 'abstract', label: 'Abstract', icon: FileText },
    { id: 'pdf', label: 'PDF', icon: Eye },
    { id: 'notes', label: 'Notes', icon: MessageSquare },
    { id: 'citations', label: 'Citations', icon: Quote },
    { id: 'related', label: 'Related', icon: Network },
  ];

  return (
    <div className="h-full flex bg-gray-50">
      {/* LEFT PANEL - Metadata */}
      <div className="w-80 border-r border-gray-200 bg-white flex flex-col overflow-hidden shrink-0">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
          <button
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-3 transition-colors"
            onClick={() => window.history.back()}
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Library
          </button>
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shrink-0 text-2xl">
              📄
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Paper Details</h3>
              <p className="text-sm font-medium text-gray-900 line-clamp-2 leading-tight">{paper.title}</p>
            </div>
          </div>
        </div>

        {/* Scrollable Metadata */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Quick Stats */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">📊 Quick Stats</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Quote className="w-3.5 h-3.5 text-purple-600" />
                  <span className="text-xs text-gray-600">Citations</span>
                </div>
                <p className="text-lg font-bold text-purple-700">{paper.citations}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-blue-600" />
                  <span className="text-xs text-gray-600">Year</span>
                </div>
                <p className="text-lg font-bold text-blue-700">{paper.year}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-3.5 h-3.5 text-green-600" />
                  <span className="text-xs text-gray-600">Impact</span>
                </div>
                <p className="text-lg font-bold text-green-700">High</p>
              </div>
              <div className="bg-amber-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Award className="w-3.5 h-3.5 text-amber-600" />
                  <span className="text-xs text-gray-600">Quartile</span>
                </div>
                <p className="text-lg font-bold text-amber-700">Q1</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Tags/Topics */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">🏷️ Topics</h4>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="text-xs">Machine Learning</Badge>
              <Badge variant="secondary" className="text-xs">Neural Networks</Badge>
              <Badge variant="secondary" className="text-xs">Computer Vision</Badge>
            </div>
          </div>

          <Separator />

          {/* Authors */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">👥 Authors ({paper.authors.length})</h4>
            <div className="space-y-2">
              {paper.authors.slice(0, 5).map((author, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-400 to-blue-400 flex items-center justify-center text-white text-xs font-medium">
                    {author.charAt(0)}
                  </div>
                  <span className="text-gray-700">{author}</span>
                </div>
              ))}
              {paper.authors.length > 5 && (
                <button className="text-xs text-purple-600 hover:text-purple-700 font-medium">
                  +{paper.authors.length - 5} more
                </button>
              )}
            </div>
          </div>

          <Separator />

          {/* Publication Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">📚 Publication</h4>

            {paper.venue && (
              <div className="flex items-start gap-2">
                <Building2 className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500">Venue</p>
                  <p className="text-sm text-gray-900 font-medium">{paper.venue}</p>
                </div>
              </div>
            )}

            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500">Source</p>
                <Badge variant="outline" className="mt-1">{paper.source}</Badge>
              </div>
            </div>

            {paper.doi && (
              <div className="flex items-start gap-2">
                <ExternalLink className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500">DOI</p>
                  <a
                    href={`https://doi.org/${paper.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-purple-600 hover:text-purple-700 hover:underline break-all"
                  >
                    {paper.doi}
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL - Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-white">
        {/* Tabs */}
        <div className="border-b border-gray-200 bg-white px-4">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all relative
                  ${activeTab === tab.id
                    ? 'text-purple-600'
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-600 to-blue-600" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'abstract' && (
            <div className="p-6">
              {/* Title - Large and prominent */}
              <h1 className="text-2xl font-bold text-gray-900 leading-tight mb-4">
                {paper.title}
              </h1>

              {/* Authors line */}
              <p className="text-sm text-gray-600 mb-6">
                {formatAuthors(paper.authors)} · {paper.year}
              </p>

              {/* Abstract Section */}
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 mb-6 border border-purple-100">
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Abstract
                </h2>
                <p className="text-gray-800 leading-relaxed text-base">{paper.abstract}</p>
              </div>

              {/* Key Insights (Mock) */}
              <div className="bg-white rounded-xl p-6 border border-gray-200 mb-6">
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4 flex items-center gap-2">
                  <Highlighter className="w-4 h-4" />
                  AI-Generated Key Insights
                </h2>
                <div className="space-y-3">
                  {[
                    'Novel deep learning architecture achieving state-of-the-art results',
                    'Significant improvement in computational efficiency (40% faster)',
                    'Extensive evaluation on 5 benchmark datasets',
                  ].map((insight, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center shrink-0 text-xs font-bold">
                        {idx + 1}
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">{insight}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Methodology (Mock) */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-500 mb-2">Dataset</h3>
                  <p className="text-sm text-gray-900">ImageNet, COCO</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-500 mb-2">Method</h3>
                  <p className="text-sm text-gray-900">Supervised Learning</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-500 mb-2">Metrics</h3>
                  <p className="text-sm text-gray-900">Accuracy, F1-Score</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'pdf' && (
            <div className="h-full bg-gray-50 flex flex-col">
              {displayPdfUrl ? (
                <>
                  <div className="bg-white border-b border-gray-200 p-3 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">PDF Preview</span>
                      <Badge variant="secondary" className="text-xs">
                        {paper.openAccess ? 'Open Access' : 'External Source'}
                      </Badge>
                    </div>
                    <div className="flex gap-2">
                      {/* Hidden file input */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,application/pdf"
                        style={{ display: 'none' }}
                        onChange={handleUploadPdf}
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        {isUploading ? 'Uploading...' : 'Upload PDF'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(displayPdfUrl, '_blank')}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Open in Browser
                      </Button>
                    </div>
                  </div>
                  <div className="flex-1 w-full h-full bg-gray-200 relative">
                    {isExternalPdf ? (
                      /* External PDF: Show Download UI directly (No iframe to avoid blocking) */
                      <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                        <div className="bg-white border-2 border-dashed border-gray-300 rounded-xl p-8 text-center max-w-md">
                          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                          </div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            PDF Available for Download
                          </h3>
                          <p className="text-sm text-gray-600 mb-6">
                            This paper has an external PDF. Download it to view it locally.
                          </p>
                          <div className="flex gap-3 justify-center">
                            <Button
                              size="sm"
                              onClick={handleDownloadPdf}
                              disabled={isDownloading}
                              className="bg-blue-600 hover:bg-blue-700"
                            >
                              {isDownloading ? (
                                <>
                                  <svg className="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  Downloading...
                                </>
                              ) : (
                                <>
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                  </svg>
                                  Download & View
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => window.open(displayPdfUrl, '_blank')}
                            >
                              <ExternalLink className="w-4 h-4 mr-2" />
                              Open in Browser
                            </Button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Local PDF: Show iframe */
                      <iframe
                        key={displayPdfUrl} // Force re-render when URL changes
                        src={displayPdfUrl}
                        className="w-full h-full border-0"
                        title="PDF Viewer"
                      />
                    )}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-full p-6">
                  <div className="text-center max-w-md">
                    <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <FileText className="w-10 h-10 text-gray-300" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No PDF Available</h3>
                    <p className="text-sm text-gray-600 mb-6">
                      We couldn't find a direct PDF link for this paper.
                    </p>
                    <div className="flex gap-2 justify-center">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,application/pdf"
                        style={{ display: 'none' }}
                        onChange={handleUploadPdf}
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        {isUploading ? 'Uploading...' : 'Upload PDF'}
                      </Button>
                      {paper.doi && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => window.open(`https://doi.org/${paper.doi}`, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Visit Publisher Page
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'notes' && (
            <div className="p-6">
              <div className="text-center max-w-md mx-auto py-12">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No notes yet</h3>
                <p className="text-sm text-gray-600 mb-4">Start taking notes on this paper</p>
                <Button>
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Create Note
                </Button>
              </div>
            </div>
          )}

          {activeTab === 'citations' && (
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4">Citations ({paper.citations})</h2>
              <p className="text-sm text-gray-600">Citation network visualization will appear here</p>
            </div>
          )}

          {activeTab === 'related' && (
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Network className="w-5 h-5" />
                Related Papers
              </h2>
              <div className="space-y-3">
                {[1, 2, 3].map((idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-purple-300 transition-colors cursor-pointer">
                    <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2">
                      Similar research paper title{idx}
                    </h3>
                    <p className="text-xs text-gray-600 mb-2">Authors et al. · 2023</p>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">89% match</Badge>
                      <span className="text-xs text-gray-500">125 citations</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div >
  );
}

