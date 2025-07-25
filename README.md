# OptiBot Article Scraper & Uploader

Automated system to scrape Zendesk articles and upload them to OpenAI Assistant's vector store.

## 🚀 Quick Start

### 1. Prerequisites Setup

```bash
# Copy environment template
cp .env.sample .env

# Edit .env with your configuration
ASSISTANT_ID=your_assistant_id_here
VECTOR_STORE_ID=your_vector_store_id_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional: can override via command line
```

### 2. Run with Docker

**Option A: Use .env file API key**

```bash
docker build -t optibot .
docker run --rm --env-file .env optibot
```

**Option B: Override API key via command line**

```bash
docker build -t optibot .
docker run --rm -e OPENAI_API_KEY=your_different_key_here --env-file .env optibot
```

### 3. Local Development

```bash
# Use .env file
python3 main.py

# Or override API key
OPENAI_API_KEY=your_different_key_here python3 main.py
```

### 4. Production Deployment

#### DigitalOcean App Platform (Simple)
1. **Create App**: Go to https://cloud.digitalocean.com/apps → Create App
2. **Connect GitHub**: Select `nghiahuynh091/info_scraper` repo
3. **Choose Job**: Select "Job" type (not Service)
4. **Set Environment Variables**:
   - `OPENAI_API_KEY`: Your actual API key
   - `ASSISTANT_ID`: Your assistant ID  
   - `VECTOR_STORE_ID`: Your vector store ID
5. **Deploy**: Click "Create Resources"
6. **Run**: Manually trigger from DigitalOcean dashboard whenever needed

**Cost**: ~$0.02 per job execution

#### Option B: DigitalOcean App Platform

1. Deploy using `.do/app.yaml`
2. Set `OPENAI_API_KEY` in DigitalOcean dashboard
3. Manual or API-triggered execution

#### Option B: DigitalOcean App Platform

1. Deploy using `.do/app.yaml`
2. Set environment variables in DigitalOcean dashboard
3. Manual or API-triggered execution

## 📊 Monitoring & Logs

- **GitHub Actions**: Check Actions tab for execution logs
- **Local Reports**: Generated in `reports/latest_log.json`
- **DigitalOcean**: App dashboard → Activity tab

## 🔐 Security

- ✅ No API keys in code
- ✅ Environment variables only
- ✅ `.env` files ignored by git
- ✅ Template files for easy setup
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
