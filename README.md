# Zendesk Help Center Scraper

A Node.js tool that scrapes articles from a Zendesk Help Center and converts them to Markdown files.

## Installation

```bash
npm install
```

## Usage

Run the scraper:

```bash
npm start
```

Clean output directories:

```bash
npm run clean
```

This will scrape the OptiSigns help center and save all articles as Markdown files in the `articles` directory.

## Features

- Scrapes all articles from a Zendesk Help Center
- Converts HTML content to clean Markdown
- Preserves article metadata in frontmatter
- Organizes output by category and section
- Generates a complete index of all articles

## Output

The scraper creates:

- Individual Markdown files for each article
- Organized folder structure by category/section
- Complete frontmatter with article metadata
- Index file listing all scraped articles

## Requirements

- Node.js 14+
- Internet connection to access the help center

## Configuration

Edit `src/scraper-cli.js` to change the target help center URL and the number of expected scraped articles.
