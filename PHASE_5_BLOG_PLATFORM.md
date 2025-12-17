# Phase 5: Blog Platform for SEO & Community Growth
## User-Generated Content Marketing Platform

**Timeline:** Week 8-9 (~28 hours)  
**Priority:** HIGH - Growth strategy  
**Impact:** Organic traffic, SEO ranking, community building

---

## 🎯 **Phase 5 Objectives**

1. User-generated blog posts about research tips
2. SEO-optimized content (rank on Google)
3. Show up in AI search (ChatGPT, Perplexity)
4. Build community engagement
5. Free organic traffic

**Why This is Critical:**
- **Free traffic** - No ad spend needed
- **Compound growth** - Content keeps working
- **Authority building** - Become trusted source
- **AI search** - Show up in ChatGPT/Perplexity

---

## 📊 **Database Schema** (4 hours)

```sql
CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    author_id UUID REFERENCES local_users(id),
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(250) UNIQUE NOT NULL,  -- SEO-friendly URL
    excerpt VARCHAR(500),
    content TEXT NOT NULL,
    cover_image_url VARCHAR(500),
    
    -- SEO
    meta_title VARCHAR(60),
    meta_description VARCHAR(160),
    keywords JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- Engagement
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    -- Categories
    category VARCHAR(50),
    tags JSONB
);

CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_published ON blog_posts(published_at DESC);
```

See `BLOG_PLATFORM_DESIGN.md` for complete schema.

---

## 🚀 **Backend API** (8 hours)

```python
# backend/app/api/v1/blog.py

# PUBLIC endpoints (no auth, for SEO)
@router.get("/blog/posts")
async def get_blog_posts(
    page: int = 1,
    category: Optional[str] = None,
    tag: Optional[str] = None
):
    """Get published blog posts (PUBLIC for SEO)"""
    
@router.get("/blog/posts/{slug}")
async def get_blog_post(slug: str):
    """Get single blog post by slug (PUBLIC for SEO)"""

# AUTHENTICATED endpoints
@router.post("/blog/posts")
async def create_blog_post(
    title: str,
    content: str,
    current_user_id: str = Depends(get_current_user)
):
    """Create new blog post"""

@router.get("/blog/sitemap.xml")
async def generate_sitemap():
    """Generate XML sitemap for SEO"""
```

---

## 🎨 **Frontend Components** (6 hours)

```typescript
// frontend/src/pages/BlogPage.tsx
export function BlogPage() {
  const [posts, setPosts] = useState([]);
  
  return (
    <div className="blog-page">
      <header className="blog-header">
        <h1>Research Tips & Tutorials</h1>
      </header>
      <div className="blog-grid">
        {posts.map(post => <BlogCard key={post.id} post={post} />)}
      </div>
    </div>
  );
}

// frontend/src/pages/BlogPostPage.tsx
export function BlogPostPage({ slug }: { slug: string }) {
  return (
    <article className="blog-post">
      <Helmet>
        <title>{post.meta_title}</title>
        <meta name="description" content={post.meta_description} />
      </Helmet>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: markdownToHtml(post.content) }} />
    </article>
  );
}
```

---

## 📈 **SEO Strategy** (4 hours)

### **Target Keywords:**
- "how to search research papers" (5,400/month)
- "how to write literature review" (8,100/month)
- "academic search engines" (1,600/month)

### **Content to Create:**
1. "How to Find Research Papers on Any Topic (2025 Guide)"
2. "10 Best Academic Search Engines for Researchers"
3. "How to Write a Literature Review in 5 Steps"

### **SEO Checklist:**
- [ ] Unique meta titles (50-60 chars)
- [ ] Meta descriptions (150-160 chars)
- [ ] H1/H2/H3 structure
- [ ] Internal linking
- [ ] Sitemap.xml
- [ ] RSS feed
- [ ] Open Graph tags

---

## 🧪 **Testing** (4 hours)

```python
@pytest.mark.asyncio
async def test_create_blog_post():
    """Test blog post creation"""
    response = await client.post("/api/v1/blog/posts", json={
        "title": "Test Post",
        "content": "Test content"
    })
    assert response.status_code == 200
```

---

## 📊 **Expected Results**

### **Month 1:**
- 5-10 blog posts published
- 100-500 organic visitors

### **Month 6:**
- 50+ blog posts
- 5,000-10,000 organic visitors/month
- Ranking for long-tail keywords

### **Month 12:**
- 100+ blog posts
- 20,000-50,000 organic visitors/month
- Top 3 rankings for target keywords

---

## ✅ **Success Criteria**

- [ ] Blog posts are publicly accessible
- [ ] SEO meta tags work
- [ ] Sitemap.xml generates correctly
- [ ] Google indexes posts
- [ ] Comments work
- [ ] Like functionality works

**Total Time:** ~28 hours  
**Total Cost:** $0 (just database storage)  
**ROI:** Infinite (free organic traffic!)
