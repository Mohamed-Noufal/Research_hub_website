    def _is_valid_paper(self, paper: Dict) -> bool:
        """
        Validate paper quality before saving to database
        
        Args:
            paper: Paper dictionary
            
        Returns:
            True if paper meets minimum quality standards
        """
        # Must have a meaningful title
        title = paper.get('title', '').strip()
        if not title or len(title) < 10:
            return False
        
        # Must have EITHER abstract OR authors
        abstract = paper.get('abstract', '').strip()
        authors = paper.get('authors', [])
        
        has_abstract = abstract and len(abstract) > 50
        has_authors = authors and len(authors) > 0
        
        # At least one of them must exist
        return has_abstract or has_authors
