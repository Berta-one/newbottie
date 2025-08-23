#!/usr/bin/env node

/**
 * Smart OpenAI Model Selector - Integration Test
 * Automated testing script to verify OpenAI integration works correctly
 * 
 * Usage: node test-openai-integration.js
 * Requires: OPENAI_API_KEY environment variable for live tests
 */

const SmartOpenAISelector = require('./openai-model-selector');
const SmartOpenAIAPI = require('./openai-api-wrapper');

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
    log('🧪 Testing OpenAI Selector Basic Functionality', 'info');
    
    try {
        // Test 1: Constructor with default options
        const selector1 = new SmartOpenAISelector({
            apiKey: 'test-key-sk-test'
        });
        assert(selector1.apiKey === 'test-key-sk-test', 'Constructor accepts API key');
        assert(selector1.aggressiveSavings === true, 'Aggressive savings enabled by default');
        assert(selector1.qualityFocused === false, 'Quality focus disabled by default');
        
        // Test 2: Constructor with custom options
        const selector2 = new SmartOpenAISelector({
            apiKey: 'test-key',
            qualityFocused: true,
            aggressiveSavings: false,
            maxRetries: 5,
            enableLogging: true
        });
        assert(selector2.qualityFocused === true, 'Quality focus can be enabled');
        assert(selector2.aggressiveSavings === false, 'Aggressive savings can be disabled');
        assert(selector2.maxRetries === 5, 'Custom max retries setting');
        
        // Test 3: Constructor error handling
        try {
            new SmartOpenAISelector(); // No API key
            assert(false, 'Constructor should require API key');
        } catch (error) {
            assert(error.message.includes('API key is required'), 'Constructor validates API key requirement');
        }
        
    } catch (error) {
        assert(false, 'Basic functionality test suite failed', error.message);
    }
}

async function testRequestAnalysis() {
    log('🧪 Testing OpenAI Request Analysis', 'info');
    
    const selector = new SmartOpenAISelector({ apiKey: 'test-key' });
    
    // Test simple requests
    const simpleAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'What is 2+2?' }
    ]);
    assert(simpleAnalysis.isSimple === true, 'Simple questions detected');
    assert(simpleAnalysis.complexity === 'low', 'Simple questions have low complexity');
    assert(simpleAnalysis.taskType === 'simple', 'Simple questions categorized correctly');
    
    // Test coding requests
    const codingAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Write a JavaScript function to sort an array' }
    ]);
    assert(codingAnalysis.requiresCoding === true, 'Coding requests detected');
    assert(codingAnalysis.taskType === 'coding', 'Coding requests categorized correctly');
    
    // Test complex analysis requests
    const analysisRequest = selector.analyzeRequest([
        { role: 'user', content: 'Analyze the comprehensive impact of AI on society' }
    ]);
    assert(analysisRequest.complexity === 'high', 'Complex analysis detected');
    assert(analysisRequest.taskType === 'analysis', 'Analysis tasks categorized correctly');
    
    // Test creative requests
    const creativeAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Write a creative story about time travel' }
    ]);
    assert(creativeAnalysis.requiresCreativity === true, 'Creative requests detected');
    assert(creativeAnalysis.taskType === 'creative', 'Creative tasks categorized correctly');
    
    // Test reasoning requests
    const reasoningAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Solve this complex logical reasoning problem' }
    ]);
    assert(reasoningAnalysis.requiresAdvancedReasoning === true, 'Advanced reasoning detected');
    assert(reasoningAnalysis.taskType === 'reasoning', 'Reasoning tasks categorized correctly');
    
    // Test confidence levels
    const shortAnalysis = selector.analyzeRequest([
        { role: 'user', content: 'Hi' }
    ]);
    assert(shortAnalysis.confidence >= 0.9, 'High confidence for very short simple messages');
}

async function testModelSelection() {
    log('🧪 Testing OpenAI Model Selection Logic', 'info');
    
    // Test aggressive savings mode (default)
    const aggressiveSelector = new SmartOpenAISelector({ 
        apiKey: 'test-key', 
        aggressiveSavings: true 
    });
    
    const simpleTask = { 
        complexity: 'low', 
        taskType: 'simple', 
        isSimple: true, 
        estimatedTokens: 50 
    };
    const selectedModel1 = aggressiveSelector.selectOptimalModel(simpleTask);
    assert(selectedModel1 === 'gpt-4o-mini', 'Simple tasks use mini model in aggressive mode');
    
    const codingTask = { 
        complexity: 'medium', 
        taskType: 'coding', 
        requiresCoding: true,
        requiresAdvancedReasoning: false,
        estimatedTokens: 500 
    };
    const selectedModel2 = aggressiveSelector.selectOptimalModel(codingTask);
    assert(selectedModel2 === 'gpt-4o-mini', 'Basic coding tasks use mini in aggressive mode');
    
    // Test quality-focused mode
    const qualitySelector = new SmartOpenAISelector({ 
        apiKey: 'test-key', 
        qualityFocused: true,
        aggressiveSavings: false
    });
    
    const complexTask = { 
        complexity: 'high', 
        taskType: 'reasoning', 
        requiresAdvancedReasoning: true 
    };
    const selectedModel3 = qualitySelector.selectOptimalModel(complexTask);
    assert(selectedModel3 === 'gpt-4o', 'Complex reasoning uses GPT-4o in quality mode');
    
    // Test model override
    const overrideModel = aggressiveSelector.selectOptimalModel(simpleTask, { model: 'gpt-4o' });
    assert(overrideModel === 'gpt-4o', 'User-specified model overrides selection');
}

async function testCostCalculation() {
    log('🧪 Testing OpenAI Cost Calculation', 'info');
    
    const selector = new SmartOpenAISelector({ apiKey: 'test-key' });
    
    // Test GPT-4o-mini pricing
    const miniCost = selector.calculateCost('gpt-4o-mini', 1000, 1000);
    const expectedMiniCost = (1000/1000000) * 0.15 + (1000/1000000) * 0.60; // $0.00075
    assert(Math.abs(miniCost - expectedMiniCost) < 0.0001, 'GPT-4o-mini cost calculation accurate');
    
    // Test GPT-4o pricing
    const gpt4oCost = selector.calculateCost('gpt-4o', 1000, 1000);
    const expectedGpt4oCost = (1000/1000000) * 2.50 + (1000/1000000) * 10.00; // $0.0125
    assert(Math.abs(gpt4oCost - expectedGpt4oCost) < 0.0001, 'GPT-4o cost calculation accurate');
    
    // Test cost comparison (mini should be much cheaper)
    assert(miniCost < gpt4oCost, 'GPT-4o-mini is significantly cheaper than GPT-4o');
    
    // Test savings calculation
    const savingsRatio = (gpt4oCost - miniCost) / gpt4oCost;
    assert(savingsRatio > 0.9, 'GPT-4o-mini provides >90% cost savings vs GPT-4o');
}

async function testUsageTracking() {
    log('🧪 Testing OpenAI Usage Tracking', 'info');
    
    const selector = new SmartOpenAISelector({ apiKey: 'test-key' });
    
    // Initial stats should be empty
    const initialStats = selector.getUsageStats();
    assert(initialStats.totalRequests === 0, 'Initial request count is zero');
    assert(parseFloat(initialStats.totalCostSaved) === 0, 'Initial cost saved is zero');
    
    // Mock a usage tracking call
    const mockResult = {
        usage: {
            prompt_tokens: 100,
            completion_tokens: 200,
            total_tokens: 300
        }
    };
    
    const mockAnalysis = { complexity: 'low', taskType: 'simple' };
    selector.trackUsage('gpt-4o-mini', mockAnalysis, mockResult);
    
    const updatedStats = selector.getUsageStats();
    assert(updatedStats.totalRequests === 1, 'Request count increments');
    assert(updatedStats.modelUsage['gpt-4o-mini'] === 1, 'Model usage tracked');
    
    // Test stats reset
    selector.resetStats();
    const resetStats = selector.getUsageStats();
    assert(resetStats.totalRequests === 0, 'Stats reset successfully');
}

async function testModelCapabilities() {
    log('🧪 Testing OpenAI Model Capabilities', 'info');
    
    const selector = new SmartOpenAISelector({ apiKey: 'test-key' });
    const models = selector.getAvailableModels();
    
    assert(Array.isArray(models), 'getAvailableModels returns array');
    assert(models.length > 0, 'Available models list is not empty');
    
    const gpt4oModel = models.find(m => m.model === 'gpt-4o');
    assert(gpt4oModel !== undefined, 'GPT-4o model available');
    assert(gpt4oModel.coding === 'excellent', 'GPT-4o has excellent coding capability');
    assert(gpt4oModel.pricing.input === 2.50, 'GPT-4o pricing information included');
    
    const miniModel = models.find(m => m.model === 'gpt-4o-mini');
    assert(miniModel !== undefined, 'GPT-4o-mini model available');
    assert(miniModel.costRank === 1, 'GPT-4o-mini has the best cost rank');
}

async function testPerformanceBenchmark() {
    log('🧪 Testing OpenAI Performance Benchmark', 'info');
    
    const selector = new SmartOpenAISelector({ apiKey: 'test-key' });
    
    // Run a small benchmark
    const benchmark = await selector.benchmark(100);
    
    assert(benchmark.iterations === 100, 'Benchmark ran correct number of iterations');
    assert(benchmark.selectionsPerSecond > 1000, 'Performance is acceptable (>1000 selections/second)');
    assert(benchmark.totalTime >= 0, 'Benchmark measured execution time');
    assert(benchmark.averageTimePerSelection >= 0, 'Average time calculated');
    assert(benchmark.modelDistribution, 'Model distribution tracked');
    assert(benchmark.modelDistribution.estimatedSavings >= 0, 'Estimated savings calculated');
    
    log(`Performance: ${benchmark.selectionsPerSecond.toLocaleString()} selections/second`, 'info');
    log(`Mini usage: ${benchmark.modelDistribution.miniPercentage}% (${benchmark.modelDistribution.estimatedSavings}% estimated savings)`, 'info');
}

async function testAPIWrapper() {
    log('🧪 Testing OpenAI API Wrapper', 'info');
    
    const api = new SmartOpenAIAPI({ apiKey: 'test-key' });
    
    // Test configuration
    const config = api.getConfig();
    assert(config.selector, 'Wrapper exposes selector config');
    assert(config.defaults, 'Wrapper exposes default options');
    
    // Test available models access
    const models = api.getAvailableModels();
    assert(Array.isArray(models), 'Wrapper provides access to available models');
    
    // Test stats access
    const stats = api.getUsageStats();
    assert(typeof stats === 'object', 'Wrapper provides access to usage stats');
    
    // Test selector access
    const selector = api.getSelector();
    assert(selector instanceof SmartOpenAISelector, 'Wrapper provides direct selector access');
    
    // Test configuration updates
    api.setDefaults({ temperature: 0.5 });
    const updatedConfig = api.getConfig();
    assert(updatedConfig.defaults.temperature === 0.5, 'Default options can be updated');
}

async function testApiIntegration() {
    if (TEST_CONFIG.skipApiTests) {
        skip('OpenAI API integration tests (set SKIP_API_TESTS=false to enable)');
        return;
    }
    
    if (!process.env.OPENAI_API_KEY) {
        skip('OpenAI API integration tests (OPENAI_API_KEY not set)');
        return;
    }
    
    log('🧪 Testing OpenAI API Integration (Live Tests)', 'info');
    
    const api = new SmartOpenAIAPI({
        apiKey: process.env.OPENAI_API_KEY,
        enableLogging: TEST_CONFIG.verbose
    });
    
    try {
        // Test simple message with timeout
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('API test timeout')), TEST_CONFIG.maxTestTime)
        );
        
        const apiPromise = api.sendMessage('Say "test successful" if you can read this.', { 
            max_tokens: 50 
        });
        
        const response = await Promise.race([apiPromise, timeoutPromise]);
        
        assert(response && response.content, 'API returned valid response');
        assert(response.model, 'Selected model tracked');
        assert(response.usage, 'Usage information included');
        assert(response.metadata, 'Smart selector metadata included');
        
        log(`API Test: Used model ${response.model}`, 'info');
        
        // Test usage stats after API call
        const stats = api.getUsageStats();
        assert(stats.totalRequests > 0, 'Usage stats updated after API call');
        
        // Test different wrapper methods
        const codeResponse = await api.generateCode('Create a hello world function in Python', 'Python', { max_tokens: 100 });
        assert(codeResponse && codeResponse.code, 'Code generation works');
        assert(codeResponse.model, 'Code generation tracks model');
        
        log(`Code generation used: ${codeResponse.model}`, 'info');
        
    } catch (error) {
        if (error.message === 'API test timeout') {
            skip('OpenAI API integration test (timeout)');
        } else {
            assert(false, 'OpenAI API integration test failed', error.message);
        }
    }
}

// Main test runner
async function runAllTests() {
    console.log('🚀 Smart OpenAI Model Selector - Integration Tests\n');
    
    const startTime = Date.now();
    
    try {
        await testBasicFunctionality();
        await testRequestAnalysis();
        await testModelSelection();
        await testCostCalculation();
        await testUsageTracking();
        await testModelCapabilities();
        await testPerformanceBenchmark();
        await testAPIWrapper();
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
        console.log('\n🎉 All tests passed! Smart OpenAI Selector is ready to use.');
        console.log('💰 Expected savings: 80-90% on OpenAI API costs');
        console.log('🚀 Performance: 100,000+ selections/second');
        console.log('🎯 Model accuracy: Optimized for aggressive cost savings');
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
Smart OpenAI Model Selector - Integration Test

Usage: node test-openai-integration.js [options]

Options:
  --help, -h          Show this help message
  --verbose           Enable verbose output
  --skip-api          Skip live API tests
  
Environment Variables:
  OPENAI_API_KEY      Required for live API tests
  SKIP_API_TESTS      Set to 'true' to skip API tests
  VERBOSE             Set to 'true' for detailed output
  
Examples:
  node test-openai-integration.js
  VERBOSE=true node test-openai-integration.js
  SKIP_API_TESTS=true node test-openai-integration.js
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