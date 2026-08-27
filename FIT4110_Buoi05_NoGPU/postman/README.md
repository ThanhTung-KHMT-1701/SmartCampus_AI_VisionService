# SmartCampus AI Vision NoGPU - Postman Collection

## Overview

This folder contains Postman collection and environment files for testing the SmartCampus AI Vision Service (No GPU version).

## Files

- `collections/SmartCampus_AI_Vision_NoGPU_Integration.postman_collection.json` - Main API test collection
- `environments/SmartCampus_AI_Vision_NoGPU.postman_environment.json` - Environment variables

## Test Coverage

The collection includes the following test scenarios:

1. **Gateway Health Check** - Verify gateway service is running
2. **Internal Service Health Check** - Verify AI vision service is healthy
3. **Detect Objects - Valid Image URL** - Test object detection with valid input
4. **Get Detection History** - Retrieve detection history with pagination
5. **Get Detection by ID** - Get specific detection result by ID
6. **Detect Objects - Invalid Auth** - Test authentication failure (401)
7. **Detect Objects - Invalid Image URL** - Test error handling for invalid URLs

## Running Tests

### Using Postman GUI

1. Import collection: `collections/SmartCampus_AI_Vision_NoGPU_Integration.postman_collection.json`
2. Import environment: `environments/SmartCampus_AI_Vision_NoGPU.postman_environment.json`
3. Select the environment from dropdown
4. Run the collection using Collection Runner

### Using Newman (CLI)

```bash
# Install newman if not already installed
npm install -g newman

# Run the collection
newman run postman/collections/SmartCampus_AI_Vision_NoGPU_Integration.postman_collection.json \
  -e postman/environments/SmartCampus_AI_Vision_NoGPU.postman_environment.json \
  -r cli,html \
  --reporter-html-export reports/test-report.html

# Run with detailed output
newman run postman/collections/SmartCampus_AI_Vision_NoGPU_Integration.postman_collection.json \
  -e postman/environments/SmartCampus_AI_Vision_NoGPU.postman_environment.json \
  --verbose
```

## Environment Variables

- `gateway_url`: Gateway service URL (default: http://localhost:8000)
- `auth_token`: Authentication token for API requests
- `internal_service_url`: Internal AI vision service URL (default: http://localhost:8001)

## Expected Results

All tests should pass when the services are running correctly:
- ✅ Health checks return 200
- ✅ Object detection processes images successfully
- ✅ History and retrieval endpoints work properly
- ✅ Authentication is enforced (401 for invalid tokens)
- ✅ Error handling works for invalid inputs

## Notes

- Make sure Docker services are running before executing tests
- The first detection request may take longer due to model initialization
- Invalid image URL test may take longer due to timeout settings
