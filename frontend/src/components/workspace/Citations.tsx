import { useState } from 'react';
import {
  Quote,
  Copy,
  Download,
  FileText,
  Link as LinkIcon,
  Check
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { toast } from 'sonner';
import type { Paper } from '../../App';

interface CitationsProps {
  papers: Paper[];
}

export default function Citations({ papers }: CitationsProps) {
  const [citationStyle, setCitationStyle] = useState<'APA' | 'MLA' | 'Chicago' | 'IEEE'>('APA');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Generate citation based on style
  const generateCitation = (paper: Paper, style: string): string => {
    const authors = paper.authors.slice(0, 3).join(', ');
    const moreAuthors = paper.authors.length > 3 ? ' et al.' : '';

    switch (style) {
      case 'APA':
        return `${authors}${moreAuthors} (${paper.year}). ${paper.title}. ${paper.venue || 'Unpublished'}. ${paper.doi ? `https://doi.org/${paper.doi}` : ''}`;
      case 'MLA':
        return `${authors}${moreAuthors}. "${paper.title}." ${paper.venue || 'Unpublished'}, ${paper.year}.`;
      case 'Chicago':
        return `${authors}${moreAuthors}. "${paper.title}." ${paper.venue || 'Unpublished'} (${paper.year}).`;
      case 'IEEE':
        return `${authors}${moreAuthors}, "${paper.title}," ${paper.venue || 'Unpublished'}, ${paper.year}.`;
      default:
        return `${authors}${moreAuthors} (${paper.year}). ${paper.title}.`;
    }
  };

  const copyCitation = (paperId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(paperId);
    setTimeout(() => setCopiedId(null), 2000);
    toast.success('Copied to clipboard');
  };

  const exportReferences = (format: 'txt' | 'bibtex' | 'ris') => {
    let content = '';
    let filename = '';

    if (format === 'txt') {
      content = papers.map(paper => generateCitation(paper, citationStyle)).join('\n\n');
      filename = `references-${citationStyle.toLowerCase()}.txt`;
    } else if (format === 'bibtex') {
      content = papers.map(paper => {
        const key = `${paper.authors[0]?.split(' ').pop()}${paper.year}`;
        return `@article{${key},\n  title={${paper.title}},\n  author={${paper.authors.join(' and ')}},\n  year={${paper.year}},\n  journal={${paper.venue || 'Unpublished'}}\n}`;
      }).join('\n\n');
      filename = 'references.bib';
    } else if (format === 'ris') {
      content = papers.map(paper => {
        return `TY  - JOUR\nTI  - ${paper.title}\nAU  - ${paper.authors.join('\nAU  - ')}\nPY  - ${paper.year}\nER  - `;
      }).join('\n\n');
      filename = 'references.ris';
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    toast.success(`Exported as ${format.toUpperCase()}`);
  };

  const filteredPapers = papers.filter(paper =>
    searchQuery === '' ||
    paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.authors.some(author => author.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Quote className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg">Citations & References</h2>
          </div>
          <Badge variant="secondary">{papers.length} papers</Badge>
        </div>

        <div className="flex items-center gap-2">
          <Select value={citationStyle} onValueChange={(v) => setCitationStyle(v as typeof citationStyle)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="APA">APA 7th</SelectItem>
              <SelectItem value="MLA">MLA 9th</SelectItem>
              <SelectItem value="Chicago">Chicago</SelectItem>
              <SelectItem value="IEEE">IEEE</SelectItem>
            </SelectContent>
          </Select>

          <Input
            placeholder="Search papers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1"
          />
        </div>
      </div>

      <Tabs defaultValue="formatted" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-2">
          <TabsTrigger value="formatted">Formatted Citations</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        {/* Formatted Citations Tab */}
        <TabsContent value="formatted" className="flex-1 overflow-y-auto p-4 mt-0">
          {filteredPapers.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Quote className="w-12 h-12 mb-3" />
              <p className="text-center">No papers found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredPapers.map((paper) => (
                <Card key={paper.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="mb-3">
                    <h3 className="text-sm mb-1">{paper.title}</h3>
                    <p className="text-xs text-gray-500">
                      {paper.authors.slice(0, 3).join(', ')}
                      {paper.authors.length > 3 ? ' et al.' : ''} • {paper.year}
                    </p>
                  </div>

                  <div className="bg-gray-50 p-3 rounded text-sm mb-3 font-mono text-xs">
                    {generateCitation(paper, citationStyle)}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyCitation(paper.id, generateCitation(paper, citationStyle))}
                    >
                      {copiedId === paper.id ? (
                        <>
                          <Check className="w-3 h-3 mr-1" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3 mr-1" />
                          Copy
                        </>
                      )}
                    </Button>

                    {paper.doi && (
                      <Badge variant="outline" className="text-xs">
                        DOI: {paper.doi}
                      </Badge>
                    )}

                    <Badge variant="outline" className="text-xs ml-auto">
                      {paper.citations} citations
                    </Badge>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export" className="flex-1 overflow-y-auto p-4 mt-0">
          <div className="space-y-4">
            <div>
              <h3 className="mb-3">Export All References</h3>
              <p className="text-sm text-gray-600 mb-4">
                Export all {papers.length} papers in various formats
              </p>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => exportReferences('txt')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Export as Text ({citationStyle})
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => exportReferences('bibtex')}
                >
                  <LinkIcon className="w-4 h-4 mr-2" />
                  Export as BibTeX
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => exportReferences('ris')}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export as RIS
                </Button>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="mb-3">Citation Style Preview</h3>
              <div className="space-y-3">
                {['APA', 'MLA', 'Chicago', 'IEEE'].map(style => {
                  const samplePaper = papers[0];
                  if (!samplePaper) return null;

                  return (
                    <Card key={style} className="p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant={citationStyle === style ? "default" : "outline"}>
                          {style}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600 font-mono">
                        {generateCitation(samplePaper, style)}
                      </p>
                    </Card>
                  );
                })}
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="mb-3">Quick Reference</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div>
                  <p className="font-medium text-gray-900">APA 7th Edition</p>
                  <p className="text-xs">Author, A. A. (Year). Title. Journal, volume(issue), pages.</p>
                </div>
                <div>
                  <p className="font-medium text-gray-900">MLA 9th Edition</p>
                  <p className="text-xs">Author. "Title." Journal, vol. #, no. #, Year, pp. #-#.</p>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Chicago Style</p>
                  <p className="text-xs">Author. "Title." Journal # (Year): pages.</p>
                </div>
                <div>
                  <p className="font-medium text-gray-900">IEEE Style</p>
                  <p className="text-xs">A. Author, "Title," Journal, vol. #, pp. #-#, Year.</p>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

