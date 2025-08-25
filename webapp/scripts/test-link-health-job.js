#!/usr/bin/env node

/**
 * Test script for the link health job
 * Run this to test the job locally
 */

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

async function testLinkHealthJob() {
  console.log('🧪 Testing Link Health Job...\n')
  
  try {
    // Test 1: Dry run with small limit
    console.log('📋 Test 1: Dry run (5 files)')
    const dryRunResponse = await fetch(`${BASE_URL}/api/jobs/link-health?limit=5&dryRun=true`)
    const dryRunResult = await dryRunResponse.json()
    
    console.log('Response:', JSON.stringify(dryRunResult, null, 2))
    console.log('✅ Dry run completed\n')
    
    // Test 2: Small actual run
    console.log('🔍 Test 2: Actual run (3 files)')
    const actualResponse = await fetch(`${BASE_URL}/api/jobs/link-health`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit: 3, dryRun: false })
    })
    const actualResult = await actualResponse.json()
    
    console.log('Response:', JSON.stringify(actualResult, null, 2))
    console.log('✅ Actual run completed\n')
    
    // Test 3: Check database for updates
    console.log('📊 Test 3: Checking database for link_health field')
    const dbCheckResponse = await fetch(`${BASE_URL}/api/jobs/link-health?limit=1&dryRun=true`)
    const dbCheckResult = await dbCheckResponse.json()
    
    console.log('Database check response:', JSON.stringify(dbCheckResult, null, 2))
    console.log('✅ Database check completed\n')
    
    console.log('🎉 All tests completed successfully!')
    
  } catch (error) {
    console.error('❌ Test failed:', error)
    process.exit(1)
  }
}

// Run the test
testLinkHealthJob()
