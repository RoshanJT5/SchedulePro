#!/bin/bash
# Security Check Script - Verify no secrets are exposed

echo "🔍 Checking for exposed secrets in code..."
echo ""

# Check for exposed API keys
echo "1. Checking for exposed API keys (sk-or-v1-)..."
EXPOSED_KEYS=$(git grep -i "sk-or-v1-" -- ':!.env.example' ':!SECURITY_FIX_SUMMARY.md' ':!security-check.sh' 2>/dev/null || echo "")
if [ -z "$EXPOSED_KEYS" ]; then
    echo "   ✅ No exposed API keys found"
else
    echo "   ❌ WARNING: Exposed API keys found:"
    echo "$EXPOSED_KEYS"
fi

echo ""

# Check for hardcoded passwords/secrets
echo "2. Checking for hardcoded secrets..."
HARDCODED=$(git grep -E "(password|secret|api_key|apikey).*=.*['\"][a-zA-Z0-9]{10,}" -- '*.py' '*.js' ':!.env.example' 2>/dev/null | grep -v "getenv\|os.getenv\|process.env" || echo "")
if [ -z "$HARDCODED" ]; then
    echo "   ✅ No hardcoded secrets found"
else
    echo "   ⚠️  Potential hardcoded values (verify these):"
    echo "$HARDCODED"
fi

echo ""

# Check .gitignore coverage
echo "3. Checking .gitignore coverage..."
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "   ✅ .env is in .gitignore"
else
    echo "   ❌ WARNING: .env not in .gitignore!"
fi

if grep -q "\.db$\|\.sqlite" .gitignore 2>/dev/null; then
    echo "   ✅ Database files are in .gitignore"
else
    echo "   ⚠️  Database files might not be ignored"
fi

if grep -q "\.log$" .gitignore 2>/dev/null; then
    echo "   ✅ Log files are in .gitignore"
else
    echo "   ⚠️  Log files might not be ignored"
fi

echo ""

# Check if .env exists and is not tracked
echo "4. Checking .env file status..."
if [ -f .env ]; then
    echo "   ✅ .env file exists"
    if git ls-files --error-unmatch .env 2>/dev/null; then
        echo "   ❌ CRITICAL: .env is tracked by Git! Run: git rm --cached .env"
    else
        echo "   ✅ .env is not tracked by Git"
    fi
else
    echo "   ⚠️  .env file doesn't exist (create from .env.example)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Security Check Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
