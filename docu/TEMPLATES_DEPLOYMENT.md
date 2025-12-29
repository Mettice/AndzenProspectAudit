# Templates Deployment Status

## ✅ Templates are Backend-Only (Railway)

The `templates/` directory contains HTML templates used by the **backend** (Railway) to generate audit reports. They are **NOT** needed for the frontend (Vercel).

## 📁 Template Structure

```
templates/
├── assets/
│   ├── andzen_logo.png.placeholder
│   └── styles.css
├── components/          # Reusable template components
├── sections/            # Report section templates
├── dashboard/          # Dashboard images
├── audit_report.html
├── audit_template.html
├── base.html
└── comprehensive_audit_template.html
```

## 🚂 Railway Deployment

**Status**: ✅ Templates are automatically included

- Railway deploys the **entire GitHub repository**
- Templates are at the root level: `templates/`
- Backend code looks for templates at: `Path(__file__).parent.parent.parent.parent / "templates"`
- This resolves to: `{project_root}/templates/`

**No special configuration needed** - Railway will have access to all templates.

## 🌐 Vercel Deployment

**Status**: ✅ Templates are NOT needed

- Vercel only deploys the `frontend/` directory
- Templates are not used by the frontend
- Frontend only needs: `index.html`, `style.css`, and `config.js`

## ✅ Verification

To verify templates are available on Railway:

1. Check Railway logs after deployment
2. Test report generation - if templates are missing, you'll see errors like:
   - `TemplateNotFound: comprehensive_audit_template.html`
   - `FileNotFoundError: templates/...`

## 📝 Template Usage

Templates are loaded by:
- `api/services/report/__init__.py` - Main report service
- Uses Jinja2 `FileSystemLoader` to load templates
- Path resolution: `api/services/report/__init__.py` → up 4 levels → `templates/`

## 🔍 If Templates Are Missing

If you encounter template errors on Railway:

1. **Check Railway deployment logs** - verify all files are deployed
2. **Verify template path** - ensure `templates/` is at project root
3. **Check .gitignore** - templates should NOT be ignored
4. **Manual verification**:
   ```bash
   # SSH into Railway or check deployment
   ls -la templates/
   ```

## ✅ Current Status

- ✅ Templates are in Git repository
- ✅ Templates are NOT in .gitignore
- ✅ Railway will deploy all files including templates
- ✅ Backend code correctly references templates directory
- ✅ No additional configuration needed

