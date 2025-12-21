import { useState, useEffect } from 'react';
import {
  BookOpen, Plus, ChevronRight, Users,
  LayoutGrid, PieChart as PieChartIcon,
  Target, Scale, FileText, FlaskConical,
  FolderPlus, MoreHorizontal, Trash2
} from 'lucide-react';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';

// Import types and hooks
import type { Project, Tab } from './literature-review/types';
import { useLiteratureReviews, useCreateLiteratureReview, useDeleteLiteratureReview, useUpdateLiteratureReview, useProjectPapers } from '../../hooks/useLiteratureReviews';
import { usersApi } from '../../api/users';
// MOCK_PAPERS removed as we now fetch real data

// Import tab components
import SummaryView from './literature-review/SummaryView';
import MethodologyView from './literature-review/MethodologyView';
import FindingsView from './literature-review/FindingsView';
import ComparisonView from './literature-review/ComparisonView';
import SynthesisView from './literature-review/SynthesisView';
import AnalysisView from './literature-review/AnalysisView';
import PaperSelector from './literature-review/PaperSelector';

// --- Main Component ---

export default function LiteratureReview({ initialProjectId }: { initialProjectId?: number }) {
  const [currentView, setCurrentView] = useState<'projects' | 'workspace'>(initialProjectId ? 'workspace' : 'projects');
  const [activeProject, setActiveProject] = useState<Project | null>(null);

  // We need the list of projects to find the matching project object if initialProjectId is provided
  const { data } = useLiteratureReviews();

  useEffect(() => {
    if (initialProjectId && data?.reviews) {
      const found = data.reviews.find((p: Project) => p.id === initialProjectId);
      if (found) {
        setActiveProject(found);
        setCurrentView('workspace');
      }
    }
  }, [initialProjectId, data]);

  const handleOpenProject = (project: Project) => {
    setActiveProject(project);
    setCurrentView('workspace');
  };

  const handleBackToProjects = () => {
    setActiveProject(null);
    setCurrentView('projects');
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {currentView === 'projects' ? (
        <ProjectList onOpenProject={handleOpenProject} />
      ) : activeProject ? (
        <ProjectWorkspace
          project={activeProject}
          onBack={handleBackToProjects}
        />
      ) : (
        <div className="flex items-center justify-center h-full">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}

// --- Project List View ---

function ProjectList({ onOpenProject }: { onOpenProject: (p: Project) => void }) {
  const { data, isLoading } = useLiteratureReviews();
  const createMutation = useCreateLiteratureReview();
  const deleteMutation = useDeleteLiteratureReview();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const handleCreate = async () => {
    if (!newProjectTitle.trim()) return;
    await createMutation.mutateAsync({
      title: newProjectTitle,
      description: newProjectDesc
    });
    setIsCreateOpen(false);
    setNewProjectTitle('');
    setNewProjectDesc('');
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this project?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const projects = data?.reviews || [];

  return (
    <div className="p-8 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Literature Reviews</h1>
          <p className="text-gray-600 mt-1">Manage your systematic reviews and research projects</p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={() => setIsCreateOpen(true)}>
          <FolderPlus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project: Project) => (
          <div
            key={project.id}
            className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer group relative"
            onClick={() => onOpenProject(project)}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                  <BookOpen className="w-5 h-5" />
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600" onClick={(e) => e.stopPropagation()}>
                      <MoreHorizontal className="w-5 h-5" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent onClick={(e) => e.stopPropagation()}>
                    <DropdownMenuItem className="text-red-600" onClick={(e) => handleDelete(e, project.id)}>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate pr-2">{project.name}</h3>
              <p className="text-sm text-gray-600 line-clamp-2 mb-4 min-h-[40px]">
                {project.description || "No description provided."}
              </p>
              <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
                <span>{project.paperIds?.length || 0} papers</span>
                <span>Updated {new Date(project.updatedAt).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        ))}

        {/* Create New Placeholder */}
        <button
          onClick={() => setIsCreateOpen(true)}
          className="border-2 border-dashed border-gray-300 rounded-xl p-6 flex flex-col items-center justify-center text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors bg-gray-50 hover:bg-white h-[220px]"
        >
          <Plus className="w-8 h-8 mb-3" />
          <span className="font-medium">Create New Project</span>
        </button>
      </div>

      {/* Create Project Modal */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[500px] bg-white p-0 gap-0 overflow-hidden shadow-2xl rounded-2xl border border-gray-100">
          <DialogHeader className="px-6 py-5 border-b border-gray-100 bg-gray-50/50">
            <DialogTitle className="text-lg font-semibold text-gray-900 tracking-tight">Create New Research Project</DialogTitle>
            <p className="text-sm text-gray-500 mt-1">Start a new systematic review or literature analysis.</p>
          </DialogHeader>

          <div className="p-6 space-y-5 bg-white">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 ml-1">Project Name <span className="text-red-500">*</span></label>
              <input
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-gray-400 text-gray-900"
                value={newProjectTitle}
                onChange={(e) => setNewProjectTitle(e.target.value)}
                placeholder="e.g., AI in Healthcare Review"
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 ml-1">Description <span className="text-xs font-normal text-gray-400">(Optional)</span></label>
              <textarea
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-gray-400 text-gray-900 resize-none"
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
                placeholder="Briefly describe the goals of this research..."
                rows={4}
              />
            </div>
          </div>

          <DialogFooter className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setIsCreateOpen(false)}
              className="h-10 px-4 text-gray-600 hover:text-gray-700 border-gray-200 hover:bg-white hover:shadow-sm transition-all"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newProjectTitle.trim()}
              className="h-10 px-6 bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg hover:shadow-indigo-500/20 transition-all disabled:opacity-50 disabled:shadow-none"
            >
              Create Project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// --- Project Workspace ---

function ProjectWorkspace({ project, onBack }: { project: Project, onBack: () => void }) {
  const [activeTab, setActiveTab] = useState<Tab>('summary');
  const [isPaperSelectorOpen, setIsPaperSelectorOpen] = useState(false);
  const updateMutation = useUpdateLiteratureReview();

  // Re-fetch project to get latest paper IDs as they might change
  // Note: We use the list hook which might be stale if we don't invalidate correctly, 
  // or we could implement a single project hook. For now using props but relying on parent re-render.
  // Ideally: const { data: freshProject } = useLiteratureReview(project.id);

  // Combine real papers (if we had a hook to fetch them by ID) with mock fallbacks
  // For this demo, we assume MOCK_PAPERS contains everything or we filter what we can.
  // In a real app, we need `usePapers(project.paperIds)`.
  // Using MOCK_PAPERS filter for now as per instructions.
  /* 
     REPLACED MOCK LOGIC WITH REAL DATA HOOK
     Old: const projectPapers = MOCK_PAPERS.filter(p => project.paperIds?.includes(p.id));
  */
  /* 
     REPLACED MOCK LOGIC WITH REAL DATA HOOK
     Old: const projectPapers = MOCK_PAPERS.filter(p => project.paperIds?.includes(p.id));
  */
  const { data: realProjectPapers = [], refetch: refetchPapers } = useProjectPapers(String(project.id));
  const projectPapers = realProjectPapers;

  // Template/Demo Data Loader
  // Template/Demo Data Loader
  const handleLoadTemplate = async () => {
    try {
      if (!project.id) return;
      const response = await usersApi.seedProject(project.id);

      if (response.status === 'seeded') {
        // Refetch project papers without full page reload
        await refetchPapers();
        // Show success message
        alert('Demo template loaded successfully!');
      }
    } catch (e) {
      console.error("Failed to seed project", e);
      alert('Failed to load template. Please check the console for errors.');
    }
  };

  const handleAddPapers = async (selectedIds: number[]) => {
    // Merge unique IDs
    const currentIds = project.paperIds || [];
    const newIds = Array.from(new Set([...currentIds, ...selectedIds]));

    await updateMutation.mutateAsync({
      id: project.id,
      data: { paperIds: newIds }
    });
    refetchPapers();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 pt-3 pb-0">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <button onClick={onBack} className="hover:text-gray-900">Projects</button>
          <ChevronRight className="w-3 h-3" />
          <span className="text-gray-900 font-medium">{project.name}</span>
        </div>

        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{project.name}</h1>
            <p className="text-xs text-gray-600 mt-0.5">{project.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-8 text-xs">
              <Users className="w-3 h-3 mr-2" />
              Share
            </Button>
            <Button
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 h-8 text-xs"
              onClick={() => setIsPaperSelectorOpen(true)}
            >
              <Plus className="w-3 h-3 mr-2" />
              Add Papers
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-6 overflow-x-auto">
          {[
            { id: 'summary', label: 'Summary Table', icon: LayoutGrid },
            { id: 'methodology', label: 'Methodology Explorer', icon: FlaskConical },
            { id: 'findings', label: 'Findings & Gaps', icon: Target },
            { id: 'comparison', label: 'Comparison', icon: Scale },
            { id: 'synthesis', label: 'Synthesis', icon: FileText },
            { id: 'analysis', label: 'Analysis & Visuals', icon: PieChartIcon },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`flex items-center gap-2.5 pb-3 px-1 text-sm font-medium transition-all border-b-2 whitespace-nowrap ${activeTab === tab.id
                ? 'text-indigo-600 border-indigo-600 bg-indigo-50/10'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50/50'
                }`}
            >
              <tab.icon className={`w-4.5 h-4.5 ${activeTab === tab.id ? 'stroke-[2.5px]' : 'stroke-2'}`} />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto bg-gray-50 p-6">
        {projectPapers.length === 0 && activeTab === 'summary' ? (
          <div className="text-center py-20">
            <h3 className="text-lg font-medium text-gray-900">No papers yet</h3>
            <p className="text-gray-500 mt-2 mb-6">Add papers from your library to start your review.</p>
            <div className="flex items-center justify-center gap-4">
              <Button onClick={() => setIsPaperSelectorOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Papers
              </Button>
              <Button variant="outline" onClick={handleLoadTemplate} title="Adds sample papers for demonstration">
                <BookOpen className="w-4 h-4 mr-2" />
                Load Demo Template
              </Button>
            </div>
          </div>
        ) : (
          <>
            {activeTab === 'summary' && <SummaryView papers={projectPapers} projectId={project.id} />}
            {activeTab === 'methodology' && <MethodologyView papers={projectPapers} projectId={project.id} />}
            {activeTab === 'analysis' && <AnalysisView papers={projectPapers} />}
            {activeTab === 'findings' && <FindingsView papers={projectPapers} projectId={project.id} />}
            {activeTab === 'comparison' && <ComparisonView papers={projectPapers} projectId={project.id} />}
            {activeTab === 'synthesis' && <SynthesisView papers={projectPapers} projectId={project.id} />}
          </>
        )}
      </div>

      <PaperSelector
        isOpen={isPaperSelectorOpen}
        onClose={() => setIsPaperSelectorOpen(false)}
        onSelect={handleAddPapers}
        selectedIds={project.paperIds}
      />
    </div>
  );
}
