/**
 * Zendesk Help Center API Scraper
 * Fetches articles via Zendesk API and converts to clean Markdown files
 */

import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class ZendeskApiScraper {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || 'https://support.optisigns.com';
    this.apiUrl = `${this.baseUrl}/api/v2/help_center`;
    this.locale = options.locale || 'en-us';
    this.outputDir = options.outputDir || path.join(__dirname, '../articles');
    this.delay = options.delay || 1000;
    this.maxArticles = options.maxArticles || 50;
    
    // Create axios instance with proper headers
    this.api = axios.create({
      timeout: 30000,
      headers: {
        'User-Agent': 'OptiSigns Article Scraper 1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
  }

  /**
   * Sleep for specified milliseconds
   */
  async sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Ensure output directory exists
   */
  async ensureOutputDir() {
    try {
      await fs.mkdir(this.outputDir, { recursive: true });
      console.log(`Output directory ready: ${this.outputDir}`);
    } catch (error) {
      console.error('Error creating output directory:', error);
      throw error;
    }
  }

  /**
   * Fetch all categories from Zendesk API
   */
  async fetchCategories() {
    try {
          console.log('Fetching categories...');
      const response = await this.api.get(`${this.apiUrl}/${this.locale}/categories.json`);
      const categories = response.data.categories || [];
          console.log(`Found ${categories.length} categories`);
      return categories;
    } catch (error) {
      console.error('Error fetching categories:', error.message);
      return [];
    }
  }

  /**
   * Fetch all sections from a category
   */
  async fetchSections(categoryId) {
    try {
      const response = await this.api.get(`${this.apiUrl}/${this.locale}/categories/${categoryId}/sections.json`);
      return response.data.sections || [];
    } catch (error) {
      console.error(`Error fetching sections for category ${categoryId}:`, error.message);
      return [];
    }
  }

  /**
   * Fetch all articles from a section
   */
  async fetchArticles(sectionId) {
    try {
      const response = await this.api.get(`${this.apiUrl}/${this.locale}/sections/${sectionId}/articles.json`);
      return response.data.articles || [];
    } catch (error) {
      console.error(`Error fetching articles for section ${sectionId}:`, error.message);
      return [];
    }
  }

  /**
   * Fetch full article content including body
   */
  async fetchArticleContent(articleId) {
    try {
      await this.sleep(this.delay);
      const response = await this.api.get(`${this.apiUrl}/${this.locale}/articles/${articleId}.json`);
      return response.data.article;
    } catch (error) {
      console.error(`Error fetching article ${articleId}:`, error.message);
      return null;
    }
  }

  /**
   * Convert HTML to clean Markdown
   */
  htmlToMarkdown(html, articleUrl) {
    if (!html) return '';

    let markdown = html
      // Remove unwanted elements
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
      .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '')
      .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '')
      .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '')
      .replace(/<aside[^>]*>[\s\S]*?<\/aside>/gi, '')
      
      // Convert headings
      .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1')
      .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1')
      .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1')
      .replace(/<h4[^>]*>(.*?)<\/h4>/gi, '#### $1')
      .replace(/<h5[^>]*>(.*?)<\/h5>/gi, '##### $1')
      .replace(/<h6[^>]*>(.*?)<\/h6>/gi, '###### $1')
      
      // Convert formatting
      .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
      .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
      .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
      .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
      .replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`')
      
      // Convert links (preserve relative links)
      .replace(/<a[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi, (match, href, text) => {
        // Keep relative links as-is, make absolute links from same domain relative
        if (href.startsWith('/')) {
          return `[${text}](${href})`;
        } else if (href.startsWith(this.baseUrl)) {
          const relativePath = href.replace(this.baseUrl, '');
          return `[${text}](${relativePath})`;
        } else if (href.startsWith('http')) {
          return `[${text}](${href})`;
        } else {
          return `[${text}](${href})`;
        }
      })
      
      // Convert images
      .replace(/<img[^>]*src=["']([^"']*)["'][^>]*alt=["']([^"']*)["'][^>]*>/gi, '![$2]($1)')
      .replace(/<img[^>]*src=["']([^"']*)["'][^>]*>/gi, '![]($1)')
      
      // Convert lists
      .replace(/<ul[^>]*>/gi, '')
      .replace(/<\/ul>/gi, '')
      .replace(/<ol[^>]*>/gi, '')
      .replace(/<\/ol>/gi, '')
      .replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1')
      
      // Convert code blocks
      .replace(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/gi, '```\n$1\n```')
      .replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gi, '```\n$1\n```')
      
      // Convert paragraphs
      .replace(/<p[^>]*>/gi, '')
      .replace(/<\/p>/gi, '\n\n')
      
      // Convert line breaks
      .replace(/<br[^>]*>/gi, '\n')
      
      // Convert divs to line breaks
      .replace(/<div[^>]*>/gi, '')
      .replace(/<\/div>/gi, '\n')
      
      // Remove remaining HTML tags
      .replace(/<[^>]*>/g, '')
      
      // Decode HTML entities
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ')
      

      .replace(/\n\s*\n\s*\n/g, '\n\n') // Multiple newlines to double
      .replace(/\n\s+/g, '\n') //leading spaces on lines
      .replace(/\s+$/gm, '') //trailing spaces
      .trim();

    return markdown;
  }

  /**
   * Generate a slug from title
   */
  generateSlug(title) {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '') //special chars
      .replace(/\s+/g, '-') // Spaces to hyphens
      .replace(/-+/g, '-') // Multiple hyphens to single
      .replace(/^-|-$/g, ''); //leading/trailing hyphens
  }

  /**
   * Save article as Markdown file
   */
  async saveArticleAsMarkdown(article, category, section) {
    try {
      const slug = this.generateSlug(article.title);
      const filename = `${slug}.md`;
      const filepath = path.join(this.outputDir, filename);

      const markdownContent = this.htmlToMarkdown(article.body, article.html_url);

      // Create frontmatter with metadata
      const frontmatter = `---
title: "${article.title.replace(/"/g, '\\"')}"
id: ${article.id}
url: ${article.html_url}
category: "${category?.name || 'Unknown'}"
section: "${section?.name || 'Unknown'}"
author: "${article.author_id || 'Unknown'}"
created_at: "${article.created_at}"
updated_at: "${article.updated_at}"
draft: ${article.draft}
promoted: ${article.promoted}
position: ${article.position}
vote_sum: ${article.vote_sum}
vote_count: ${article.vote_count}
section_id: ${article.section_id}
category_id: ${category?.id || ''}
tags: ${JSON.stringify(article.label_names || [])}
---

`;

      const fullContent = frontmatter + markdownContent;

      await fs.writeFile(filepath, fullContent, 'utf8');
      console.log(`Saved: ${filename} (${markdownContent.length} chars)`);
      
      return {
        filename,
        filepath,
        slug,
        title: article.title,
        length: markdownContent.length
      };
    } catch (error) {
      console.error(`Error saving article ${article.title}:`, error.message);
      return null;
    }
  }

  /**
   * Scrape all articles from OptiSigns Help Center
   */
  async scrapeAllArticles() {
      console.log('Starting help center scraper...');
    console.log(`Target: ${this.baseUrl}`);
    console.log(`Output: ${this.outputDir}`);
    
    await this.ensureOutputDir();

    const categories = await this.fetchCategories();
    if (categories.length === 0) {
      console.log('No categories found');
      return [];
    }

    const savedArticles = [];
    let totalArticles = 0;

    for (const category of categories) {
      if (totalArticles >= this.maxArticles) break;
      
      console.log(`\nProcessing category: ${category.name}`);
      
      const sections = await this.fetchSections(category.id);
      console.log(`   Found ${sections.length} sections`);

      for (const section of sections) {
        if (totalArticles >= this.maxArticles) break;
        
        console.log(`   Processing section: ${section.name}`);
        
        const articles = await this.fetchArticles(section.id);
        console.log(`      Found ${articles.length} articles`);

        for (const articleSummary of articles) {
          if (totalArticles >= this.maxArticles) break;
          
          console.log(`      Fetching: ${articleSummary.title.substring(0, 50)}...`);
          
          const fullArticle = await this.fetchArticleContent(articleSummary.id);
          if (fullArticle) {
            const saved = await this.saveArticleAsMarkdown(fullArticle, category, section);
            if (saved) {
              savedArticles.push(saved);
              totalArticles++;
            }
          }
        }
      }
    }

    console.log(`\nScraping complete!`);
    console.log(`Results:`);
    console.log(`   • Categories processed: ${categories.length}`);
    console.log(`   • Articles saved: ${savedArticles.length}`);
    console.log(`   • Output directory: ${this.outputDir}`);

    return savedArticles;
  }

  /**
   * Generate index file with all articles
   */
  async generateIndex(savedArticles) {
    const indexPath = path.join(this.outputDir, 'README.md');
    
    let indexContent = `# OptiSigns Help Center Articles

This directory contains ${savedArticles.length} articles scraped from the OptiSigns Help Center.

## Articles by Title

`;

    savedArticles
      .sort((a, b) => a.title.localeCompare(b.title))
      .forEach(article => {
        indexContent += `- [${article.title}](${article.filename})\n`;
      });

    indexContent += `
## Scraping Details

- **Source**: ${this.baseUrl}
- **Scraped on**: ${new Date().toISOString()}
- **Total articles**: ${savedArticles.length}
- **Format**: Markdown with YAML frontmatter

## File Structure

Each article includes:
- YAML frontmatter with metadata (title, ID, URLs, dates, etc.)
- Clean Markdown content
- Preserved relative links and code blocks
- Removed navigation and ads

`;

    await fs.writeFile(indexPath, indexContent, 'utf8');
    console.log(`Generated index: README.md`);
  }
}

export default ZendeskApiScraper;
