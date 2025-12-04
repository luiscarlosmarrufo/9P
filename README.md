# 9P Social Analytics

AI-powered social media analytics tool that classifies brand mentions across the 9Ps marketing framework using Claude AI.

![9P Social Analytics](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=flat-square&logo=typescript)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)

## ✨ Features

- 🔍 **Reddit Post Analysis** - Fetch and analyze brand mentions from Reddit
- 🤖 **AI Classification** - Classify posts into 9Ps categories using Claude 3.5 Haiku
- 📊 **Interactive Dashboard** - Visualize sentiment, category distribution, and trends
- 🎯 **Smart Filtering** - Filter by sentiment, category, source, and search text
- 💰 **Cost Optimization** - Reuses classifications to save up to 90% on API costs
- 📈 **Strategic Insights** - Generate AI-powered recommendations and opportunities
- 🌙 **Dark Theme** - Beautiful purple-accented dark mode interface

## 🚀 Quick Start

**For Users (Non-Technical):**

👉 **[Read the Complete Setup Guide](SETUP_GUIDE.md)** 👈

Just follow the step-by-step instructions for Windows or Mac!

**TL;DR:**
1. Install Docker Desktop
2. Download this project
3. Run `docker-compose up`
4. Open http://localhost:3000

## 📚 The 9Ps Sustainability Framework

The app classifies social media posts using a sustainability-focused framework:

1. **Product** - Transparent production process, ethically sourced materials, eco-design, durability, full traceability, and recyclability
2. **Price** - Fair value creation accounting for environmental costs, social equity, transparency, and affordability while discouraging overconsumption
3. **Place** - Equitable access through socially and environmentally responsible channels, local sourcing, low-carbon logistics, and ethical partnerships
4. **Publicity** - Total transparency avoiding greenwashing, ethical and truthful communication aligned with sustainable values
5. **Production** - Ethical and efficient manufacturing with renewable energy, waste reduction, water efficiency, and fair labor conditions
6. **Pre-Consumption** - Strategies creating positive environmental and social footprint before consumption begins
7. **Disposal** - Post-consumption practices including recycling, reusing, composting, and circular economy principles
8. **Purpose Drive** - Shared intention guiding actions to generate collective well-being reflected in brand behavior
9. **People** - Direct, participatory, and transparent relationships with stakeholders and communities

## 🛠️ Tech Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind CSS
- **UI Components:** Shadcn UI, Recharts
- **Database:** Supabase (PostgreSQL)
- **AI:** Claude 3.5 Haiku (Anthropic)
- **Data Source:** Reddit API
- **Deployment:** Docker

## 📖 Documentation

- **[Setup Guide](SETUP_GUIDE.md)** - Complete installation instructions
- **[Classification Optimization](CLASSIFICATION_OPTIMIZATION.md)** - How the cost-saving system works
- **Database Schema:** See `supabase/schema.sql`
- **Migrations:** See `supabase/migrations/`

## 🎯 How It Works

1. **Fetch Posts** - Search Reddit for brand mentions within a date range
2. **Store Posts** - Save unique posts to Supabase (shared across analyses)
3. **Check Classifications** - See which posts already have AI classifications
4. **Classify New Posts** - Only send unclassified posts to Claude AI (saves money!)
5. **Generate Dashboard** - Visualize sentiment, categories, and trends
6. **AI Insights** - Optionally generate strategic recommendations

## 💡 Key Features Explained

### Classification Reuse (Cost Optimization)
Re-analyzing the same brand multiple times? The app **reuses existing classifications** instead of calling the Claude API again.

**Example:**
- First analysis of "Nike" with 50 posts = 50 API calls (~$0.03)
- Second analysis of "Nike" with same 50 posts = **0 API calls** (~$0.00)
- **67-90% cost savings** on repeated analyses!

See [CLASSIFICATION_OPTIMIZATION.md](CLASSIFICATION_OPTIMIZATION.md) for details.

### Advanced Filtering
The dashboard includes powerful filters that affect all visualizations:
- **Sentiment:** Filter by positive, neutral, or negative
- **Categories:** Filter by any 9Ps category
- **Source:** Filter by data source (currently Reddit)
- **Search:** Full-text search across posts, authors, subreddits

### Multiple Visualizations
- **Pie Chart:** Overall sentiment distribution
- **Radar Chart:** 9Ps category coverage
- **Stacked Bar Chart:** Sentiment breakdown within each category
- **Data Table:** Detailed post-by-post analysis

## 🔐 Security & Privacy

- **Supabase Credentials:** The `NEXT_PUBLIC_SUPABASE_ANON_KEY` is safe to share (it's public by design)
- **Row Level Security:** Enabled on Supabase to prevent unauthorized access
- **API Keys:** Users configure their own Reddit and Anthropic API keys (stored locally in browser)
- **Shared Database:** All users of this instance share the same Supabase database

## 🐳 Docker Deployment

The app is pre-configured with Docker for easy deployment:

```bash
# Start the app
docker-compose up

# Start in background
docker-compose up -d

# Stop the app
docker-compose down

# Rebuild after updates
docker-compose up --build
```

**Included in Docker:**
- ✅ Next.js app with all dependencies
- ✅ Supabase credentials (pre-configured)
- ✅ Production-optimized build
- ✅ Auto-restart on failure

## 📊 Database Schema

The app uses a many-to-many relationship between posts and analyses:

```
analyses ←→ analysis_posts ←→ posts ←→ classifications
```

This allows:
- Multiple analyses to share the same posts
- One classification per post (reused across analyses)
- Efficient storage and cost optimization

## 🚀 Development

Want to modify the code?

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📝 Environment Variables

When running locally (not Docker), create `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

**Note:** Users configure Reddit and Anthropic keys in the app Settings (not in .env).

## 🤝 Contributing

This is a personal project, but suggestions are welcome! Feel free to:
- Report bugs
- Suggest features
- Share your analyses

## 📄 License

This project is for educational and personal use.

## 🙏 Credits

- **AI:** Powered by [Anthropic Claude](https://www.anthropic.com/)
- **Data:** Sourced from [Reddit](https://www.reddit.com/)
- **Database:** Hosted on [Supabase](https://supabase.com/)
- **UI Components:** [Shadcn UI](https://ui.shadcn.com/)
- **Charts:** [Recharts](https://recharts.org/)

---

**Made with ❤️ using Next.js, TypeScript, and Claude AI**

**Need help?** Check the [Setup Guide](SETUP_GUIDE.md) or open an issue!
