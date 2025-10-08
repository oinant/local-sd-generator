# local-sd-generator
Simple CLI and API tools allowing to prompt your local StableDiffusion WebUI API with prompts variation

## Development Setup

### Configuration
1. Copy the environment configuration:
```bash
cd api
cp .env.example .env
```

2. Edit `.env` and replace the example GUIDs with your own:
```bash
# Generate new GUIDs (Linux/Mac)
uuidgen

# Or use online generators like https://www.uuidgenerator.net/
```

3. Update the GUIDs in `.env`:
```env
VALID_GUIDS=["your-admin-guid", "your-user-guid", "your-readonly-guid"]
READ_ONLY_GUIDS=["your-readonly-guid"]
```

### Backend API (FastAPI)
```bash
cd api
pip install -e .
python -m uvicorn main:app --reload
```

### Frontend (Vue.js)
```bash
cd front
npm install
npm run serve
```

### Authentication
Use any of the GUIDs configured in your `.env` file as Bearer tokens:
```
Authorization: Bearer your-admin-guid
```
