# Blog Platform Feature
## User-Generated Content for SEO & Community Growth

**Purpose:** Allow users to write and share blog posts about research tips, app tutorials, and academic advice. This helps with:
- **SEO** - Rank for keywords like "how to search research papers"
- **AI Search** - Show up in ChatGPT, Perplexity searches
- **Community** - Build engaged user base
- **Growth** - Organic traffic from Google

**Timeline:** Week 7-8 (28 hours)  
**Cost:** $0 (just database storage)  
**Impact:** HIGH - Major growth driver

---

## 📊 **Database Schema**

```sql
-- Blog posts table
CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    author_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    
    -- Content
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(250) UNIQUE NOT NULL,  -- SEO-friendly URL
    excerpt VARCHAR(500),  -- Preview text
    content TEXT NOT NULL,  -- Markdown content
    cover_image_url VARCHAR(500),
    
    -- SEO
    meta_title VARCHAR(60),  -- Google title
    meta_description VARCHAR(160),  -- Google description
    keywords JSONB,  -- ["research", "papers", "tips"]
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, published, archived
    is_featured BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    
    -- Engagement
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    -- Categories
    category VARCHAR(50),  -- tutorial, tips, feature, research
    tags JSONB  -- ["beginner", "advanced", "ai"]
);

-- Indexes for performance
CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_author ON blog_posts(author_id);
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_published ON blog_posts(published_at DESC);
CREATE INDEX idx_blog_posts_category ON blog_posts(category);
CREATE INDEX idx_blog_posts_tags ON blog_posts USING GIN(tags);

-- Comments table
CREATE TABLE blog_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    parent_id INTEGER REFERENCES blog_comments(id),  -- For nested comments
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_blog_comments_post ON blog_comments(post_id);
CREATE INDEX idx_blog_comments_user ON blog_comments(user_id);
CREATE INDEX idx_blog_comments_parent ON blog_comments(parent_id);

-- Likes table
CREATE TABLE blog_likes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, user_id)  -- One like per user per post
);

CREATE INDEX idx_blog_likes_post ON blog_likes(post_id);
CREATE INDEX idx_blog_likes_user ON blog_likes(user_id);
```

---

## 🎯 **SEO Strategy**

### **URL Structure**
```
✅ Good: yourapp.com/blog/how-to-search-research-papers
❌ Bad: yourapp.com/blog/post/123
```

### **Target Keywords** (High Volume)
1. "how to search research papers" (5,400/month)
2. "how to find research papers" (2,900/month)
3. "how to write literature review" (8,100/month)
4. "academic search engines" (1,600/month)
5. "citation management tools" (1,300/month)
6. "how to read scientific papers" (2,400/month)
7. "research paper database" (880/month)
8. "free academic papers" (1,900/month)

### **Content Categories**
- **Tutorials** - "How to write a literature review in 5 steps"
- **Tips & Tricks** - "10 advanced search operators for research"
- **Feature Guides** - "Using AI to summarize papers"
- **Research Methods** - "How to read a scientific paper effectively"
- **App Updates** - "New features in version 2.0"

### **SEO Checklist**
- [ ] Unique meta title (50-60 chars)
- [ ] Compelling meta description (150-160 chars)
- [ ] H1 tag (title)
- [ ] H2/H3 subheadings
- [ ] Internal links to papers
- [ ] External links to authoritative sources
- [ ] Alt text for images
- [ ] Sitemap.xml
- [ ] RSS feed
- [ ] Open Graph tags (social sharing)
- [ ] Schema.org markup (Article)

---

## 📝 **Example Blog Posts** (for Launch)

### **Post 1: "How to Find Research Papers on Any Topic (2025 Guide)"**
**Target:** "how to find research papers" (2,900/month)
**Outline:**
1. Introduction - Why finding papers is hard
2. Best academic search engines (link to your app!)
3. Advanced search techniques
4. Using AI tools (your app's features)
5. Organizing your research
6. Conclusion + CTA

### **Post 2: "10 Best Academic Search Engines for Researchers"**
**Target:** "academic search engines" (1,600/month)
**Outline:**
1. Google Scholar
2. PubMed
3. arXiv
4. **Your App** (featured!)
5. Semantic Scholar
6. CORE
7. BASE
8. OpenAlex
9. Dimensions
10. Comparison table

### **Post 3: "How to Write a Literature Review in 5 Steps"**
**Target:** "how to write literature review" (8,100/month)
**Outline:**
1. Define your research question
2. Search for relevant papers (use your app!)
3. Evaluate and select papers
4. Organize papers by themes
5. Write and cite properly
6. Use your app's document generator!

---

## 💻 **Implementation Tasks**

### **Week 7, Day 1-2: Database & Models** (4 hours)
```python
# backend/app/models/blog.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship

class BlogPost(Base):
    __tablename__ = "blog_posts"
    # ... (see schema above)

class BlogComment(Base):
    __tablename__ = "blog_comments"
    # ... (see schema above)

class BlogLike(Base):
    __tablename__ = "blog_likes"
    # ... (see schema above)
```

### **Week 7, Day 3-4: Backend API** (8 hours)
```python
# backend/app/api/v1/blog.py

# PUBLIC endpoints (no auth, for SEO)
@router.get("/blog/posts")  # List all posts
@router.get("/blog/posts/{slug}")  # Single post
@router.get("/blog/sitemap.xml")  # SEO sitemap
@router.get("/blog/rss.xml")  # RSS feed

# AUTHENTICATED endpoints
@router.post("/blog/posts")  # Create post
@router.put("/blog/posts/{id}")  # Update post
@router.delete("/blog/posts/{id}")  # Delete post
@router.post("/blog/posts/{id}/like")  # Like post
@router.post("/blog/posts/{id}/comments")  # Add comment
```

### **Week 7, Day 5-6: Blog Editor** (6 hours)
```typescript
// frontend/src/components/BlogEditor.tsx
// Rich text editor with:
// - Markdown support
// - Image upload
// - SEO fields (meta title, description)
// - Category/tag selection
// - Preview mode
// - Draft/publish toggle
```

### **Week 7, Day 7 + Week 8, Day 1-2: Public Blog Pages** (6 hours)
```typescript
// frontend/src/pages/BlogListPage.tsx
// - Grid of blog posts
// - Category filter
// - Tag filter
// - Search
// - Pagination

// frontend/src/pages/BlogPostPage.tsx
// - Full post content
// - Author info
// - Related posts
// - Comments section
// - Like button
// - Share buttons
```

### **Week 8, Day 3-4: SEO Optimization** (4 hours)
- Add sitemap generation
- Add RSS feed
- Add Open Graph tags
- Add Schema.org markup
- Submit to Google Search Console
- Create robots.txt
- Optimize images
- Add social sharing

---

## 🚀 **Launch Strategy**

### **Phase 1: Seed Content** (Week 8)
Write 5-10 high-quality posts yourself:
1. "How to Find Research Papers" (2,900/month)
2. "How to Write Literature Review" (8,100/month)
3. "Best Academic Search Engines" (1,600/month)
4. "How to Read Scientific Papers" (2,400/month)
5. "Citation Management Guide" (1,300/month)

### **Phase 2: User-Generated Content** (Month 2)
- Invite power users to write
- Offer incentives (premium features)
- Feature best posts
- Share on social media

### **Phase 3: SEO Growth** (Month 3-6)
- Monitor Google Search Console
- Optimize top-performing posts
- Build backlinks
- Guest post on other blogs
- Create video versions (YouTube)

---

## 📈 **Expected Results**

### **Month 1:**
- 5-10 blog posts published
- 100-500 organic visitors
- Google starts indexing

### **Month 3:**
- 20-30 blog posts
- 1,000-2,000 organic visitors/month
- Ranking for long-tail keywords

### **Month 6:**
- 50+ blog posts
- 5,000-10,000 organic visitors/month
- Ranking for competitive keywords
- 10-20% of visitors convert to users

### **Month 12:**
- 100+ blog posts
- 20,000-50,000 organic visitors/month
- Top 3 rankings for target keywords
- Major traffic source for app

---

## 💰 **Cost Analysis**

### **Development:**
- Week 7-8: 28 hours

### **Ongoing:**
- Content writing: 2-4 hours/post
- Image creation: 1 hour/post
- SEO optimization: 1 hour/post
- **Total per post: 4-6 hours**

### **Infrastructure:**
- Database storage: ~$1/month
- Image hosting: $0-5/month (Cloudflare R2)
- **Total: $1-6/month**

### **ROI:**
- Organic traffic: FREE
- User acquisition cost: $0
- Lifetime value: $50-150/user
- **ROI: Infinite** 🚀

---

## ✅ **Success Metrics**

### **Traffic:**
- [ ] 1,000 organic visitors/month (Month 3)
- [ ] 5,000 organic visitors/month (Month 6)
- [ ] 20,000 organic visitors/month (Month 12)

### **Engagement:**
- [ ] 50+ blog posts published
- [ ] 100+ comments
- [ ] 500+ likes
- [ ] 10+ user-generated posts

### **SEO:**
- [ ] Rank top 10 for 5 keywords
- [ ] Rank top 3 for 2 keywords
- [ ] 100+ backlinks
- [ ] Domain authority > 30

### **Conversion:**
- [ ] 10% of blog visitors sign up
- [ ] 5% become active users
- [ ] 1% convert to paid

---

## 🎯 **Priority: HIGH**

**Why this is important:**
1. **Free traffic** - No ad spend needed
2. **Compound growth** - Content keeps working
3. **Authority building** - Become trusted source
4. **AI search** - Show up in ChatGPT/Perplexity
5. **Community** - Engaged users create content

**Recommendation:** Implement in Week 7-8 as planned!

---

**Files to create:**
- `backend/app/models/blog.py`
- `backend/app/api/v1/blog.py`
- `backend/migrations/003_create_blog_tables.sql`
- `frontend/src/pages/BlogListPage.tsx`
- `frontend/src/pages/BlogPostPage.tsx`
- `frontend/src/components/BlogEditor.tsx`
- `frontend/src/components/BlogCard.tsx`

**Dependencies:**
```bash
pip install python-slugify markdown2
npm install react-markdown react-syntax-highlighter
```
