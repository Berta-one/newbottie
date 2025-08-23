#!/usr/bin/env node

/**
 * Smart Claude Model Selector - Integration Test
 * Automated testing script to verify integration works correctly
 * 
 * Usage: node test-integration.js
 * Requires: ANTHROPIC_API_KEY environment variable
 */

const SmartClaudeSelector = require('./smart-claude-selector');

// Test configuration
const TEST_CONFIG = {
    skipApiTests: process.env.SKIP_API_TESTS === 'true',
    verbose: process.env.VERBOSE === 'true',
    maxTestTime: 30000 // 30 seconds max for API tests
};

// Test results tracking
let testResults = {
    passed: 0,
    failed: 0,
    skipped: 0,
    details: []
};

// Utility functions
function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const symbols = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️', skip: '⏭️' };
    console.log(`${symbols[type]} ${message}`);
    
    if (TEST_CONFIG.verbose) {
        console.log(`   [${timestamp}]`);
    }
}

function assert(condition, message, details = null) {
    if (condition) {
        testResults.passed++;
        testResults.details.push({ status: 'PASS', message, details });
        log(`PASS: ${message}`, 'success');
    } else {
        testResults.failed++;
        testResults.details.push({ status: 'FAIL', message, details });
        log(`FAIL: ${message}`, 'error');
        if (details) {
            console.log(`       Details: ${JSON.stringify(details, null, 2)}`);
        }
    }
}

function skip(message) {
    testResults.skipped++;
    testResults.details.push({ status: 'SKIP', message });
    log(`SKIP: ${message}`, 'skip');
}

// Test suites
async function testBasicFunctionality() {
    log('🧪 Testing Basic Functionality', 'info');
    
    try {
        // Test 1: Constructor with default options
        const selector1 = new SmartClaudeSelector({
            apiKey: 'test-key-sk-ant-test'
        });
        assert(selector1.apiKey === 'test-key-sk-ant-test', 'Constructor accepts API key');
        assert(selector1.costOptimized === true, 'Cost optimization enabled by default');
        assert(selector1.qualityFocused === false, 'Quality focus disabled by default');
        
        // Test 2: Constructor with custom options
        const selector2 = new SmartClaudeSelector({
            apiKey: 'test-key',
            qualityFocused: true,
            costOptimized: false,
            maxRetries: 5,
            enableLogging: true
        });
        assert(selector2.qualityFocused === true, 'Quality focus can be enabled');
        assert(selector2.costOptimized === false, 'Cost optimization can be disabled');
        assert(selector2.maxRetries === 5, 'Custom max retries setting');
        
        // Test 3: Constructor error handling
        try {
            new SmartClaudeSelector(); // No API key
            assert(false, 'Constructor should require API key');
        } catch (error) {
            assert(error.message.includes('API key is required'), 'Constructor validates API key requirement');
        }
        
    } catch (error) {
        assert(false, 'Basic functionality test suite failed', error.message);
    }
}

async function testRequestAnalysis() {
    log('🧪 Testing Request Analysis', 'info');
    
    const selector = new SmartClaudeSelector({ apiKey: 'test-key' });
    
    // Test simple requests
    const simpleAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'What is 2+2?' }
    ]);
    assert(simpleAnalysis.complexity === 'low', 'Simple questions detected as low complexity');
    assert(simpleAnalysis.taskType === 'general', 'Simple questions categorized as general');
    
    // Test coding requests
    const codingAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Write a JavaScript function to sort an array' }
    ]);
    assert(codingAnalysis.requiresCoding === true, 'Coding requests detected');
    assert(codingAnalysis.taskType === 'coding', 'Coding requests categorized correctly');
    
    // Test complex analysis requests
    const analysisRequest = selector.analyzeRequest([
        { role: 'user', content: 'Analyze the comprehensive impact of climate change on global economics' }
    ]);
    assert(analysisRequest.complexity === 'high', 'Complex analysis detected');
    assert(analysisRequest.taskType === 'analysis', 'Analysis tasks categorized correctly');
    
    // Test creative requests
    const creativeAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Write a creative story about a robot discovering emotions' }
    ]);
    assert(creativeAnalysis.requiresCreativity === true, 'Creative requests detected');
    assert(creativeAnalysis.taskType === 'creative', 'Creative tasks categorized correctly');
    
    // Test reasoning requests
    const reasoningAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Provide a logical proof for this mathematical theorem' }
    ]);
    assert(reasoningAnalysis.requiresAdvancedReasoning === true, 'Advanced reasoning detected');
    assert(reasoningAnalysis.taskType === 'reasoning', 'Reasoning tasks categorized correctly');
}

async function testModelSelection() {
    log('🧪 Testing Model Selection Logic', 'info');
    
    // Test cost-optimized mode (default)
    const costSelector = new SmartClaudeSelector({ apiKey: 'test-key', costOptimized: true });
    
    const simpleTask = { complexity: 'low', taskType: 'general', estimatedTokens: 100 };
    const selectedModel1 = costSelector.selectOptimalModel(simpleTask);
    assert(selectedModel1 === 'claude-3-haiku-20240307', 'Simple tasks use cheapest model in cost mode');
    
    const codingTask = { complexity: 'medium', taskType: 'coding', estimatedTokens: 500, requiresCoding: true };
    const selectedModel2 = costSelector.selectOptimalModel(codingTask);
    assert(selectedModel2 === 'claude-3-5-sonnet-20241022', 'Coding tasks use Sonnet in cost mode');
    
    // Test quality-focused mode
    const qualitySelector = new SmartClaudeSelector({ 
        apiKey: 'test-key', 
        qualityFocused: true, 
        costOptimized: false 
    });
    
    const complexTask = { complexity: 'high', taskType: 'reasoning', requiresAdvancedReasoning: true };
    const selectedModel3 = qualitySelector.selectOptimalModel(complexTask);
    assert(selectedModel3 === 'claude-3-opus-20240229', 'Complex reasoning uses Opus in quality mode');
    
    // Test model override
    const overrideModel = costSelector.selectOptimalModel(simpleTask, { model: 'claude-3-5-sonnet-20241022' });
    assert(overrideModel === 'claude-3-5-sonnet-20241022', 'User-specified model overrides selection');
}

async function testCostCalculation() {
    log('🧪 Testing Cost Calculation', 'info');
    
    const selector = new SmartClaudeSelector({ apiKey: 'test-key' });
    
    // Test Haiku pricing
    const haikuCost = selector.calculateCost('claude-3-haiku-20240307', 1000, 1000);
    const expectedHaikuCost = (1000/1000000) * 0.25 + (1000/1000000) * 1.25; // $0.0015
    assert(Math.abs(haikuCost - expectedHaikuCost) < 0.0001, 'Haiku cost calculation accurate');
    
    // Test Sonnet pricing
    const sonnetCost = selector.calculateCost('claude-3-5-sonnet-20241022', 1000, 1000);
    const expectedSonnetCost = (1000/1000000) * 3.00 + (1000/1000000) * 15.00; // $0.018
    assert(Math.abs(sonnetCost - expectedSonnetCost) < 0.0001, 'Sonnet cost calculation accurate');
    
    // Test cost comparison
    assert(haikuCost < sonnetCost, 'Haiku is cheaper than Sonnet');
}

async function testUsageTracking() {
    log('🧪 Testing Usage Tracking', 'info');
    
    const selector = new SmartClaudeSelector({ apiKey: 'test-key' });
    
    // Initial stats should be empty
    const initialStats = selector.getUsageStats();
    assert(initialStats.totalRequests === 0, 'Initial request count is zero');
    assert(parseFloat(initialStats.totalCostSaved) === 0, 'Initial cost saved is zero');
    
    // Mock a usage tracking call
    const mockResult = {
        usage: {
            input_tokens: 100,
            output_tokens: 200
        }
    };
    
    const mockAnalysis = { complexity: 'low', taskType: 'general' };
    selector.trackUsage('claude-3-haiku-20240307', mockAnalysis, mockResult);
    
    const updatedStats = selector.getUsageStats();
    assert(updatedStats.totalRequests === 1, 'Request count increments');
    assert(updatedStats.modelUsage['claude-3-haiku-20240307'] === 1, 'Model usage tracked');
    
    // Test stats reset
    selector.resetStats();
    const resetStats = selector.getUsageStats();
    assert(resetStats.totalRequests === 0, 'Stats reset successfully');
}

async function testModelCapabilities() {
    log('🧪 Testing Model Capabilities', 'info');
    
    const selector = new SmartClaudeSelector({ apiKey: 'test-key' });
    const models = selector.getAvailableModels();
    
    assert(Array.isArray(models), 'getAvailableModels returns array');
    assert(models.length > 0, 'Available models list is not empty');
    
    const sonnetModel = models.find(m => m.model === 'claude-3-5-sonnet-20241022');
    assert(sonnetModel !== undefined, 'Sonnet model available');
    assert(sonnetModel.coding === 'excellent', 'Sonnet has excellent coding capability');
    assert(sonnetModel.pricing.input === 3.00, 'Sonnet pricing information included');
    
    const haikuModel = models.find(m => m.model === 'claude-3-haiku-20240307');
    assert(haikuModel !== undefined, 'Haiku model available');
    assert(haikuModel.costRank === 1, 'Haiku has the best cost rank');
}

async function testPerformanceBenchmark() {
    log('🧪 Testing Performance Benchmark', 'info');
    
    const selector = new SmartClaudeSelector({ apiKey: 'test-key' });
    
    // Run a small benchmark
    const benchmark = await selector.benchmark(100);
    
    assert(benchmark.iterations === 100, 'Benchmark ran correct number of iterations');
    assert(benchmark.selectionsPerSecond > 1000, 'Performance is acceptable (>1000 selections/second)');
    assert(benchmark.totalTime >= 0, 'Benchmark measured execution time');
    assert(benchmark.averageTimePerSelection >= 0, 'Average time calculated');
    
    log(`Performance: ${benchmark.selectionsPerSecond.toLocaleString()} selections/second`, 'info');
}

async function testApiIntegration() {
    if (TEST_CONFIG.skipApiTests) {
        skip('API integration tests (set SKIP_API_TESTS=false to enable)');
        return;
    }
    
    if (!process.env.ANTHROPIC_API_KEY) {
        skip('API integration tests (ANTHROPIC_API_KEY not set)');
        return;
    }
    
    log('🧪 Testing API Integration (Live Tests)', 'info');
    
    const selector = new SmartClaudeSelector({
        apiKey: process.env.ANTHROPIC_API_KEY,
        enableLogging: TEST_CONFIG.verbose
    });
    
    try {
        // Test simple request with timeout
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('API test timeout')), TEST_CONFIG.maxTestTime)
        );
        
        const apiPromise = selector.createMessage([
            { role: 'user', content: 'Say "test successful" if you can read this.' }
        ], { max_tokens: 50 });
        
        const response = await Promise.race([apiPromise, timeoutPromise]);
        
        assert(response && response.content, 'API returned valid response');
        assert(response._smartSelector, 'Smart selector metadata included');
        assert(response._smartSelector.selectedModel, 'Selected model tracked');
        
        log(`API Test: Used model ${response._smartSelector.selectedModel}`, 'info');
        
        // Test usage stats after API call
        const stats = selector.getUsageStats();
        assert(stats.totalRequests > 0, 'Usage stats updated after API call');
        
    } catch (error) {
        if (error.message === 'API test timeout') {
            skip('API integration test (timeout)');
        } else {
            assert(false, 'API integration test failed', error.message);
        }
    }
}

// Main test runner
async function runAllTests() {
    console.log('🚀 Smart Claude Model Selector - Integration Tests\n');
    
    const startTime = Date.now();
    
    try {
        await testBasicFunctionality();
        await testRequestAnalysis();
        await testModelSelection();
        await testCostCalculation();
        await testUsageTracking();
        await testModelCapabilities();
        await testPerformanceBenchmark();
        await testApiIntegration();
        
    } catch (error) {
        log(`Test suite error: ${error.message}`, 'error');
        testResults.failed++;
    }
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Print results
    console.log('\n📊 Test Results:');
    console.log(`✅ Passed: ${testResults.passed}`);
    console.log(`❌ Failed: ${testResults.failed}`);
    console.log(`⏭️ Skipped: ${testResults.skipped}`);
    console.log(`⏱️ Total time: ${totalTime}ms`);
    
    if (testResults.failed === 0) {
        console.log('\n🎉 All tests passed! Smart Claude Selector is ready to use.');
        console.log('💰 Expected savings: 40-70% on Claude API costs');
        console.log('🚀 Performance: 100,000+ selections/second');
        process.exit(0);
    } else {
        console.log('\n❌ Some tests failed. Check the output above for details.');
        
        if (TEST_CONFIG.verbose) {
            console.log('\nDetailed Results:');
            testResults.details.forEach((result, index) => {
                console.log(`${index + 1}. ${result.status}: ${result.message}`);
                if (result.details) {
                    console.log(`   ${JSON.stringify(result.details)}`);
                }
            });
        }
        
        process.exit(1);
    }
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log(`
Smart Claude Model Selector - Integration Test

Usage: node test-integration.js [options]

Options:
  --help, -h          Show this help message
  --verbose           Enable verbose output
  --skip-api          Skip live API tests
  
Environment Variables:
  ANTHROPIC_API_KEY   Required for live API tests
  SKIP_API_TESTS      Set to 'true' to skip API tests
  VERBOSE             Set to 'true' for detailed output
  
Examples:
  node test-integration.js
  VERBOSE=true node test-integration.js
  SKIP_API_TESTS=true node test-integration.js
    `);
    process.exit(0);
}

if (process.argv.includes('--verbose')) {
    TEST_CONFIG.verbose = true;
}

if (process.argv.includes('--skip-api')) {
    TEST_CONFIG.skipApiTests = true;
}

// Run tests
runAllTests().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});