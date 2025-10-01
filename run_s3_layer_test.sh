#!/bin/bash

echo "========================================"
echo "S3 3-Layer Integration Test Runner"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with AWS credentials"
    echo "You can copy .env.example and fill in your credentials"
    exit 1
fi

echo "✓ Found .env file"
echo ""

# Run test using docker-compose
echo "Starting test in Docker container..."
echo ""

docker-compose run --rm data-processor python tests/test_s3_three_layer_integration.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✓ Test completed successfully!"
else
    echo ""
    echo "❌ Test failed with exit code $exit_code"
fi

exit $exit_code