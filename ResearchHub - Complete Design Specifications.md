# ResearchHub - Complete Design Specifications

## 🎯 Overview
This document contains pixel-perfect specifications for all ResearchHub pages based on Figma designs. Use these specs to rebuild components without messiness.

---

## 📄 PAGE 1: Landing/Search Page

### 1. LAYOUT STRUCTURE

#### Container
- **Max-width**: 1440px (desktop)
- **Centered**: Yes, using `margin: 0 auto`
- **Horizontal padding**: 80px on desktop, 24px on mobile

#### Header/Navigation
- **Height**: 72px
- **Background**: White (#FFFFFF)
- **Border-bottom**: 1px solid #E5E7EB
- **Layout**: Flex, space-between
- **Logo position**: Left, with 16px gap to text "ResearchHub"
- **Nav items**: Right-aligned, 32px gap between items
  - Features, Pricing, Blog, About, Contact
  - "Sign In" button (text only)
  - "My Workspace" button (filled, black background)

#### Hero Section
- **Padding-top**: 120px from header
- **Padding-bottom**: 80px
- **Text alignment**: Center
- **Layout**: Vertical flex, center-aligned

**Logo Icon:**
- Size: 64px × 64px
- Blue gradient icon
- Margin-bottom: 24px

**Main Title:**
```
Text: "ResearchHub"
Font-size: 72px
Font-weight: 700 (Bold)
Color: #111827 (near-black)
Letter-spacing: -0.02em
Line-height: 1.1
Margin-bottom: 24px
```

**Subtitle:**
```
Text: "Search millions of academic papers from arXiv, Semantic Scholar, and OpenAlex"
Font-size: 20px
Font-weight: 400
Color: #6B7280 (gray)
Line-height: 1.6
Max-width: 720px
Margin: 0 auto 48px auto
```

#### Feature Pills Row
- **Layout**: Horizontal flex, center-aligned
- **Gap**: 24px between pills
- **Margin-bottom**: 48px

**Each pill:**
```
Padding: 8px 16px
Background: #F9FAFB
Border-radius: 999px (fully rounded)
Font-size: 14px
Color: #374151
Icon + Text with 8px gap
```

Pills content:
1. ⚡ AI-Powered
2. 📄 250M+ Papers
3. 👥 Trusted by Researchers

#### Category Tabs
- **Layout**: Horizontal flex, center-aligned
- **Gap**: 12px between tabs
- **Margin-bottom**: 48px

**Active tab (AI & CS):**
```
Background: #2563EB (blue)
Color: #FFFFFF (white)
Padding: 12px 24px
Border-radius: 999px
Font-size: 15px
Font-weight: 500
```

**Inactive tabs:**
```
Background: transparent
Color: #6B7280
Padding: 12px 24px
Border-radius: 999px
Font-size: 15px
Font-weight: 400
Hover: Background #F3F4F6
```

Tabs: AI & CS | Medicine & Biology | Agriculture & Animal Science | Humanities & Social Sciences | Economics & Business

#### Search Bar
- **Max-width**: 800px
- **Margin**: 0 auto
- **Height**: 64px
- **Layout**: Flex row

**Container:**
```
Background: #FFFFFF
Border: 2px solid #E5E7EB
Border-radius: 16px
Box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
Padding: 8px 8px 8px 20px
Display: flex
Align-items: center
Gap: 12px
```

**Search Icon:**
```
Size: 24px × 24px
Color: #9CA3AF
Position: Left side, 20px from edge
```

**Input Field:**
```
Flex: 1
Border: none
Font-size: 16px
Color: #111827
Placeholder: "Search for papers, authors, topics..."
Placeholder-color: #9CA3AF
Outline: none
```

**Search Button:**
```
Background: #6366F1 (blue-indigo gradient)
Border-radius: 12px
Padding: 16px 32px
Color: #FFFFFF
Font-size: 16px
Font-weight: 500
Border: none
Cursor: pointer
Icon: 🔍 (search icon, 20px)

Hover state:
- Background: #4F46E5 (darker blue)
- Transform: scale(1.02)
- Transition: all 0.2s ease
```

### 2. STATISTICS CARDS SECTION

**Section Container:**
```
Padding: 80px 0
Background: linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%)
```

**Cards Grid:**
```
Display: grid
Grid-template-columns: repeat(3, 1fr)
Gap: 32px
Max-width: 1200px
Margin: 0 auto

Mobile (<768px):
- Grid-template-columns: 1fr
- Gap: 16px
```

**Card Styles:**

*Card 1 (arXiv - Blue):*
```
Background: #EFF6FF (light blue)
Border: 1px solid #DBEAFE
Border-radius: 24px
Padding: 48px 40px
Text-align: center
```

*Card 2 (Semantic Scholar - Purple):*
```
Background: #F5F3FF (light purple)
Border: 1px solid #EDE9FE
Border-radius: 24px
Padding: 48px 40px
Text-align: center
```

*Card 3 (OpenAlex - Green):*
```
Background: #ECFDF5 (light green)
Border: 1px solid #D1FAE5
Border-radius: 24px
Padding: 48px 40px
Text-align: center
```

**Card Content:**
```
Number:
- Font-size: 56px
- Font-weight: 700
- Color: #111827
- Margin-bottom: 8px

Label:
- Font-size: 18px
- Font-weight: 400
- Color: #6B7280
```

Content:
1. 2M+ | arXiv Papers
2. 200M+ | Semantic Scholar
3. 250M+ | OpenAlex

### 3. SPACING VALUES

```
Section vertical spacing: 80px
Card internal padding: 48px 40px
Element gaps: 12px (small), 24px (medium), 48px (large)
Container padding: 80px (desktop), 24px (mobile)
```

### 4. COLORS PALETTE

```css
/* Primary Colors */
--primary-blue: #2563EB;
--primary-indigo: #6366F1;
--primary-dark: #111827;

/* Gray Scale */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-700: #374151;
--gray-900: #111827;

/* Background Colors */
--bg-blue: #EFF6FF;
--bg-purple: #F5F3FF;
--bg-green: #ECFDF5;

/* Border Colors */
--border-blue: #DBEAFE;
--border-purple: #EDE9FE;
--border-green: #D1FAE5;
```

### 5. TYPOGRAPHY SYSTEM

```css
/* Font Family */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;

/* Font Sizes */
--text-xs: 12px;
--text-sm: 14px;
--text-base: 16px;
--text-lg: 18px;
--text-xl: 20px;
--text-2xl: 24px;
--text-4xl: 36px;
--text-6xl: 56px;
--text-7xl: 72px;

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.1;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.6;
```

### 6. RESPONSIVE BREAKPOINTS

```css
/* Mobile First Approach */
--mobile: 320px;
--tablet: 768px;
--desktop: 1024px;
--wide: 1440px;

@media (max-width: 768px) {
  /* Hero title: 48px */
  /* Hero subtitle: 18px */
  /* Container padding: 24px */
  /* Category tabs: Horizontal scroll */
  /* Stats grid: 1 column */
}
```

---

## 📱 PAGE 2: Workspace - My Saved Papers

### 1. LAYOUT STRUCTURE

#### Overall Layout
```
Display: Flex (horizontal)
Height: 100vh
Background: #FFFFFF
```

**Left Sidebar:**
```
Width: 280px (fixed)
Background: #1F2937 (dark gray)
Height: 100vh
Overflow-y: auto
Flex-shrink: 0
```

**Main Content Area:**
```
Flex: 1
Background: #F9FAFB
Overflow-y: auto
```

### 2. LEFT SIDEBAR SPECIFICATIONS

**Sidebar Header:**
```
Padding: 24px 20px
Border-bottom: 1px solid #374151
```

Back button + Logo:
```
Display: flex
Align-items: center
Gap: 12px
Color: #FFFFFF
Font-size: 16px
Font-weight: 500
```

**Navigation Icons:**
```
Padding: 20px 0
Gap: 8px between items
```

**Each Nav Item:**
```
Width: 100%
Padding: 12px 20px
Display: flex
Align-items: center
Gap: 12px
Color: #9CA3AF
Font-size: 14px
Transition: all 0.2s

Active state:
- Background: #2563EB (blue)
- Color: #FFFFFF
- Border-left: 4px solid #3B82F6

Hover state:
- Background: #374151
- Color: #FFFFFF
```

Nav items order:
1. 📌 (Bookmark icon) - Active
2. 📁 (Folder icon)
3. 🎁 (Box icon)
4. 📚 (Books icon)
5. 📊 (Chart icon)
6. 🔄 (History icon)

### 3. SAVED PAPERS PANEL

**Panel Container:**
```
Width: 320px
Background: #FFFFFF
Border-right: 1px solid #E5E7EB
Height: 100%
Display: flex
Flex-direction: column
```

**Panel Header:**
```
Padding: 20px 24px
Border-bottom: 1px solid #E5E7EB
Display: flex
Justify-content: space-between
Align-items: center
```

Header content:
```
Title: "My Saved Papers"
Font-size: 18px
Font-weight: 600
Color: #111827

Close button (×):
- Size: 24px
- Color: #6B7280
- Hover: #111827
```

**Saved Papers Section:**
```
Padding: 24px
```

Section title:
```
Display: flex
Align-items: center
Gap: 8px
Font-size: 16px
Font-weight: 600
Color: #111827
Margin-bottom: 16px
Icon: 📌 (bookmark)
```

**Upload PDF Button:**
```
Width: 100%
Padding: 12px 16px
Background: #F9FAFB
Border: 1px dashed #D1D5DB
Border-radius: 8px
Display: flex
Align-items: center
Justify-content: center
Gap: 8px
Color: #6B7280
Font-size: 14px
Font-weight: 500
Cursor: pointer

Hover:
- Background: #F3F4F6
- Border-color: #9CA3AF
```

**Search Library:**
```
Margin-top: 16px
Width: 100%
Padding: 10px 12px
Background: #F9FAFB
Border: 1px solid #E5E7EB
Border-radius: 8px
Font-size: 14px
Color: #6B7280
```

**Empty State:**
```
Padding: 60px 24px
Text-align: center
```

Folder icon:
```
Size: 64px
Color: #D1D5DB
Margin-bottom: 16px
```

Empty text:
```
Font-size: 14px
Color: #9CA3AF
Line-height: 1.6
Max-width: 240px
Margin: 0 auto
```

### 4. MAIN WORKSPACE AREA

**Top Bar:**
```
Height: 64px
Background: #FFFFFF
Border-bottom: 1px solid #E5E7EB
Padding: 0 24px
Display: flex
Align-items: center
Justify-content: space-between
Position: sticky
Top: 0
Z-index: 10
```

**Tab System:**
```
Display: flex
Gap: 4px
```

**Each Tab:**
```
Padding: 8px 16px
Background: #F3F4F6
Border-radius: 8px 8px 0 0
Font-size: 14px
Color: #6B7280
Display: flex
Align-items: center
Gap: 8px
Cursor: pointer

Active tab:
- Background: #FFFFFF
- Color: #111827
- Border-bottom: 2px solid #2563EB
```

**Dropdown in Tab:**
```
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 6px
Padding: 6px 32px 6px 12px
Font-size: 14px
Color: #111827
Position: relative

Arrow icon: Chevron down, 16px
```

**Right Side Actions:**
```
Display: flex
Gap: 12px
```

Buttons:
- Expand icon (↗️)
- Close icon (×)

### 5. NOTES/CONTENT AREA

**Content Container:**
```
Padding: 40px
Max-width: 900px
Margin: 0 auto
```

**Document Title:**
```
Font-size: 32px
Font-weight: 700
Color: #111827
Margin-bottom: 24px
Border: none
Outline: none
```

**Formatting Toolbar:**
```
Display: flex
Gap: 8px
Margin-bottom: 24px
Padding-bottom: 16px
Border-bottom: 1px solid #E5E7EB
```

**Toolbar Buttons:**
```
Width: 32px
Height: 32px
Border-radius: 6px
Background: transparent
Border: 1px solid #E5E7EB
Color: #6B7280
Display: flex
Align-items: center
Justify-content: center
Cursor: pointer

Hover:
- Background: #F3F4F6
- Border-color: #9CA3AF
```

Buttons: H1, H2, Bold, Italic, Code, Link, Image, More (...)

**Content Area:**
```
Font-size: 16px
Line-height: 1.7
Color: #374151
```

Placeholder text:
```
Color: #9CA3AF
Font-style: italic
```

**Key Points Section:**
```
Margin-top: 32px
```

Heading:
```
Font-size: 18px
Font-weight: 600
Color: #111827
Margin-bottom: 12px
```

List items:
```
Font-size: 15px
Color: #4B5563
Line-height: 1.6
Padding-left: 20px
List-style: disc
Margin-bottom: 8px
```

**Questions Section:**
```
Margin-top: 32px
```

Same styling as Key Points

**Footer Metadata:**
```
Position: fixed
Bottom: 0
Right: 0
Padding: 12px 40px
Background: #FFFFFF
Border-top: 1px solid #E5E7EB
Font-size: 12px
Color: #9CA3AF
```

Content: "Last edited: 11/17/2025" + "Note ID:"

---

## 📱 PAGE 3: Workspace - AI Assistant & Literature Review

### 1. LAYOUT STRUCTURE

Same 3-column layout as Page 2:
- Left sidebar (280px, dark)
- Middle panel (variable width)
- Right panel (flexible, main content)

### 2. AI ASSISTANT PANEL (LEFT MIDDLE)

**Panel Container:**
```
Width: 380px
Background: #FFFFFF
Border-right: 1px solid #E5E7EB
Display: flex
Flex-direction: column
Height: 100%
```

**Panel Header:**
```
Padding: 20px 24px
Border-bottom: 1px solid #E5E7EB
Display: flex
Justify-content: space-between
Align-items: center
```

Title:
```
Display: flex
Align-items: center
Gap: 8px
Font-size: 18px
Font-weight: 600
Color: #111827
Icon: 🤖 (robot/AI icon in purple)
```

**Context Badge:**
```
Font-size: 12px
Color: #6B7280
Padding: 4px 12px
Background: #F9FAFB
Border-radius: 12px
Margin-top: 8px
```

Content: "0 papers in context"

**Welcome Message:**
```
Padding: 24px
Background: #F9FAFB
Border-radius: 12px
Margin: 24px
```

Avatar icon:
```
Width: 40px
Height: 40px
Background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)
Border-radius: 50%
Display: flex
Align-items: center
Justify-content: center
Color: #FFFFFF
Margin-bottom: 12px
```

Message text:
```
Font-size: 15px
Color: #374151
Line-height: 1.6
```

**Capabilities List:**
```
Padding: 0 24px
Margin-top: 16px
```

Each bullet:
```
Font-size: 14px
Color: #4B5563
Line-height: 1.8
Margin-bottom: 8px
Padding-left: 20px
List-style: disc
```

**Action Buttons:**
```
Padding: 0 24px
Margin-top: 24px
Display: flex
Flex-direction: column
Gap: 12px
```

**Primary Buttons:**
```
Width: 100%
Padding: 12px 16px
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 8px
Font-size: 14px
Font-weight: 500
Color: #374151
Display: flex
Align-items: center
Gap: 8px
Cursor: pointer
Transition: all 0.2s

Hover:
- Border-color: #2563EB
- Background: #F9FAFB
```

Buttons:
1. 📄 Summarize all papers
2. ⚖️ Compare papers
3. 🔍 Literature review help

**Chat Input Area:**
```
Padding: 20px 24px
Border-top: 1px solid #E5E7EB
Margin-top: auto
Background: #FFFFFF
```

**Input Container:**
```
Position: relative
Display: flex
Align-items: flex-end
Gap: 12px
```

**Text Input:**
```
Flex: 1
Padding: 12px 16px
Background: #F9FAFB
Border: 1px solid #E5E7EB
Border-radius: 12px
Font-size: 14px
Color: #111827
Resize: none
Min-height: 44px
Max-height: 120px
```

Placeholder: "Ask me anything about your papers..."

**Send Button:**
```
Width: 44px
Height: 44px
Background: #6366F1
Border-radius: 12px
Border: none
Color: #FFFFFF
Display: flex
Align-items: center
Justify-content: center
Cursor: pointer
Flex-shrink: 0

Hover:
- Background: #4F46E5
```

**Helper Text:**
```
Font-size: 11px
Color: #9CA3AF
Margin-top: 8px
```

Content: "Press Enter to send, Shift+Enter for new line"

### 3. LITERATURE REVIEW PANEL (RIGHT SIDE)

**Panel Header:**
```
Padding: 24px 32px
Background: #FFFFFF
Border-bottom: 1px solid #E5E7EB
Display: flex
Justify-content: space-between
Align-items: center
```

**Title Section:**
```
Display: flex
Align-items: center
Gap: 12px
```

Icon:
```
Width: 32px
Height: 32px
Background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)
Border-radius: 8px
Display: flex
Align-items: center
Justify-content: center
Color: #FFFFFF
```

Title:
```
Font-size: 24px
Font-weight: 600
Color: #111827
```

**New Project Button:**
```
Padding: 10px 20px
Background: #111827
Color: #FFFFFF
Border-radius: 8px
Font-size: 14px
Font-weight: 500
Display: flex
Align-items: center
Gap: 8px
Border: none
Cursor: pointer

Hover:
- Background: #374151
```

**Content Area:**
```
Padding: 32px
```

**Subtitle:**
```
Font-size: 14px
Color: #6B7280
Line-height: 1.6
Margin-bottom: 32px
```

Content: "Organize your papers into projects. Click a project to view and edit the table."

**Projects Grid:**
```
Display: grid
Grid-template-columns: repeat(auto-fill, minmax(400px, 1fr))
Gap: 24px
```

### 4. PROJECT CARDS

**Card Container:**
```
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 12px
Padding: 24px
Position: relative
Transition: all 0.2s
Cursor: pointer

Hover:
- Border-color: #2563EB
- Box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08)
- Transform: translateY(-2px)
```

**Delete Button:**
```
Position: absolute
Top: 20px
Right: 20px
Width: 32px
Height: 32px
Background: #FEE2E2
Border-radius: 6px
Display: flex
Align-items: center
Justify-content: center
Color: #DC2626
Border: none
Cursor: pointer
Opacity: 0.8

Hover:
- Opacity: 1
- Background: #FEF2F2
```

**Card Title:**
```
Font-size: 18px
Font-weight: 600
Color: #111827
Margin-bottom: 8px
Padding-right: 40px
```

**Card Description:**
```
Font-size: 14px
Color: #6B7280
Line-height: 1.5
Margin-bottom: 20px
```

**Card Footer:**
```
Display: flex
Align-items: center
Gap: 16px
Font-size: 13px
Color: #9CA3AF
```

Paper count badge:
```
Background: #F3F4F6
Padding: 4px 10px
Border-radius: 6px
Font-weight: 500
Color: #6B7280
```

Date:
```
Color: #9CA3AF
```

**Project Cards:**

Card 1:
```
Title: "Machine Learning"
Description: "Papers related to ML algorithms and applications"
Papers: 0 papers
Created: 11/17/2025
```

Card 2:
```
Title: "Neural Networks"
Description: "Research on deep learning and neural architectures"
Papers: 0 papers
Created: 11/17/2025
```

---

## 📱 PAGE 4: Search Results

### 1. LAYOUT STRUCTURE

**Overall Container:**
```
Display: flex
Height: 100vh
Background: #FFFFFF
```

**Left Filters Sidebar:**
```
Width: 280px
Background: #FFFFFF
Border-right: 1px solid #E5E7EB
Overflow-y: auto
Flex-shrink: 0
```

**Right Content Area:**
```
Flex: 1
Display: flex
Flex-direction: column
Overflow-y: auto
```

### 2. SEARCH HEADER

**Header Container:**
```
Padding: 20px 32px
Background: #FFFFFF
Border-bottom: 1px solid #E5E7EB
Position: sticky
Top: 0
Z-index: 10
```

**Back Button:**
```
Display: flex
Align-items: center
Gap: 8px
Color: #6B7280
Font-size: 14px
Margin-bottom: 16px
Cursor: pointer

Hover:
- Color: #2563EB
```

**Search Bar:**
```
Display: flex
Gap: 16px
Align-items: center
```

**Search Input Container:**
```
Flex: 1
Background: #F9FAFB
Border: 1px solid #E5E7EB
Border-radius: 10px
Padding: 12px 16px
Display: flex
Align-items: center
Gap: 12px
```

Search input:
```
Flex: 1
Border: none
Background: transparent
Font-size: 15px
Color: #111827
Outline: none
```

**Category Badge:**
```
Padding: 6px 12px
Background: #EFF6FF
Border-radius: 6px
Font-size: 13px
Color: #2563EB
Font-weight: 500
```

Content: "Category: AI & CS"

**Workspace Button:**
```
Padding: 10px 20px
Background: #111827
Color: #FFFFFF
Border-radius: 8px
Font-size: 14px
Font-weight: 500
Border: none
Cursor: pointer

Hover:
- Background: #374151
```

### 3. FILTERS SIDEBAR

**Sidebar Container:**
```
Padding: 24px 20px
```

**Filter Header:**
```
Display: flex
Align-items: center
Gap: 8px
Font-size: 16px
Font-weight: 600
Color: #111827
Margin-bottom: 24px
Icon: ⚡ (funnel/filter icon)
```

**Filter Section:**
```
Margin-bottom: 32px
```

**Section Title:**
```
Font-size: 14px
Font-weight: 600
Color: #111827
Margin-bottom: 12px
```

### 4. SORT BY SECTION

**Dropdown:**
```
Width: 100%
Padding: 10px 12px
Background: #F9FAFB
Border: 1px solid #E5E7EB
Border-radius: 8px
Font-size: 14px
Color: #374151
Cursor: pointer
Appearance: none
Background-image: url(chevron-down-icon)
Background-position: right 12px center
Background-repeat: no-repeat
```

Options:
- Relevance (selected)
- Most Recent
- Most Cited

### 5. SOURCES SECTION

**Checkboxes:**
```
Display: flex
Flex-direction: column
Gap: 12px
```

**Each Checkbox:**
```
Display: flex
Align-items: center
Gap: 10px
Cursor: pointer
```

Checkbox input:
```
Width: 18px
Height: 18px
Border: 2px solid #D1D5DB
Border-radius: 4px
Cursor: pointer

Checked:
- Background: #2563EB
- Border-color: #2563EB
```

Label:
```
Font-size: 14px
Color: #374151
```

Sources:
- ☑️ arXiv
- ☑️ Semantic Scholar
- ☑️ OpenAlex

### 6. YEAR RANGE SECTION

**Range Display:**
```
Font-size: 13px
Color: #6B7280
Margin-bottom: 12px
```

Content: "Year Range: 2020 - 2025"

**Range Slider:**
```
Width: 100%
Height: 6px
Background: #E5E7EB
Border-radius: 3px
Position: relative
```

Active track:
```
Background: #2563EB
Height: 100%
Border-radius: 3px
```

Slider thumbs:
```
Width: 18px
Height: 18px
Background: #FFFFFF
Border: 3px solid #2563EB
Border-radius: 50%
Cursor: pointer
Box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1)
```

### 7. MINIMUM CITATIONS SECTION

**Slider:**
```
Width: 100%
Height: 6px
Background: #E5E7EB
Border-radius: 3px
Margin-bottom: 12px
```

**Value Display:**
```
Font-size: 13px
Color: #6B7280
```

Content: "Minimum Citations: 0"

### 8. SEARCH RESULTS AREA

**Results Header:**
```
Padding: 32px 32px 24px 32px
```

**Results Count:**
```
Font-size: 28px
Font-weight: 600
Color: #111827
Margin-bottom: 8px
```

Content: "Search Results"

**Results Meta:**
```
Font-size: 14px
Color: #6B7280
```

Content: "Found 20 papers matching "mdd" in AI & CS"

### 9. PAPER CARDS

**Card Container:**
```
Padding: 24px 32px
Border-bottom: 1px solid #E5E7EB
Background: #FFFFFF
Transition: background 0.2s

Hover:
- Background: #F9FAFB
```

**Card Header:**
```
Display: flex
Justify-content: space-between
Align-items: flex-start
Margin-bottom: 12px
```

**Paper Title:**
```
Font-size: 20px
Font-weight: 600
Color: #2563EB
Line-height: 1.4
Cursor: pointer
Text-decoration: none

Hover:
- Text-decoration: underline
```

**Bookmark Button:**
```
Width: 36px
Height: 36px
Background: transparent
Border: 1px solid #E5E7EB
Border-radius: 8px
Display: flex
Align-items: center
Justify-content: center
Color: #6B7280
Cursor: pointer
Flex-shrink: 0

Hover:
- Background: #F3F4F6
- Border-color: #2563EB
- Color: #2563EB

Active (saved):
- Background: #EFF6FF
- Border-color: #2563EB
- Color: #2563EB
```

**Authors & Date:**
```
Font-size: 14px
Color: #6B7280
Margin-bottom: 12px
```

Format: "Author 1, Author 2, Author 3 · 2020"

**Paper Abstract:**
```
Font-size: 15px
Color: #374151
Line-height: 1.7
Margin-bottom: 16px
```

**Card Footer:**
```
Display: flex
Align-items: center
Justify-content: space-between
Flex-wrap: wrap
Gap: 16px
```

**Source Badges:**
```
Display: flex
Gap: 8px
```

**Each Badge:**
```
Padding: 4px 12px
Background: #F3F4F6
Border-radius: 6px
Font-size: 12px
Font-weight: 500
Color: #4B5563
```

Badge examples:
- arXiv (blue tint)
- NeurIPS (purple tint)

**Citation Count:**
```
Font-size: 14px
Color: #6B7280
Display: flex
Align-items: center
Gap: 6px
```

Format: "457 citations"

**Action Buttons:**
```
Display: flex
Gap: 12px
```

**View PDF Button:**
```
Padding: 8px 16px
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 8px
Font-size: 14px
Font-weight: 500
Color: #374151
Display: flex
Align-items: center
Gap: 6px
Cursor: pointer

Hover:
- Border-color: #2563EB
- Color: #2563EB
```

**Source Button:**
```
Padding: 8px 16px
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 8px
Font-size: 14px
Font-weight: 500
Color: #374151
Display: flex
Align-items: center
Gap: 6px
Cursor: pointer

Hover:
- Border-color: #2563EB
- Color: #2563EB
```

Icon: 🔗 (external link)

---

## 🎨 COMPONENT-SPECIFIC STYLING

### Dropdown Menu Styling

**Dropdown Container (Window 1 dropdown):**
```
Position: absolute
Top: 100%
Left: 0
Margin-top: 4px
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 8px
Box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)
Min-width: 200px
Padding: 6px
Z-index: 50
```

**Dropdown Items:**
```
Padding: 10px 12px
Border-radius: 6px
Font-size: 14px
Color: #374151
Cursor: pointer
Display: flex
Align-items: center
Gap: 10px
Transition: all 0.15s

Hover:
- Background: #F3F4F6
- Color: #111827

Selected:
- Background: #EFF6FF
- Color: #2563EB
```

Menu items:
- Paper Viewer
- Notes (selected)
- AI Assistant
- Literature Review
- Citation Comparison

---

## 🔄 INTERACTIVE STATES

### Button States

**Primary Button (Blue):**
```
/* Default */
Background: #2563EB
Color: #FFFFFF
Border: none

/* Hover */
Background: #1D4ED8
Transform: scale(1.02)

/* Active (click) */
Background: #1E40AF
Transform: scale(0.98)

/* Disabled */
Background: #93C5FD
Cursor: not-allowed
Opacity: 0.6
```

**Secondary Button (White with border):**
```
/* Default */
Background: #FFFFFF
Color: #374151
Border: 1px solid #E5E7EB

/* Hover */
Background: #F9FAFB
Border-color: #2563EB
Color: #2563EB

/* Active */
Background: #F3F4F6
Border-color: #1D4ED8
```

**Ghost Button (Transparent):**
```
/* Default */
Background: transparent
Color: #6B7280
Border: none

/* Hover */
Background: #F3F4F6
Color: #111827

/* Active */
Background: #E5E7EB
```

### Input States

**Text Input:**
```
/* Default */
Border: 1px solid #E5E7EB
Background: #F9FAFB

/* Focus */
Border: 2px solid #2563EB
Background: #FFFFFF
Outline: none
Box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1)

/* Error */
Border: 2px solid #DC2626
Box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1)

/* Disabled */
Background: #F3F4F6
Color: #9CA3AF
Cursor: not-allowed
```

### Card Hover Effects

**Paper Card:**
```
/* Default */
Background: #FFFFFF
Border-bottom: 1px solid #E5E7EB

/* Hover */
Background: #F9FAFB
Transform: translateX(4px)
Transition: all 0.2s ease
```

**Project Card:**
```
/* Default */
Border: 1px solid #E5E7EB
Box-shadow: none

/* Hover */
Border-color: #2563EB
Box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08)
Transform: translateY(-2px)
Transition: all 0.2s ease
```

---

## 📐 SPACING SYSTEM

### Global Spacing Scale
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
--space-24: 96px;
--space-32: 128px;
```

### Component-Specific Spacing

**Card Spacing:**
```
Internal padding: 24px
Gap between elements: 12px
Margin between cards: 16px
Section spacing: 32px
```

**Container Spacing:**
```
Page horizontal padding: 32px (desktop), 16px (mobile)
Section vertical spacing: 80px (desktop), 40px (mobile)
Component gaps: 16px (standard)
```

**Text Spacing:**
```
Heading margin-bottom: 8px (small), 16px (medium), 24px (large)
Paragraph margin-bottom: 16px
List item spacing: 8px
```

---

## 🎯 ICON SYSTEM

### Icon Specifications
```
Small icons: 16px × 16px
Medium icons: 20px × 20px
Large icons: 24px × 24px
Feature icons: 32px × 32px
Avatar/logo: 40px × 40px, 64px × 64px
```

### Icon Colors
```
Primary: #2563EB
Secondary: #6B7280
Success: #10B981
Warning: #F59E0B
Error: #DC2626
Info: #3B82F6
```

### Commonly Used Icons
```
Search: 🔍
Bookmark: 📌
Settings: ⚙️
Close: ×
Back: ←
Forward: →
External link: 🔗
Document: 📄
Folder: 📁
User: 👤
AI/Robot: 🤖
Send: ➤
Filter: ⚡
```

---

## 📱 RESPONSIVE BEHAVIOR

### Breakpoint System
```css
/* Mobile First */
@media (min-width: 320px) {
  /* Mobile styles */
}

@media (min-width: 768px) {
  /* Tablet styles */
  .sidebar { display: block; }
  .container { padding: 0 32px; }
}

@media (min-width: 1024px) {
  /* Desktop styles */
  .grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1440px) {
  /* Wide desktop styles */
  .container { max-width: 1440px; }
  .grid { grid-template-columns: repeat(3, 1fr); }
}
```

### Mobile Adaptations (<768px)

**Landing Page:**
```
Hero title: 48px → 36px
Hero subtitle: 20px → 16px
Container padding: 80px → 24px
Category tabs: Horizontal scroll with snap
Statistics grid: 1 column
Search bar height: 64px → 52px
```

**Workspace:**
```
Sidebar: Collapsible drawer (off-canvas)
Toggle button: Top-left hamburger menu
Panels: Stack vertically
AI panel width: 100% when active
Content padding: 32px → 16px
```

**Search Results:**
```
Filters sidebar: Off-canvas drawer
Results padding: 32px → 16px
Paper card: Stack elements vertically
Action buttons: Full width, stacked
```

### Tablet Adaptations (768px - 1024px)

**Landing Page:**
```
Container padding: 40px
Statistics grid: 2 columns
Hero title: 56px
Search bar: Full width with max-width: 700px
```

**Workspace:**
```
Sidebar: Fixed, visible
AI panel: 320px width
Content area: Flexible
Font sizes: Same as desktop
```

**Search Results:**
```
Filters sidebar: 240px fixed
Results area: Flexible
Paper cards: Full layout maintained
```

---

## 🎨 ANIMATION & TRANSITIONS

### Transition Speeds
```css
--transition-fast: 0.15s;
--transition-base: 0.2s;
--transition-slow: 0.3s;
--transition-slower: 0.5s;
```

### Common Animations

**Fade In:**
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

animation: fadeIn 0.3s ease-in-out;
```

**Slide In from Left:**
```css
@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

animation: slideInLeft 0.3s ease-out;
```

**Scale Up:**
```css
@keyframes scaleUp {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

animation: scaleUp 0.2s ease-out;
```

**Hover Lift:**
```css
transition: transform 0.2s ease, box-shadow 0.2s ease;

&:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
```

**Button Press:**
```css
transition: transform 0.1s ease;

&:active {
  transform: scale(0.98);
}
```

### Loading States

**Skeleton Loader:**
```css
background: linear-gradient(
  90deg,
  #F3F4F6 0%,
  #E5E7EB 50%,
  #F3F4F6 100%
);
background-size: 200% 100%;
animation: loading 1.5s ease-in-out infinite;

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

**Spinner:**
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  border: 3px solid #E5E7EB;
  border-top-color: #2563EB;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 0.6s linear infinite;
}
```

---

## 🔍 ACCESSIBILITY REQUIREMENTS

### Focus States
```css
/* Keyboard focus visible */
:focus-visible {
  outline: 2px solid #2563EB;
  outline-offset: 2px;
  border-radius: 4px;
}

/* Remove default outline */
:focus:not(:focus-visible) {
  outline: none;
}
```

### ARIA Labels
```html
<!-- Buttons -->
<button aria-label="Search papers">
  <SearchIcon />
</button>

<!-- Inputs -->
<input aria-label="Search query" placeholder="Search..." />

<!-- Navigation -->
<nav aria-label="Main navigation">
  <a href="/" aria-current="page">Home</a>
</nav>

<!-- Modal -->
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Modal Title</h2>
</div>
```

### Color Contrast
```
/* WCAG AA Standard */
Normal text (16px): 4.5:1 minimum
Large text (24px): 3:1 minimum
UI components: 3:1 minimum

/* Validated combinations */
#111827 on #FFFFFF ✓ (14.6:1)
#374151 on #FFFFFF ✓ (10.7:1)
#6B7280 on #FFFFFF ✓ (4.6:1)
#2563EB on #FFFFFF ✓ (5.5:1)
#FFFFFF on #2563EB ✓ (5.5:1)
```

### Keyboard Navigation
```
Tab: Move forward through interactive elements
Shift+Tab: Move backward
Enter: Activate button/link
Space: Toggle checkbox/radio
Escape: Close modal/dropdown
Arrow keys: Navigate within dropdown/menu
```

---

## 🛠️ IMPLEMENTATION NOTES

### Component Architecture

**File Structure:**
```
src/
├── components/
│   ├── landing/
│   │   ├── SearchPage.tsx
│   │   ├── HeroSection.tsx
│   │   ├── SearchBar.tsx
│   │   └── StatsCards.tsx
│   ├── workspace/
│   │   ├── Workspace.tsx
│   │   ├── Sidebar.tsx
│   │   ├── SavedPapers.tsx
│   │   ├── AIAssistant.tsx
│   │   ├── LiteratureReview.tsx
│   │   └── NotesEditor.tsx
│   ├── search/
│   │   ├── SearchResults.tsx
│   │   ├── FilterSidebar.tsx
│   │   └── PaperCard.tsx
│   └── shared/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Dropdown.tsx
│       └── Card.tsx
├── styles/
│   ├── colors.css
│   ├── typography.css
│   └── spacing.css
└── utils/
    ├── constants.ts
    └── helpers.ts
```

### CSS Variables Setup
```css
:root {
  /* Colors */
  --primary-blue: #2563EB;
  --primary-indigo: #6366F1;
  --gray-50: #F9FAFB;
  --gray-900: #111827;
  
  /* Spacing */
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  
  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --text-base: 16px;
  --text-xl: 20px;
  
  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-base: 0.2s ease;
  --transition-fast: 0.15s ease;
}
```

### Flexible Workspace Windows

**Window System:**
```typescript
interface Window {
  id: string;
  type: 'notes' | 'paper-viewer' | 'ai-assistant' | 'literature-review';
  title: string;
  width: number; // percentage or pixels
  minWidth: number;
  maxWidth: number;
  isResizable: boolean;
}

// Windows can be:
// - Resized horizontally via drag handles
// - Closed individually
// - Added dynamically via "+ Add Window"
// - Reordered by dragging tabs
```

**Resize Handle:**
```css
.resize-handle {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  position: absolute;
  top: 0;
  bottom: 0;
  right: 0;
  z-index: 10;
  
  &:hover,
  &:active {
    background: #2563EB;
  }
}
```

**Window Constraints:**
```
Minimum width: 320px
Maximum width: 70% of viewport
Default widths:
- Sidebar: 280px (fixed)
- Notes panel: 40% (flexible)
- AI Assistant: 380px (flexible)
- Literature Review: Remaining space (flexible)
```

---

## ✅ FINAL CHECKLIST FOR LLM

When implementing, ensure:

- [ ] All colors use exact hex codes from specification
- [ ] Spacing uses the defined spacing scale (4px, 8px, 12px, etc.)
- [ ] Typography matches exact font sizes and weights
- [ ] Hover states include transitions (0.2s ease)
- [ ] Focus states are visible for keyboard navigation
- [ ] Responsive breakpoints adapt layout correctly
- [ ] Icons are sized consistently (16px, 20px, 24px)
- [ ] Cards have consistent border-radius (8px, 12px)
- [ ] Buttons include all interactive states (default, hover, active, disabled)
- [ ] Inputs have proper focus rings with blue outline
- [ ] Shadows match specified values
- [ ] Components are reusable and well-structured
- [ ] Accessibility attributes (aria-labels) are included
- [ ] Loading states are implemented
- [ ] Error states are styled consistently
- [ ] Mobile layout stacks elements vertically
- [ ] Windows in workspace are resizable with drag handles
- [ ] All text content matches exactly from designs

---

## 📞 QUICK REFERENCE SUMMARY

**Key Colors:**
- Primary Blue: `#2563EB`
- Dark Text: `#111827`
- Gray Text: `#6B7280`
- Light Background: `#F9FAFB`
- Border: `#E5E7EB`

**Key Spacing:**
- Small gap: `12px`
- Medium gap: `24px`
- Large gap: `48px`
- Section padding: `32px`

**Key Typography:**
- Hero: `72px / 700`
- Heading: `24px / 600`
- Body: `16px / 400`
- Small: `14px / 400`

**Key Components:**
- Border radius: `8px` (standard), `12px` (large)
- Button height: `44px`
- Input height: `44px`
- Card padding: `24px`

---

**END OF SPECIFICATIONS**

*This document contains all visual specifications needed to rebuild the ResearchHub interface. Use it as the single source of truth for all styling decisions.*