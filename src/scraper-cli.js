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
  maxArticles: 2,
  delay: 1500
});

try {
  const savedArticles = await scraper.scrapeAllArticles();
  await scraper.generateIndex(savedArticles);
  
  console.log('Scraping completed successfully!');
  console.log(`Articles saved: ${savedArticles.length}`);
  console.log('Check the ./articles directory for results');
  
} catch (error) {
  console.error('Scraping failed:', error.message);
  process.exit(1);
}
