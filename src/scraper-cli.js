#!/usr/bin/env node


import 'dotenv/config';
import ZendeskApiScraper from './zendesk-api-scraper.js';
import fs from 'fs';

const isCleanMode = process.argv.includes('clean');

if (isCleanMode) {
  console.log('Zendesk Help Center Scraper - Clean Mode');
  console.log('Cleaning output directories...');
  
  const dirsToClean = ['./articles', './reports', './.bot_cache.json' ];
  
  for (const dir of dirsToClean) {
    if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true, force: true });
      console.log(`Removed: ${dir}`);
    }
  }
  
  console.log('Clean completed!');
  process.exit(0);
}

console.log('Zendesk Help Center Scraper');
console.log('Scraping the help center...');


const scraper = new ZendeskApiScraper({
  baseUrl: process.env.BASE_URL,
  maxArticles: process.env.MAX_ARTICLES ? Number(process.env.MAX_ARTICLES) : undefined
});

try {
  const savedArticles = await scraper.scrapeAllArticles();
  
  let scrapeCache = {};
  
  if (fs.existsSync('.bot_cache.json')) {
    try {
      const existingCache = fs.readFileSync('.bot_cache.json', 'utf8');
      scrapeCache = JSON.parse(existingCache);
      console.log('Loaded existing cache with article data');
    } catch (error) {
      console.log('Could not load existing cache, creating new one');
    }
  }
  
  scrapeCache._metadata = {
    ...scrapeCache._metadata, // Preserve any existing metadata
    last_scrape_time: new Date().toISOString(),
    scrape_count: savedArticles.length
  };
  
  fs.writeFileSync('.bot_cache.json', JSON.stringify(scrapeCache, null, 2));
  console.log(`Scrape cache updated: ${scrapeCache._metadata.last_scrape_time}`);
  
  console.log('Scraping completed successfully!');
  console.log(`Articles saved: ${savedArticles.length}`);
  console.log('Check the ./articles directory for results');
  
} catch (error) {
  console.error('Scraping failed:', error.message);
  process.exit(1);
}
