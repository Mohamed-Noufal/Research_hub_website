import { useState, useEffect, useRef, useCallback } from 'react';
import {
  BookmarkCheck, FolderOpen, History, Settings, BookOpen,
  X, Sparkles, FileText, Maximize2, ChevronLeft, Quote, Columns2, Plus,
  Search, Brain, PenTool
} from 'lucide-react';
import type { View, Paper } from '../App';

// Import Real Components
import LibraryPanel from './workspace/LibraryPanel';
import AIAssistant from './workspace/AIAssistant';
import PaperViewer from './workspace/PaperViewer';
import NotesManager from './workspace/NotesManager';
import LiteratureReview from './workspace/LiteratureReview';
import Citations from './workspace/Citations';
import HistoryPanel from './workspace/HistoryPanel';
// Import New Tools
import DOIFetcher from './workspace/DOIFetcher';
import AIDetector from './workspace/AIDetector';
import AIParaphraser from './workspace/AIParaphraser';
import { useLiteratureReviews } from '../hooks/useLiteratureReviews';
import type { Project } from './workspace/literature-review/types';

interface WorkspaceProps {
  savedPapers: Paper[];
  onNavigate: (view: View) => void;
  onSavePaper: (paper: Paper) => void;
  onSearch: (query: string, category?: string) => void;
}

// Tab Interface (replacing Windows)
interface Tab {
  id: string;
  type: 'paper' | 'notes' | 'assistant' | 'literature-review' | 'citations' | 'history' | 'doi-fetcher' | 'ai-detector' | 'ai-paraphraser';
  label: string;
  paperId?: string;
  projectId?: number;
}

const Workspace = ({ savedPapers = [], onNavigate, onSearch }: WorkspaceProps) => {
  const { data: literatureReviewsData } = useLiteratureReviews();
  const projects = literatureReviewsData?.reviews || [];

  // --- Layout State ---
  const [leftPanelWidth, setLeftPanelWidth] = useState(280);
  const [rightPanelWidth, setRightPanelWidth] = useState(350);
  const [leftPanelVisible, setLeftPanelVisible] = useState(true);
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  const [isSplitView, setIsSplitView] = useState(false);

  // --- Library Refresh State ---
  const [libraryRefreshKey, setLibraryRefreshKey] = useState(0);
  const [backendSavedPapers, setBackendSavedPapers] = useState<Paper[]>([]);
  const [isLoadingLibrary, setIsLoadingLibrary] = useState(false); // eslint-disable-line @typescript-eslint/no-unused-vars

  // --- Active Views ---
  const [activeSidebarItem, setActiveSidebarItem] = useState<'library' | 'notes' | 'history' | 'literature-review' | 'citations' | 'doi-fetcher' | 'ai-detector' | 'ai-paraphraser'>('library');

  // --- Tab State ---
  const [tabs, setTabs] = useState<Tab[]>([
    { id: '1', type: 'paper', label: 'Paper Viewer', paperId: undefined }
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('1');
  const [secondaryTabId, setSecondaryTabId] = useState<string | null>(null);
  const [showNewTabMenu, setShowNewTabMenu] = useState(false);
  const [activeTabDropdown, setActiveTabDropdown] = useState<string | null>(null);
  const [draggedTabId, setDraggedTabId] = useState<string | null>(null);

  // Fetch saved papers from backend
  useEffect(() => {
    const fetchSavedPapers = async () => {
      setIsLoadingLibrary(true);
      try {
        const { apiService } = await import('../services/api');
        const response = await apiService.getSavedPapers();

        // Map API Paper to App Paper interface
        const mappedPapers: Paper[] = response.papers.map((p: any) => ({
          id: p.id?.toString() || String(p.id), // Ensure ID is always a string
          title: p.title,
          authors: p.authors || [],
          abstract: p.abstract || '',
          year: p.publication_date ? new Date(p.publication_date).getFullYear() : new Date().getFullYear(),
          citations: p.citation_count || 0,
          source: (p.source?.toLowerCase() as any) || 'unknown',
          url: p.pdf_url || '',
          pdfUrl: p.pdf_url,
          doi: p.doi,
          venue: p.venue,
          saved: true,
          openAccess: !!p.pdf_url // Assume open access if PDF URL exists for now
        }));

        setBackendSavedPapers(mappedPapers);
      } catch (error) {
        console.error('Failed to fetch saved papers:', error);
      } finally {
        setIsLoadingLibrary(false);
      }
    };

    fetchSavedPapers();
  }, [libraryRefreshKey]); // Re-fetch when library refresh is triggered

  // Callback to refresh library when a paper is saved from DOI Fetcher
  const handleLibraryRefresh = () => {
    setLibraryRefreshKey(prev => prev + 1);
    // Also switch to library view to show the saved paper
    setActiveSidebarItem('library');
    setLeftPanelVisible(true);
  };

  // --- Resizing Logic ---
  const isResizingLeft = useRef(false);
  const isResizingRight = useRef(false);
  const isResizingSplit = useRef(false);
  const [splitPaneWidth, setSplitPaneWidth] = useState(50); // percentage

  const startResizingLeft = useCallback(() => { isResizingLeft.current = true; }, []);
  const startResizingRight = useCallback(() => { isResizingRight.current = true; }, []);
  const startResizingSplit = useCallback(() => {
    isResizingSplit.current = true;
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
  }, []);

  const stopResizing = useCallback(() => {
    isResizingLeft.current = false;
    isResizingRight.current = false;
    isResizingSplit.current = false;
  }, []);

  const handleResize = useCallback((e: MouseEvent) => {
    if (isResizingLeft.current) {
      const newWidth = e.clientX - 48; // Subtract Activity Bar width
      if (newWidth > 150 && newWidth < 600) setLeftPanelWidth(newWidth);
    }
    if (isResizingRight.current) {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 200 && newWidth < 800) setRightPanelWidth(newWidth);
    }
    if (isResizingSplit.current) {
      // Calculate percentage based on the main content area
      // Get the content area element
      const contentArea = document.querySelector('.flex-1.flex.overflow-hidden.relative');
      if (contentArea) {
        const rect = contentArea.getBoundingClientRect();
        const relativeX = e.clientX - rect.left;
        const percentage = (relativeX / rect.width) * 100;

        // Constrain between 20% and 80%
        if (percentage >= 20 && percentage <= 80) {
          setSplitPaneWidth(percentage);
        }
      }
    }
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      handleResize(e);
      // Prevent text selection during resize
      if (isResizingLeft.current || isResizingRight.current || isResizingSplit.current) {
        e.preventDefault();
      }
    };

    const handleMouseUp = () => {
      stopResizing();
      // Re-enable text selection
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleResize, stopResizing]);

  // --- Tab Management ---
  const openTab = (type: Tab['type'], label: string, paperId?: string, projectId?: number) => {
    // Check if tab exists
    const existingTab = tabs.find(t =>
      t.type === type &&
      (paperId ? t.paperId === paperId : true) &&
      (projectId ? t.projectId === projectId : true) &&
      t.label === label
    );

    if (existingTab) {
      setActiveTabId(existingTab.id);
      return;
    }

    const newTab: Tab = {
      id: Date.now().toString(),
      type,
      label,
      paperId,
      projectId
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newTab.id);
    setShowNewTabMenu(false);

    // If split view is active and no secondary tab, set it
    if (isSplitView && !secondaryTabId) {
      setSecondaryTabId(newTab.id);
    }
  };

  const closeTab = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const newTabs = tabs.filter(t => t.id !== id);
    setTabs(newTabs);
    if (activeTabId === id && newTabs.length > 0) {
      setActiveTabId(newTabs[newTabs.length - 1].id);
    }
    if (secondaryTabId === id) {
      setSecondaryTabId(null);
    }
  };

  // --- Paraphraser State ---
  const [paraphraseInitialText, setParaphraseInitialText] = useState<string | undefined>(undefined);

  const handleParaphraseRequest = (text: string) => {
    setParaphraseInitialText(text);
    openTab('ai-paraphraser', 'Paraphraser');
  };

  // --- Render Helpers ---
  const renderSidebarContent = () => {
    switch (activeSidebarItem) {
      case 'library':
        return (
          <LibraryPanel
            onOpenPaper={(paper) => openTab('paper', paper.title.substring(0, 20) + '...', paper.id)}
          />
        );
      case 'notes':
        return (
          <div className="flex flex-col h-full">
            <div className="p-3 border-b border-[#E9ECEF] flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">MY NOTES</span>
              <button
                onClick={() => openTab('notes', 'New Note')}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="New Note"
              >
                <Plus className="w-3.5 h-3.5 text-gray-500" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {['Research Plan', 'Meeting Notes', 'Ideas & Brainstorm', 'Draft V1', 'Literature Summary'].map((note, i) => (
                <button
                  key={i}
                  onClick={() => openTab('notes', note)}
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-2 transition-colors"
                >
                  <FileText className="w-3.5 h-3.5 text-gray-400" />
                  <span className="flex-1 truncate">{note}</span>
                </button>
              ))}
            </div>
          </div>
        );
      case 'literature-review':
        return (
          <div className="flex flex-col h-full">
            <div className="p-3 border-b border-[#E9ECEF] flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">REVIEW PROJECTS</span>
              <button
                onClick={() => openTab('literature-review', 'New Review')}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="New Review"
              >
                <Plus className="w-3.5 h-3.5 text-gray-500" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              <div className="flex-1 overflow-y-auto p-2">
                {projects.length === 0 ? (
                  <div className="text-sm text-gray-500 p-2 text-center">No projects yet. Create one!</div>
                ) : (
                  projects.map((project: Project) => (
                    <button
                      key={project.id}
                      onClick={() => openTab('literature-review', project.name, undefined, project.id)}
                      className="w-full text-left px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-2 transition-colors"
                    >
                      <BookOpen className="w-3.5 h-3.5 text-gray-400" />
                      <span className="flex-1 truncate">{project.name}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        );
      case 'citations':
        return (
          <div className="flex flex-col h-full">
            <div className="p-3 border-b border-[#E9ECEF] flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500">BIBLIOGRAPHIES</span>
              <button
                onClick={() => openTab('citations', 'New Bibliography')}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="New Bibliography"
              >
                <Plus className="w-3.5 h-3.5 text-gray-500" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {['Master Bibliography', 'Thesis References', 'Pending Citations', 'Archive'].map((list, i) => (
                <button
                  key={i}
                  onClick={() => openTab('citations', list)}
                  className="w-full text-left px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-2 transition-colors"
                >
                  <Quote className="w-3.5 h-3.5 text-gray-400" />
                  <span className="flex-1 truncate">{list}</span>
                </button>
              ))}
            </div>
          </div>
        );
      case 'history':
        return <HistoryPanel onSearch={onSearch} />;
      default:
        return null;
    }
  };

  const handleSidebarClick = (item: typeof activeSidebarItem) => {
    // New tools open in tabs instead of left panel
    if (item === 'doi-fetcher' || item === 'ai-detector' || item === 'ai-paraphraser') {
      const labels = {
        'doi-fetcher': 'DOI Fetcher',
        'ai-detector': 'AI Detector',
        'ai-paraphraser': 'Paraphraser'
      };
      openTab(item, labels[item]);
      return;
    }

    // ALL other icons open the left panel (Antigravity pattern)
    if (activeSidebarItem === item && leftPanelVisible) {
      // Toggle off if clicking the same active item
      setLeftPanelVisible(false);
    } else {
      // Activate and show panel
      setActiveSidebarItem(item);
      setLeftPanelVisible(true);
    }
  };

  const renderTabContent = (tabId: string) => {
    const tab = tabs.find(t => t.id === tabId);
    if (!tab) return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-50/50">
        <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-3">
          <BookOpen className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-sm">No tab selected</p>
      </div>
    );

    switch (tab.type) {
      case 'paper':
        return <PaperViewer paper={backendSavedPapers.find(p => p.id === tab.paperId || p.id.toString() === tab.paperId)} onPdfUpload={handleLibraryRefresh} />;
      case 'notes':
        return <NotesManager />;
      case 'assistant':
        return <AIAssistant papers={backendSavedPapers} />;
      case 'literature-review':
        return <LiteratureReview initialProjectId={tab.projectId} />;
      case 'citations':
        return <Citations papers={backendSavedPapers} />;
      case 'history':
        return <HistoryPanel onSearch={onSearch} />;
      case 'doi-fetcher':
        return <DOIFetcher onPaperSaved={handleLibraryRefresh} />;
      case 'ai-detector':
        return <AIDetector onParaphrase={handleParaphraseRequest} />;
      case 'ai-paraphraser':
        return <AIParaphraser initialText={paraphraseInitialText} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden font-sans text-gray-900">
      {/* Top Header */}
      <header className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-4 shrink-0 select-none">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Workspace
            </h1>
          </div>
          {/* Back to Results Button */}
          <button
            onClick={() => onNavigate('results')}
            className="ml-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-2 border border-gray-300"
            title="Back to Search Results"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Results
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setIsSplitView(!isSplitView);
              // When enabling split view, show active tab in both panes
              if (!isSplitView) {
                setSecondaryTabId(activeTabId);
              }
            }}
            className={`p-1 rounded hover:bg-gray-200 ${isSplitView ? 'text-blue-600 bg-blue-50' : 'text-gray-400'}`}
            title="Toggle Split Editor"
          >
            <Columns2 className="w-4 h-4" />
          </button>
          <div className="w-px h-4 bg-gray-300 mx-1" />
          <button onClick={() => setRightPanelVisible(!rightPanelVisible)} className={`p-1 rounded hover:bg-gray-200 ${rightPanelVisible ? 'text-blue-600' : 'text-gray-400'}`}>
            <Sparkles className="w-4 h-4" />
          </button>
        </div >
      </header >

      <div className="flex-1 flex overflow-hidden">
        {/* 1. Activity Bar (Fixed Left) */}
        <div className="w-12 bg-[#F1F3F5] border-r border-[#E9ECEF] flex flex-col items-center py-2 gap-1 shrink-0 z-20">
          <button
            onClick={() => onNavigate('search')}
            className="p-2.5 mb-2 rounded-lg text-gray-500 hover:bg-gray-200/50 hover:text-gray-900 transition-all"
            title="Back to Search"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          {[
            { id: 'library', icon: BookmarkCheck, label: 'Library' },
            { id: 'notes', icon: FolderOpen, label: 'Notes' },
            { id: 'literature-review', icon: BookOpen, label: 'Reviews' },
            { id: 'citations', icon: Quote, label: 'Citations' },
            { id: 'history', icon: History, label: 'History' },
          ].map((item) => {
            // Determine if this item is "active"
            const isActive = activeSidebarItem === item.id && leftPanelVisible;

            return (
              <button
                key={item.id}
                onClick={() => handleSidebarClick(item.id as any)}
                className={`p-2.5 rounded-lg transition-all relative group ${isActive
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-200/50 hover:text-gray-900'
                  }`}
                title={item.label}
              >
                <item.icon className="w-5 h-5" />
                {/* Tooltip */}
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
                  {item.label}
                </div>
              </button>
            )
          })}

          {/* Divider */}
          <div className="w-8 h-px bg-gray-300 my-2" />

          {/* New Tools Section */}
          {[
            { id: 'doi-fetcher', icon: Search, label: 'DOI Fetcher', color: 'text-purple-600' },
            { id: 'ai-detector', icon: Brain, label: 'AI Detector', color: 'text-blue-600' },
            { id: 'ai-paraphraser', icon: PenTool, label: 'Paraphraser', color: 'text-pink-600' },
          ].map((item) => {
            // Determine if this item is "active"
            const isActive = activeSidebarItem === item.id && leftPanelVisible;

            return (
              <button
                key={item.id}
                onClick={() => handleSidebarClick(item.id as any)}
                className={`p-2.5 rounded-lg transition-all relative group ${isActive
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-200/50 hover:text-gray-900'
                  }`}
                title={item.label}
              >
                <item.icon className="w-5 h-5" />
                {/* Tooltip */}
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
                  {item.label}
                </div>
              </button>
            )
          })}
          <div className="flex-1" />
          <button className="p-2.5 text-gray-500 hover:text-gray-900">
            <Settings className="w-5 h-5" />
          </button>
        </div>

        {/* 2. Resizable Side Panel (Now shows for ALL sidebar items) */}
        {leftPanelVisible && (
          <div
            className="flex flex-col bg-[#F8F9FA] border-r border-[#E9ECEF] relative"
            style={{ width: leftPanelWidth }}
          >
            <div className="h-9 border-b border-[#E9ECEF] flex items-center justify-between px-3 bg-[#F8F9FA]">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {activeSidebarItem.replace('-', ' ')}
              </span>
              <button onClick={() => setLeftPanelVisible(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {renderSidebarContent()}
            </div>
            {/* Resizer Handle */}
            <div
              className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400/50 transition-colors z-10"
              onMouseDown={startResizingLeft}
            />
          </div>
        )}

        {/* 3. Main Content Area (Tabbed + Split) */}
        <div className={`flex-1 flex flex-col min-w-0 bg-white relative ${!rightPanelVisible ? 'mr-0' : ''}`}>
          {/* Tab Bar */}
          <div className="flex items-center h-9 bg-[#F1F3F5] border-b border-[#E9ECEF] overflow-visible">
            <div className="flex items-center overflow-x-auto no-scrollbar flex-1">
              {tabs.map(tab => (
                <div
                  key={tab.id}
                  draggable
                  onDragStart={() => setDraggedTabId(tab.id)}
                  onDragEnd={() => setDraggedTabId(null)}
                  className={`
                  group flex items-center h-full min-w-[140px] max-w-[220px] text-xs border-r border-[#E9ECEF] select-none relative
                  ${activeTabId === tab.id ? 'bg-white text-gray-900 font-medium border-t-2 border-t-blue-500' : 'text-gray-500 hover:bg-gray-200/50'}
                  ${draggedTabId === tab.id ? 'opacity-50' : ''}
                `}
                  onContextMenu={(e) => {
                    e.preventDefault();
                    setActiveTabDropdown(activeTabDropdown === tab.id ? null : tab.id);
                  }}
                >
                  {/* Tab Content - Clickable */}
                  <div
                    onClick={(e) => {
                      // In split view, Shift+Click moves tab to secondary pane
                      if (isSplitView && e.shiftKey) {
                        setSecondaryTabId(tab.id);
                      } else {
                        setActiveTabId(tab.id);
                      }
                    }}
                    className="flex items-center gap-2 px-3 flex-1 min-w-0 cursor-pointer"
                    title={isSplitView ? "Click to view | Shift+Click to view in right pane" : "Click to view"}
                  >
                    <FileText className={`w-3.5 h-3.5 shrink-0 ${activeTabId === tab.id ? 'text-blue-500' : 'text-gray-400'}`} />
                    <span className="truncate flex-1">{tab.label}</span>
                  </div>

                  {/* Context Menu (Right-click) */}
                  {activeTabDropdown === tab.id && (
                    <>
                      <div className="absolute top-full left-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-xl py-1 z-[100]">
                        <button
                          onClick={() => {
                            if (!isSplitView) setIsSplitView(true);
                            setSecondaryTabId(tab.id);
                            setActiveTabDropdown(null);
                          }}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                        >
                          <Columns2 className="w-4 h-4 text-gray-400" />
                          Open in Split View
                        </button>
                        <button
                          onClick={() => {
                            closeTab(tab.id);
                            setActiveTabDropdown(null);
                          }}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-red-50 text-red-600 flex items-center gap-2"
                        >
                          <X className="w-4 h-4" />
                          Close Tab
                        </button>
                      </div>
                      {/* Click outside to close */}
                      <div className="fixed inset-0 z-[90]" onClick={() => setActiveTabDropdown(null)} />
                    </>
                  )}

                  {/* Close Button */}
                  <button
                    onClick={(e) => closeTab(tab.id, e)}
                    className={`p-1 rounded-md hover:bg-gray-200 mr-1 ${activeTabId === tab.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>

            {/* New Tab Button */}
            <div className="relative ml-1 z-50">
              <button
                onClick={() => setShowNewTabMenu(!showNewTabMenu)}
                className="p-1 hover:bg-gray-200 rounded text-gray-500"
                title="New Tab"
              >
                <Plus className="w-4 h-4" />
              </button>

              {/* Dropdown Menu - Opens from RIGHT */}
              {showNewTabMenu && (
                <div className="absolute top-full right-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-[100]">
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 border-b border-gray-100">OPEN VIEW</div>
                  <button onClick={() => openTab('notes', 'New Note')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-gray-400" /> Note
                  </button>
                  <button onClick={() => openTab('literature-review', 'Review Board')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-gray-400" /> Literature Review
                  </button>
                  <button onClick={() => openTab('citations', 'Citations')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <Quote className="w-4 h-4 text-gray-400" /> Citations
                  </button>
                  <button onClick={() => openTab('assistant', 'AI Chat')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-gray-400" /> AI Assistant
                  </button>
                  <div className="border-t border-gray-100 my-1"></div>
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500">NEW TOOLS</div>
                  <button onClick={() => openTab('doi-fetcher', 'DOI Fetcher')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <span className="text-base">📄</span> DOI Fetcher
                  </button>
                  <button onClick={() => openTab('ai-detector', 'AI Detector')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <span className="text-base">🤖</span> AI Detector
                  </button>
                  <button onClick={() => openTab('ai-paraphraser', 'Paraphraser')} className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                    <span className="text-base">✍️</span> Paraphraser
                  </button>
                </div>
              )}
            </div>

            {/* Click outside to close menu */}
            {showNewTabMenu && (
              <div className="fixed inset-0 z-40" onClick={() => setShowNewTabMenu(false)} />
            )}
          </div>

          {/* Content Area */}
          <div className="flex-1 flex overflow-hidden relative">
            {isSplitView ? (
              // Split View with Resizable Panes and Headers
              <>
                {/* Left Pane */}
                <div className="flex-1 flex flex-col overflow-hidden" style={{ width: `${splitPaneWidth}%` }}>
                  {/* Pane Header - Drop Zone */}
                  <div
                    className="h-8 bg-[#F8F9FA] border-b border-[#E9ECEF] flex items-center justify-between px-3 shrink-0"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (draggedTabId) {
                        setActiveTabId(draggedTabId);
                        setDraggedTabId(null);
                      }
                    }}
                  >
                    <span className="text-xs text-gray-600 truncate">
                      {tabs.find(t => t.id === activeTabId)?.label || 'No tab selected'}
                    </span>
                  </div>
                  {/* Pane Content */}
                  <div className="flex-1 overflow-hidden">
                    {renderTabContent(activeTabId)}
                  </div>
                </div>

                {/* Resize Handle */}
                <div
                  className="w-2 cursor-col-resize hover:bg-blue-500 active:bg-blue-600 transition-colors bg-gray-300 shrink-0 z-50 relative select-none"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    startResizingSplit();
                  }}
                  style={{ cursor: 'col-resize', userSelect: 'none' }}
                  title="Drag to resize"
                />

                {/* Right Pane */}
                <div className="flex-1 flex flex-col overflow-hidden" style={{ width: `${100 - splitPaneWidth}%` }}>
                  {/* Pane Header - Drop Zone */}
                  <div
                    className="h-8 bg-[#F8F9FA] border-b border-[#E9ECEF] flex items-center justify-between px-3 shrink-0"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (draggedTabId) {
                        setSecondaryTabId(draggedTabId);
                        setDraggedTabId(null);
                      }
                    }}
                  >
                    <span className="text-xs text-gray-600 truncate">
                      {tabs.find(t => t.id === (secondaryTabId || activeTabId))?.label || 'No tab selected'}
                    </span>
                    <button
                      onClick={() => setIsSplitView(false)}
                      className="p-0.5 hover:bg-gray-200 rounded text-gray-500"
                      title="Close split view"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {/* Pane Content */}
                  <div className="flex-1 overflow-hidden">
                    {renderTabContent(secondaryTabId || activeTabId)}
                  </div>
                </div>
              </>
            ) : (
              // Single View
              <div className="flex-1 overflow-hidden">
                {renderTabContent(activeTabId)}
              </div>
            )}
          </div>
        </div>

        {/* 4. Resizable AI Panel (Right) */}
        {rightPanelVisible && (
          <div
            className="flex flex-col bg-white border-l border-[#E9ECEF] relative shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)]"
            style={{ width: rightPanelWidth }}
          >
            {/* Resizer Handle */}
            <div
              className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400/50 transition-colors z-10"
              onMouseDown={startResizingRight}
            />

            <div className="h-9 border-b border-[#E9ECEF] flex items-center justify-between px-3 bg-[#FAFBFC]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-semibold text-gray-700">AI Assistant</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setRightPanelWidth(rightPanelWidth > 600 ? 350 : 800)}
                  className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                  title={rightPanelWidth > 600 ? "Restore size" : "Maximize width"}
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setRightPanelVisible(false)}
                  className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                  title="Close panel"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-hidden">
              <AIAssistant papers={savedPapers} />
            </div>
          </div>
        )}
      </div>
    </div >
  );
};

export default Workspace;
