import { useState } from 'react';
import { BookOpen, Calendar, Clock, User, ArrowLeft, Tag, TrendingUp, Search, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card, CardDescription, CardHeader, CardTitle } from './ui/card';
import type { View } from '../App';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface BlogProps {
  onNavigate: (view: View) => void;
}

export interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  author: {
    name: string;
    role: string;
    avatar: string;
  };
  category: string;
  tags: string[];
  readTime: number;
  date: string;
  image: string;
  featured?: boolean;
}

const blogPosts: BlogPost[] = [
  {
    id: '1',
    title: 'The Future of AI-Assisted Literature Reviews in Academic Research',
    excerpt: 'Discover how artificial intelligence is revolutionizing the way researchers conduct literature reviews, saving time and uncovering hidden connections between papers.',
    content: `
# The Future of AI-Assisted Literature Reviews in Academic Research

The landscape of academic research is undergoing a profound transformation. As the volume of published research grows exponentially—with over 3 million papers published annually—researchers face an increasingly daunting task: staying current with literature in their field.

## The Challenge of Information Overload

Modern researchers are drowning in information. A typical PhD student must review hundreds, if not thousands, of papers to understand their field adequately. Traditional methods of literature review, while thorough, are becoming unsustainable.

### The Numbers Tell the Story

- **2.5 million** new papers are published each year
- The average researcher reads **23 papers per month**
- Literature reviews can take **3-6 months** for a comprehensive study

## Enter AI-Assisted Research

Artificial intelligence is not replacing researchers—it's augmenting their capabilities. Modern AI tools can:

1. **Automatically categorize and tag papers** based on content
2. **Identify semantic connections** between seemingly unrelated research
3. **Summarize complex papers** into digestible abstracts
4. **Suggest relevant papers** you might have missed

### Real-World Impact

Dr. Sarah Chen, a neuroscience researcher at MIT, reported: "AI tools cut my literature review time by 60%. More importantly, the AI surfaced connections I would have never found manually."

## Best Practices for AI-Assisted Reviews

While AI is powerful, it works best when combined with human expertise:

- **Use AI for discovery**, but validate findings yourself
- **Combine multiple sources**: arXiv, Semantic Scholar, OpenAlex
- **Keep human judgment central** to your research process
- **Document your methodology** for transparency

## The Road Ahead

The integration of AI in academic research is still in its early stages. Future developments we're excited about include:

- **Multi-modal understanding** of figures, tables, and equations
- **Real-time collaboration** between AI and researchers
- **Automated hypothesis generation** based on literature gaps
- **Cross-language research synthesis**

## Conclusion

AI-assisted literature reviews represent a paradigm shift in how we conduct research. By embracing these tools thoughtfully, researchers can focus more on innovation and less on information management.

The future of research is collaborative—between human creativity and AI capability.
    `,
    author: {
      name: 'Dr. Emily Rodriguez',
      role: 'Research Scientist, Stanford AI Lab',
      avatar: 'researcher-woman'
    },
    category: 'AI & Research',
    tags: ['AI', 'Literature Review', 'Research Methods', 'Machine Learning'],
    readTime: 8,
    date: '2025-11-10',
    image: 'ai technology',
    featured: true
  },
  {
    id: '2',
    title: '10 Essential Tips for Conducting Systematic Literature Reviews',
    excerpt: 'Master the art of systematic literature reviews with these expert-backed strategies that will transform your research workflow.',
    content: `
# 10 Essential Tips for Conducting Systematic Literature Reviews

A systematic literature review is the cornerstone of quality research. Here's how to do it right.

## 1. Define Clear Research Questions

Start with PICO (Population, Intervention, Comparison, Outcome) framework:
- **Population**: Who are you studying?
- **Intervention**: What are you investigating?
- **Comparison**: What are you comparing against?
- **Outcome**: What do you hope to find?

## 2. Develop a Comprehensive Search Strategy

Use boolean operators effectively:
- AND to narrow searches
- OR to broaden searches
- NOT to exclude irrelevant results

## 3. Document Everything

Create a research log that includes:
- Search terms used
- Databases searched
- Date of search
- Number of results
- Inclusion/exclusion criteria

## 4. Use Multiple Databases

Don't rely on a single source. Essential databases include:
- arXiv for preprints
- Semantic Scholar for cross-disciplinary research
- OpenAlex for comprehensive coverage
- PubMed for medical research
- IEEE Xplore for engineering

## 5. Screen Papers Systematically

Use a two-stage process:
1. **Title and abstract screening** (first pass)
2. **Full-text review** (second pass)

## 6. Assess Quality Rigorously

Evaluate papers based on:
- Methodology soundness
- Sample size and selection
- Statistical analysis
- Potential biases
- Reproducibility

## 7. Extract Data Consistently

Create a standardized form for:
- Study characteristics
- Participant demographics
- Interventions and outcomes
- Key findings
- Limitations

## 8. Synthesize Findings

Look for:
- Common themes
- Contradictions
- Knowledge gaps
- Emerging trends

## 9. Use Citation Management Tools

Essential features to look for:
- PDF organization
- Automatic metadata extraction
- Multiple citation formats
- Collaboration capabilities

## 10. Stay Current

Literature reviews aren't one-time events:
- Set up citation alerts
- Follow key authors
- Join research communities
- Revisit your review quarterly

## Conclusion

Systematic literature reviews require discipline, but the payoff is worth it. These practices will help you conduct thorough, reproducible research that stands up to scrutiny.

Remember: quality over quantity. A well-conducted review of 50 highly relevant papers is more valuable than a superficial review of 500.
    `,
    author: {
      name: 'Prof. James Martinez',
      role: 'Director of Research Methods, Oxford University',
      avatar: 'professor-man'
    },
    category: 'Research Methods',
    tags: ['Literature Review', 'Research Methods', 'Systematic Review', 'Best Practices'],
    readTime: 12,
    date: '2025-11-08',
    image: 'library books',
    featured: true
  },
  {
    id: '3',
    title: 'Citation Management in 2025: APA, MLA, Chicago, and Beyond',
    excerpt: 'Navigate the complexities of modern citation formats with confidence. Learn when and how to use different citation styles effectively.',
    content: `
# Citation Management in 2025: APA, MLA, Chicago, and Beyond

Citations are more than just academic formality—they're the foundation of scholarly discourse.

## Why Citation Formats Matter

Different disciplines have different needs:
- **APA**: Psychology, education, social sciences
- **MLA**: Humanities, literature, arts
- **Chicago**: History, business, fine arts
- **IEEE**: Engineering, computer science

## APA 7th Edition: Key Updates

Recent changes include:
- Up to 20 authors listed (previously 7)
- DOIs formatted as URLs
- Simplified in-text citations for 3+ authors
- New guidelines for social media citations

### Example:
\`\`\`
Smith, J., & Jones, M. (2025). Machine learning in research. 
Journal of AI Studies, 15(3), 234-250. 
https://doi.org/10.1234/jas.2025.234
\`\`\`

## MLA 9th Edition: Modern Updates

Focus on flexibility:
- Core elements approach
- Emphasis on digital sources
- Containers concept for complex sources

### Example:
\`\`\`
Smith, John, and Mary Jones. "Machine Learning in Research." 
Journal of AI Studies, vol. 15, no. 3, 2025, pp. 234-250.
\`\`\`

## Chicago Manual of Style 17th Edition

Two documentation systems:
1. **Notes-Bibliography**: Humanities
2. **Author-Date**: Sciences

### Notes-Bibliography Example:
\`\`\`
1. John Smith and Mary Jones, "Machine Learning in Research," 
Journal of AI Studies 15, no. 3 (2025): 234-250.
\`\`\`

## IEEE Citation Style

Numbered references:
\`\`\`
[1] J. Smith and M. Jones, "Machine learning in research," 
J. AI Studies, vol. 15, no. 3, pp. 234-250, 2025.
\`\`\`

## Best Practices Across All Formats

1. **Use citation management software**: Zotero, Mendeley, EndNote
2. **Verify automatically generated citations**
3. **Keep your citation library organized**
4. **Update citations when format guidelines change**
5. **Be consistent throughout your document**

## Common Citation Mistakes to Avoid

- Mixing citation styles
- Incomplete author information
- Missing DOIs or URLs
- Incorrect date formats
- Outdated format guidelines

## Digital Sources: Special Considerations

Modern research includes diverse sources:
- Preprints and working papers
- Datasets and code repositories
- Social media posts
- Podcasts and videos
- Blog posts and websites

Each requires specific citation elements.

## The Future of Citations

Emerging trends:
- **Persistent identifiers**: ORCIDs for authors, DOIs for papers
- **Machine-readable citations**: RIS, BibTeX formats
- **Dynamic citations**: Linking to latest versions
- **Credit taxonomy**: CRediT contributor roles

## Conclusion

Master citation management early in your research career. The right tools and knowledge will save you countless hours and prevent headaches during manuscript preparation.

Remember: citations acknowledge intellectual debt and enable reproducibility. Take them seriously.
    `,
    author: {
      name: 'Dr. Lisa Patel',
      role: 'Academic Writing Specialist, Harvard University',
      avatar: 'academic-woman'
    },
    category: 'Research Methods',
    tags: ['Citations', 'Academic Writing', 'APA', 'MLA', 'Chicago', 'IEEE'],
    readTime: 10,
    date: '2025-11-05',
    image: 'writing desk'
  },
  {
    id: '4',
    title: 'Open Access Revolution: What It Means for Researchers',
    excerpt: 'The shift to open access publishing is transforming academic research. Understand the implications for your work and career.',
    content: `
# Open Access Revolution: What It Means for Researchers

Open access is reshaping how research is published, shared, and consumed.

## What Is Open Access?

Open access (OA) means research is freely available online, without subscription barriers.

### Types of Open Access

1. **Gold OA**: Published in OA journals
2. **Green OA**: Self-archived in repositories
3. **Hybrid**: OA option in subscription journals
4. **Diamond OA**: Free for readers AND authors

## The Business Case

Traditional publishing:
- Average article processing charge: $3,000
- Subscription costs rising 5-7% annually
- Library budgets stagnant

Open access benefits:
- Wider readership (up to 3x more citations)
- Faster dissemination
- Greater impact
- Public access to publicly funded research

## Major Initiatives

### Plan S
European mandate requiring OA for publicly funded research by 2025.

### NIH Public Access Policy
Research funded by NIH must be freely available within 12 months.

### UNESCO Recommendation
Global framework for open science and open access.

## Navigating OA as a Researcher

### Finding OA Journals

Quality indicators:
- Listed in DOAJ (Directory of Open Access Journals)
- Impact factor
- Editorial board reputation
- Indexing in major databases

### Avoiding Predatory Publishers

Warning signs:
- Aggressive email solicitation
- Rapid review promises (< 2 weeks)
- Unknown editorial board
- Poor website quality
- Not indexed in reputable databases

### Funding APCs

Options for covering article processing charges:
- Grant budgets
- Institutional OA funds
- Employer support
- Waiver programs

## Preprints: The Fast Track

Benefits of preprints:
- Immediate dissemination
- Establish priority
- Get early feedback
- Free to post

Major preprint servers:
- arXiv (physics, math, CS)
- bioRxiv (biology)
- medRxiv (medicine)
- SSRN (social sciences)

## Rights and Licensing

Understanding Creative Commons:
- **CC-BY**: Most permissive, attribution only
- **CC-BY-SA**: Share-alike requirement
- **CC-BY-NC**: Non-commercial only
- **CC-BY-ND**: No derivatives

## Impact on Academic Careers

OA considerations for:
- **Graduate students**: Build public profile
- **Postdocs**: Maximize citation impact
- **Faculty**: Meet funder requirements
- **Senior researchers**: Lead cultural change

## The Future

Trends to watch:
- Institutional OA mandates
- Publishing reform movements
- Alternative peer review models
- Decentralized publishing platforms

## Conclusion

Open access isn't just about free content—it's about accelerating discovery, enabling collaboration, and democratizing knowledge.

As researchers, we have both opportunities and responsibilities in this new landscape.
    `,
    author: {
      name: 'Dr. Michael Chen',
      role: 'Director, Open Science Initiative',
      avatar: 'scientist-man'
    },
    category: 'Publishing',
    tags: ['Open Access', 'Publishing', 'Academic Career', 'Research Impact'],
    readTime: 9,
    date: '2025-11-01',
    image: 'library open'
  },
  {
    id: '5',
    title: 'Effective Note-Taking Strategies for Academic Research',
    excerpt: 'Transform how you capture and organize research notes with these proven strategies used by top researchers worldwide.',
    content: `
# Effective Note-Taking Strategies for Academic Research

Great research starts with great notes. Here's how to build a note-taking system that actually works.

## The Zettelkasten Method

Also known as the "slip-box" method, used by prolific sociologist Niklas Luhmann.

### Core Principles

1. **Atomic notes**: One idea per note
2. **Link extensively**: Connect related ideas
3. **Write in your own words**: Force understanding
4. **Build a web of knowledge**: Not just a collection

### Digital Implementation

Modern tools that support Zettelkasten:
- Obsidian
- Roam Research
- Notion
- RemNote

## The Cornell Method

Divide notes into three sections:
- **Cues** (left): Key questions and keywords
- **Notes** (right): Main content
- **Summary** (bottom): Synthesis

Perfect for lecture notes and paper summaries.

## Mind Mapping for Literature Reviews

Visual organization benefits:
- See relationships at a glance
- Identify knowledge clusters
- Spot research gaps
- Generate new hypotheses

Tools:
- XMind
- MindMeister
- Coggle

## Progressive Summarization

Tiago Forte's method:
1. **Layer 1**: Original text
2. **Layer 2**: Bold key passages
3. **Layer 3**: Highlight critical points
4. **Layer 4**: Create executive summary

## Annotation Best Practices

### Color Coding System

Example scheme:
- 🔴 Red: Critical findings
- 🟡 Yellow: Key methodology
- 🔵 Blue: Interesting tangents
- 🟢 Green: Definitions

### Marginal Notes

Include:
- Questions
- Connections to other work
- Criticisms
- Applications

## Organizing Literature Notes

### Folder Structure

\`\`\`
Research/
├── Inbox/
├── Papers/
│   ├── To Read/
│   ├── Reading/
│   └── Read/
├── Notes/
│   ├── Permanent/
│   ├── Literature/
│   └── Fleeting/
└── Writing/
\`\`\`

### Tagging Strategy

Multi-dimensional tags:
- **Topic**: #machinelearning, #neuroscience
- **Type**: #methodology, #review, #empirical
- **Status**: #toread, #reading, #done
- **Quality**: #foundational, #useful, #interesting

## Creating Synthesis Notes

After reading 5-10 papers on a topic:
1. Identify common themes
2. Note contradictions
3. Assess methodology differences
4. Synthesize key insights

## Digital vs. Analog Notes

### Digital Advantages
- Searchability
- Easy editing
- Cloud backup
- Linking capability

### Analog Advantages
- Better retention
- Fewer distractions
- Spatial memory
- Tactile engagement

### Hybrid Approach
- Read and annotate on paper
- Transfer key insights digitally
- Use digital for organization and search
- Use analog for deep thinking

## Note Templates

### Paper Summary Template

\`\`\`markdown
# [Paper Title]

**Authors**: 
**Year**: 
**Source**: 
**Tags**: 

## Research Question

## Methodology

## Key Findings

## Limitations

## My Thoughts

## Connections

## Citations
\`\`\`

## Maintenance and Review

Weekly routine:
- Process fleeting notes
- Update permanent notes
- Create new connections
- Archive completed projects

Monthly routine:
- Review orphan notes
- Strengthen weak connections
- Update folder structure
- Export backups

## Common Pitfalls

Avoid:
- ❌ Highlighting without processing
- ❌ Creating notes you never revisit
- ❌ Over-organizing instead of thinking
- ❌ Copying without understanding

Embrace:
- ✅ Writing to think
- ✅ Building connections
- ✅ Regular review
- ✅ Simple systems

## Conclusion

Your note-taking system is personal. Experiment with these methods, keep what works, and discard what doesn't.

The goal isn't perfect notes—it's a thinking environment that helps you do better research.
    `,
    author: {
      name: 'Prof. Anna Kowalski',
      role: 'Research Methodology Expert, Cambridge',
      avatar: 'professor-woman'
    },
    category: 'Research Methods',
    tags: ['Note-Taking', 'Productivity', 'Research Methods', 'Knowledge Management'],
    readTime: 11,
    date: '2025-10-28',
    image: 'notebook coffee'
  },
  {
    id: '6',
    title: 'Cross-Disciplinary Research: Bridging the Gap Between Fields',
    excerpt: 'The most exciting discoveries happen at the intersection of disciplines. Learn how to conduct effective cross-disciplinary research.',
    content: `
# Cross-Disciplinary Research: Bridging the Gap Between Fields

Innovation increasingly happens at disciplinary boundaries. Here's how to navigate cross-disciplinary research successfully.

## Why Cross-Disciplinary Research Matters

The biggest challenges facing humanity don't fit neatly into disciplines:
- Climate change needs physics, economics, politics, and social science
- AI ethics requires computer science, philosophy, law, and psychology
- Healthcare innovation blends medicine, engineering, data science, and policy

## Challenges of Cross-Disciplinary Work

### Language Barriers

Every field has jargon:
- Same word, different meanings
- Concept exists in one field, unnamed in another
- Methodological assumptions differ

### Solution

Create a shared glossary and be explicit about definitions.

### Different Methodological Standards

- Qualitative vs. quantitative traditions
- Statistical rigor expectations
- Sample size norms
- Publication timelines

### Solution

Discuss methodologies early and explicitly.

### Evaluation and Recognition

Challenges:
- Peer reviewers may not understand cross-disciplinary work
- Tenure committees favor traditional research
- Journals are often discipline-specific

### Solution

- Target interdisciplinary journals
- Document your unique contribution
- Build diverse support networks

## Building Cross-Disciplinary Collaborations

### Finding Collaborators

Where to look:
- Interdisciplinary research centers
- Conferences with diverse audiences
- Online research communities
- Social media (Academic Twitter/X)

### Successful Collaboration Practices

1. **Establish shared goals early**
2. **Respect different expertise**
3. **Communicate frequently**
4. **Co-create research questions**
5. **Share authorship fairly**

## Literature Review Strategies

### Challenge

How do you review literature across multiple fields?

### Strategy

1. **Start broad**: Read overview articles and reviews
2. **Identify key concepts**: What are the foundational ideas?
3. **Find bridges**: Look for papers that cite multiple fields
4. **Use different databases**: Each field has preferred repositories
5. **Follow citation trails**: Papers that cross boundaries

## Developing Cross-Disciplinary Expertise

### T-Shaped Knowledge

- **Depth**: Deep expertise in your home discipline
- **Breadth**: Working knowledge of adjacent fields

### Learning Pathways

- Audit courses in other departments
- Attend seminars outside your field
- Read foundational texts
- Participate in reading groups

## Communicating Cross-Disciplinary Research

### Writing for Multiple Audiences

Tips:
- Define technical terms
- Provide context for field-specific norms
- Use accessible examples
- Explicitly state your contribution to each field

### Visualizations

Good visuals transcend disciplinary boundaries:
- Conceptual diagrams
- Process maps
- Data visualizations
- Infographics

## Funding Cross-Disciplinary Research

Funding sources:
- NSF's Convergence Research program
- EU Horizon Europe clusters
- Wellcome Trust interdisciplinary awards
- Foundation grants

Grant writing tips:
- Highlight unique insights from combination
- Show need for multiple disciplines
- Demonstrate team complementarity
- Address potential challenges

## Case Studies

### Success Story 1: Computational Social Science

Merged:
- Computer science (algorithms, data)
- Social science (theories, questions)
- Statistics (methods)

Result: New insights into human behavior at scale.

### Success Story 2: Bioengineering

Merged:
- Biology (understanding life)
- Engineering (building solutions)
- Medicine (clinical applications)

Result: Artificial organs, prosthetics, drug delivery systems.

## The Future

Trends accelerating cross-disciplinary work:
- Complex global challenges
- Big data requiring diverse expertise
- Team science initiatives
- Funding agency priorities

## Practical Steps to Get Started

1. **Identify a problem** that interests you across disciplines
2. **Read broadly** in adjacent fields
3. **Attend** cross-disciplinary conferences
4. **Reach out** to potential collaborators
5. **Start small**: A pilot project or paper
6. **Be patient**: Building expertise takes time

## Conclusion

Cross-disciplinary research is challenging but rewarding. The insights gained from combining different perspectives often lead to breakthrough discoveries.

Don't be afraid to step outside your comfort zone. The future of research is collaborative, creative, and cross-disciplinary.
    `,
    author: {
      name: 'Dr. David Thompson',
      role: 'Director, Institute for Interdisciplinary Research',
      avatar: 'researcher-man'
    },
    category: 'Research Methods',
    tags: ['Interdisciplinary', 'Collaboration', 'Research Methods', 'Innovation'],
    readTime: 13,
    date: '2025-10-25',
    image: 'team collaboration'
  }
];

const categories = ['All', 'AI & Research', 'Research Methods', 'Publishing', 'Productivity'];

export default function Blog({ onNavigate }: BlogProps) {
  const [selectedPost, setSelectedPost] = useState<BlogPost | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredPosts = blogPosts.filter(post => {
    const matchesCategory = selectedCategory === 'All' || post.category === selectedCategory;
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const featuredPosts = blogPosts.filter(post => post.featured);

  if (selectedPost) {
    return (
      <div className="min-h-screen bg-white">
        {/* Header */}
        <header className="border-b px-6 py-4 flex items-center justify-between bg-white sticky top-0 z-50 shadow-sm">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSelectedPost(null)}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <BookOpen className="w-6 h-6 text-blue-600" />
              <span className="text-xl">ResearchHub Blog</span>
            </div>
          </div>

          <Button onClick={() => onNavigate('search')}>
            Back to Home
          </Button>
        </header>

        {/* Article Content */}
        <article className="max-w-4xl mx-auto px-6 py-12">
          {/* Category Badge */}
          <Badge className="mb-4">{selectedPost.category}</Badge>

          {/* Title */}
          <h1 className="text-5xl mb-6">{selectedPost.title}</h1>

          {/* Meta Information */}
          <div className="flex items-center gap-6 mb-8 text-gray-600">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4" />
              <span>{selectedPost.author.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>{new Date(selectedPost.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>{selectedPost.readTime} min read</span>
            </div>
          </div>

          {/* Featured Image */}
          <div className="mb-8 rounded-xl overflow-hidden">
            <ImageWithFallback
              src={`https://source.unsplash.com/1200x600/?${encodeURIComponent(selectedPost.image)}`}
              alt={selectedPost.title}
              className="w-full h-96 object-cover"
            />
          </div>

          {/* Article Body */}
          <div className="prose prose-lg max-w-none">
            {selectedPost.content.split('\n').map((paragraph, index) => {
              if (paragraph.startsWith('# ')) {
                return <h1 key={index} className="text-4xl mt-12 mb-6">{paragraph.substring(2)}</h1>;
              } else if (paragraph.startsWith('## ')) {
                return <h2 key={index} className="text-3xl mt-10 mb-4">{paragraph.substring(3)}</h2>;
              } else if (paragraph.startsWith('### ')) {
                return <h3 key={index} className="text-2xl mt-8 mb-3">{paragraph.substring(4)}</h3>;
              } else if (paragraph.startsWith('- ') || paragraph.startsWith('* ')) {
                return (
                  <li key={index} className="ml-6 mb-2">
                    {paragraph.substring(2)}
                  </li>
                );
              } else if (paragraph.startsWith('```')) {
                return null; // Handle code blocks separately
              } else if (paragraph.trim()) {
                return <p key={index} className="mb-4 leading-relaxed text-gray-700">{paragraph}</p>;
              }
              return <br key={index} />;
            })}
          </div>

          {/* Tags */}
          <div className="mt-12 pt-8 border-t">
            <div className="flex items-center gap-2 flex-wrap">
              <Tag className="w-4 h-4 text-gray-600" />
              {selectedPost.tags.map(tag => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
          </div>

          {/* Author Info */}
          <div className="mt-8 p-6 bg-gray-50 rounded-xl">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xl">
                {selectedPost.author.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div>
                <div className="font-semibold text-lg">{selectedPost.author.name}</div>
                <div className="text-gray-600">{selectedPost.author.role}</div>
              </div>
            </div>
          </div>

          {/* Related Articles */}
          <div className="mt-12">
            <h3 className="text-2xl mb-6">Related Articles</h3>
            <div className="grid gap-6">
              {blogPosts
                .filter(post =>
                  post.id !== selectedPost.id &&
                  (post.category === selectedPost.category ||
                    post.tags.some(tag => selectedPost.tags.includes(tag)))
                )
                .slice(0, 3)
                .map(post => (
                  <Card
                    key={post.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => setSelectedPost(post)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <CardTitle className="text-xl mb-2">{post.title}</CardTitle>
                          <CardDescription>{post.excerpt}</CardDescription>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0 mt-1" />
                      </div>
                    </CardHeader>
                  </Card>
                ))}
            </div>
          </div>
        </article>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b px-6 py-4 flex items-center justify-between bg-white sticky top-0 z-50 shadow-sm">
        <div className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-blue-600" />
          <span className="text-xl">ResearchHub Blog</span>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => onNavigate('search')}>
            Home
          </Button>
          <Button onClick={() => onNavigate('workspace')}>
            My Workspace
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-50 via-white to-purple-50 border-b">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="text-center mb-8">
            <h1 className="text-5xl mb-4">ResearchHub Blog</h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Insights, tips, and best practices for modern academic research
            </p>
          </div>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-8">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-12 py-6 text-lg"
              />
            </div>
          </div>

          {/* Categories */}
          <div className="flex justify-center gap-2 flex-wrap">
            {categories.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-full transition-all ${selectedCategory === category
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                  }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Featured Articles */}
        {selectedCategory === 'All' && !searchQuery && (
          <div className="mb-16">
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <h2 className="text-3xl">Featured Articles</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-8">
              {featuredPosts.map(post => (
                <Card
                  key={post.id}
                  className="overflow-hidden cursor-pointer hover:shadow-xl transition-shadow group"
                  onClick={() => setSelectedPost(post)}
                >
                  <div className="relative h-64 overflow-hidden">
                    <ImageWithFallback
                      src={`https://source.unsplash.com/800x600/?${encodeURIComponent(post.image)}`}
                      alt={post.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-4 left-4">
                      <Badge className="bg-white text-blue-600 hover:bg-white">
                        {post.category}
                      </Badge>
                    </div>
                  </div>
                  <CardHeader>
                    <CardTitle className="text-2xl mb-3 group-hover:text-blue-600 transition-colors">
                      {post.title}
                    </CardTitle>
                    <CardDescription className="text-base mb-4">
                      {post.excerpt}
                    </CardDescription>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        <span>{post.author.name}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{post.readTime} min</span>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* All Articles */}
        <div>
          <h2 className="text-3xl mb-6">
            {searchQuery ? 'Search Results' : selectedCategory === 'All' ? 'Recent Articles' : selectedCategory}
          </h2>

          {filteredPosts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 text-lg">No articles found matching your criteria.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-8">
              {filteredPosts.map(post => (
                <Card
                  key={post.id}
                  className="overflow-hidden cursor-pointer hover:shadow-xl transition-shadow group flex flex-col"
                  onClick={() => setSelectedPost(post)}
                >
                  <div className="relative h-48 overflow-hidden">
                    <ImageWithFallback
                      src={`https://source.unsplash.com/600x400/?${encodeURIComponent(post.image)}`}
                      alt={post.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                  <CardHeader className="flex-1 flex flex-col">
                    <div className="mb-3">
                      <Badge variant="secondary" className="mb-2">
                        {post.category}
                      </Badge>
                    </div>
                    <CardTitle className="text-xl mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                      {post.title}
                    </CardTitle>
                    <CardDescription className="mb-4 line-clamp-3 flex-1">
                      {post.excerpt}
                    </CardDescription>
                    <div className="flex items-center justify-between text-sm text-gray-600 pt-4 border-t">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(post.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{post.readTime} min</span>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Newsletter Section */}
      <div className="bg-gradient-to-br from-blue-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto px-6 py-16 text-center">
          <h2 className="text-4xl mb-4">Stay Updated</h2>
          <p className="text-xl mb-8 text-blue-100">
            Get the latest research insights and tips delivered to your inbox
          </p>
          <div className="flex gap-3 max-w-md mx-auto">
            <Input
              type="email"
              placeholder="Enter your email"
              className="bg-white text-gray-900"
            />
            <Button className="bg-white text-blue-600 hover:bg-gray-100">
              Subscribe
            </Button>
          </div>
          <p className="text-sm text-blue-100 mt-4">
            Join 10,000+ researchers. Unsubscribe anytime.
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t px-6 py-8 bg-gray-50">
        <div className="max-w-6xl mx-auto text-center text-sm text-gray-600">
          © 2025 ResearchHub. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
