#!/bin/bash
# Design Rules Compliance Linter for SafarSathi UI
# Enforces rules from docs/DESIGN_RULES.md

set -e

ERRORS=0

echo "Running SafarSathi Design Rules Linter..."

if [ ! -d "frontend/src" ]; then
    echo "No frontend/src directory found. Skipping frontend lint."
    exit 0
fi

# 1. Em-dash and En-dash check (Use commas, periods, or colons instead)
echo "Checking for em dashes and en dashes in frontend/src..."
if grep -rnE "(\xE2\x80\x94|\xE2\x80\x93|—|–)" frontend/src/ 2>/dev/null; then
    echo "❌ ERROR: Found em-dash (—) or en-dash (–) in frontend/src. Use commas, colons, or periods."
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No em/en dashes found."
fi

# 2. Decorative gradients / Purple gradients check
echo "Checking for decorative gradient backgrounds..."
if grep -rnE "(from-purple|to-purple|from-indigo|to-pink|bg-gradient)" frontend/src/ 2>/dev/null; then
    echo "❌ ERROR: Found forbidden gradient classes in frontend/src. Use solid colors with high contrast."
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No forbidden gradients found."
fi

# 3. Pill buttons check (Use rounded-md / rounded-lg, 6-8px, never rounded-full for buttons)
echo "Checking for pill-shaped buttons (rounded-full)..."
if grep -rnE "rounded-full" frontend/src/ 2>/dev/null | grep -E "(button|<button|Button)" ; then
    echo "❌ ERROR: Found pill-shaped rounded-full buttons. Use 6px to 8px border radius (rounded-md/rounded-lg)."
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No pill buttons found."
fi

# 4. AI-sounding buzzword copy check
echo "Checking for AI buzzwords in copy..."
if grep -rniE "(revolutionize|seamless|unlock|empower|elevate|game-changer)" frontend/src/ 2>/dev/null; then
    echo "❌ ERROR: Found AI buzzword filler in frontend copy. Use plain, factual, and specific sentences."
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No buzzwords found."
fi

# 5. Badges check ("Made with", "Built with")
echo "Checking for 'Made with' / 'Built with' badges..."
if grep -rniE "(made with|built with)" frontend/src/ 2>/dev/null; then
    echo "❌ ERROR: Found 'Made with' / 'Built with' template badge in frontend/src."
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No template badges found."
fi

if [ $ERRORS -gt 0 ]; then
    echo "❌ Design lint failed with $ERRORS error(s)."
    exit 1
fi

echo "✅ All design lint checks passed cleanly."
exit 0
