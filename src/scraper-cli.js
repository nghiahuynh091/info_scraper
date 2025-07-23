#!/usr/bin/env node

import ZendeskApiScraper from './zendesk-api-scraper.js';
import fs from 'fs';

const isCleanMode = process.argv.includes('--clean');

if (isCleanMode) {
  console.log('Zendesk Help Center Scraper - Clean Mode');
  console.log('Cleaning output directories...');
  
  const dirsToClean = ['./articles', './output'];
  
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
console.log('Scraping OptiSigns help center...');

const scraper = new ZendeskApiScraper({
  baseUrl: 'https://support.optisigns.com',
  maxArticles: 50,
  delay: 1500
});

try {
  const savedArticles = await scraper.scrapeAllArticles();
  await scraper.generateIndex(savedArticles);
  
  // Update scrape timestamp in cache for OptiBot (preserve existing data)
  let scrapeCache = {};
  
  // Load existing cache if it exists
  if (fs.existsSync('.optibot_cache.json')) {
    try {
      const existingCache = fs.readFileSync('.optibot_cache.json', 'utf8');
      scrapeCache = JSON.parse(existingCache);
      console.log('Loaded existing cache with article data');
    } catch (error) {
      console.log('Could not load existing cache, creating new one');
    }
  }
  
  // Update only the metadata section
  scrapeCache._metadata = {
    ...scrapeCache._metadata, // Preserve any existing metadata
    last_scrape_time: new Date().toISOString(),
    version: '2.0',
    scrape_count: savedArticles.length
  };
  
  fs.writeFileSync('.optibot_cache.json', JSON.stringify(scrapeCache, null, 2));
  console.log(`Scrape cache updated: ${scrapeCache._metadata.last_scrape_time}`);
  
  console.log('Scraping completed successfully!');
  console.log(`Articles saved: ${savedArticles.length}`);
  console.log('Check the ./articles directory for results');
  
} catch (error) {
  console.error('Scraping failed:', error.message);
  process.exit(1);
}
