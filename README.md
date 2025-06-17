# Custom Search App

A FastAPI-based search application for internal team use with Excel data sources.

## Features

- Search across multiple Excel files
- Real-time search with highlighting
- Caching for improved performance
- Support for 30+ concurrent users

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app.main:app --reload
```

3. Access at: http://localhost:8000

## Vercel Deployment

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel
```

3. Follow the prompts to connect your GitHub repository

## Data Files

Place your Excel files in the `data/` directory:
- `category_pdp_plp.xlsx`
- `attributes.xlsx`
- `concat_rule.xlsx`
- `category_tree.xlsx`
- `rejection_reasons.xlsx`
- `ptypes_dump.xlsx`

## Cache Management

- View cache stats: `GET /cache/stats`
- Clear cache: `POST /cache/clear`

## Team Access

Once deployed, share the Vercel URL with your team members for access. 