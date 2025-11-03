#!/bin/bash

# Test script to verify the new stats output format
echo "Testing new stats output format..."
echo ""
echo "Starting gemini with a simple test task..."
echo ""

# Create a temporary test file
echo "console.log('hello world');" > /tmp/gemini-test.js

# Run gemini with a simple task and then exit
echo -e "read the file /tmp/gemini-test.js\nexit" | ./bundle/gemini

# Clean up
rm -f /tmp/gemini-test.js

echo ""
echo "Test completed. Check the output above for the detailed Performance breakdown."
