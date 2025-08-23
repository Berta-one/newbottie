/**
 * Smart OpenAI API Wrapper
 * Easy-to-use wrapper with intelligent model selection
 * Drop-in replacement for direct OpenAI API calls
 * 
 * @version 1.0.0
 * @author Smart Model Selection Team
 */

const SmartOpenAISelector = require('./openai-model-selector');

class SmartOpenAIAPI {
    constructor(options = {}) {
        this.selector = new SmartOpenAISelector(options);
        this.defaultOptions = {
            max_tokens: options.defaultMaxTokens || 1000,
            temperature: options.defaultTemperature || 0.7,
            top_p: options.defaultTopP || 1,
            frequency_penalty: options.defaultFrequencyPenalty || 0,
            presence_penalty: options.defaultPresencePenalty || 0
        };
    }
    
    /**
     * Send a simple message and get a response
     * Most common use case - simplified interface
     */
    async sendMessage(content, options = {}) {
        const messages = [
            { role: 'user', content: content }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            ...options
        });
        
        return {
            content: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Send messages with conversation history
     * For chat applications with context
     */
    async sendConversation(messages, options = {}) {
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            ...options
        });
        
        return {
            content: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector,
            fullResponse: response
        };
    }
    
    /**
     * Ask a question with system prompt
     * For applications that need specific behavior
     */
    async askWithSystem(systemPrompt, userMessage, options = {}) {
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userMessage }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            ...options
        });
        
        return {
            content: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Generate completion for coding tasks
     * Optimized for code generation
     */
    async generateCode(prompt, language = '', options = {}) {
        const systemPrompt = language 
            ? `You are an expert ${language} programmer. Generate clean, efficient, well-commented code.`
            : 'You are an expert programmer. Generate clean, efficient, well-commented code.';
            
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: prompt }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            temperature: 0.3, // Lower temperature for code
            ...options
        });
        
        return {
            code: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Analyze text or data
     * For analysis and reasoning tasks
     */
    async analyze(content, analysisType = 'general', options = {}) {
        const systemPrompts = {
            general: 'You are an expert analyst. Provide thorough, insightful analysis.',
            data: 'You are a data analyst. Analyze the provided data and extract meaningful insights.',
            text: 'You are a text analyst. Analyze the writing style, tone, and content.',
            business: 'You are a business analyst. Provide strategic analysis and recommendations.',
            technical: 'You are a technical analyst. Provide detailed technical analysis.'
        };
        
        const systemPrompt = systemPrompts[analysisType] || systemPrompts.general;
        
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: content }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            temperature: 0.4, // Slightly lower for analysis
            ...options
        });
        
        return {
            analysis: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Generate creative content
     * For stories, poems, creative writing
     */
    async createContent(prompt, contentType = 'story', options = {}) {
        const systemPrompts = {
            story: 'You are a creative writer. Write engaging, well-structured stories.',
            poem: 'You are a poet. Create beautiful, meaningful poetry.',
            article: 'You are a content writer. Write informative, engaging articles.',
            marketing: 'You are a marketing copywriter. Create compelling, persuasive content.',
            social: 'You are a social media content creator. Create engaging, shareable content.'
        };
        
        const systemPrompt = systemPrompts[contentType] || systemPrompts.story;
        
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: prompt }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            temperature: 0.8, // Higher temperature for creativity
            ...options
        });
        
        return {
            content: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Summarize text
     * For document summarization
     */
    async summarize(text, style = 'concise', options = {}) {
        const systemPrompts = {
            concise: 'Summarize the following text concisely, capturing the key points.',
            detailed: 'Provide a detailed summary that covers all important aspects.',
            bullet: 'Summarize the text using bullet points for easy reading.',
            executive: 'Create an executive summary suitable for business stakeholders.'
        };
        
        const systemPrompt = systemPrompts[style] || systemPrompts.concise;
        
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: text }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            temperature: 0.3, // Lower temperature for summaries
            ...options
        });
        
        return {
            summary: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Translate text
     * For language translation
     */
    async translate(text, targetLanguage, sourceLanguage = 'auto', options = {}) {
        const systemPrompt = sourceLanguage === 'auto' 
            ? `Translate the following text to ${targetLanguage}. Maintain the original meaning and tone.`
            : `Translate the following text from ${sourceLanguage} to ${targetLanguage}. Maintain the original meaning and tone.`;
            
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: text }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            temperature: 0.2, // Very low temperature for translations
            ...options
        });
        
        return {
            translation: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Extract information from text
     * For information extraction tasks
     */
    async extract(text, extractionType = 'entities', options = {}) {
        const systemPrompts = {
            entities: 'Extract named entities (people, places, organizations, dates) from the text.',
            keywords: 'Extract the most important keywords and phrases from the text.',
            facts: 'Extract key facts and information from the text.',
            contacts: 'Extract contact information (names, emails, phone numbers, addresses) from the text.',
            dates: 'Extract all dates and time references from the text.'
        };
        
        const systemPrompt = systemPrompts[extractionType] || systemPrompts.entities;
        
        const messages = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: text }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            temperature: 0.1, // Very low temperature for extraction
            ...options
        });
        
        return {
            extracted: response.choices[0].message.content,
            model: response._smartSelector.selectedModel,
            usage: response.usage,
            metadata: response._smartSelector
        };
    }
    
    /**
     * Get usage statistics and cost savings
     */
    getUsageStats() {
        return this.selector.getUsageStats();
    }
    
    /**
     * Reset usage statistics
     */
    resetStats() {
        this.selector.resetStats();
    }
    
    /**
     * Get available models
     */
    getAvailableModels() {
        return this.selector.getAvailableModels();
    }
    
    /**
     * Run performance benchmark
     */
    async benchmark(iterations = 1000) {
        return await this.selector.benchmark(iterations);
    }
    
    /**
     * Direct access to the underlying selector for advanced usage
     */
    getSelector() {
        return this.selector;
    }
    
    /**
     * Batch process multiple requests efficiently
     */
    async batchProcess(requests, options = {}) {
        const results = await Promise.all(
            requests.map(async (req, index) => {
                try {
                    let result;
                    
                    switch (req.type || 'message') {
                        case 'message':
                            result = await this.sendMessage(req.content, req.options);
                            break;
                        case 'conversation':
                            result = await this.sendConversation(req.messages, req.options);
                            break;
                        case 'code':
                            result = await this.generateCode(req.prompt, req.language, req.options);
                            break;
                        case 'analyze':
                            result = await this.analyze(req.content, req.analysisType, req.options);
                            break;
                        case 'creative':
                            result = await this.createContent(req.prompt, req.contentType, req.options);
                            break;
                        case 'summarize':
                            result = await this.summarize(req.text, req.style, req.options);
                            break;
                        case 'translate':
                            result = await this.translate(req.text, req.targetLanguage, req.sourceLanguage, req.options);
                            break;
                        case 'extract':
                            result = await this.extract(req.text, req.extractionType, req.options);
                            break;
                        default:
                            result = await this.sendMessage(req.content, req.options);
                    }
                    
                    return {
                        index,
                        success: true,
                        result,
                        request: req
                    };
                    
                } catch (error) {
                    return {
                        index,
                        success: false,
                        error: error.message,
                        request: req
                    };
                }
            })
        );
        
        return results;
    }
    
    /**
     * Stream responses for real-time applications
     */
    async streamMessage(content, onChunk, options = {}) {
        const messages = [
            { role: 'user', content: content }
        ];
        
        const response = await this.selector.createChatCompletion(messages, {
            ...this.defaultOptions,
            stream: true,
            ...options
        });
        
        // Note: Streaming implementation would depend on the specific streaming format
        // This is a placeholder for the streaming interface
        return response;
    }
    
    /**
     * Configure default settings
     */
    setDefaults(options = {}) {
        this.defaultOptions = {
            ...this.defaultOptions,
            ...options
        };
    }
    
    /**
     * Get current configuration
     */
    getConfig() {
        return {
            selector: {
                aggressiveSavings: this.selector.aggressiveSavings,
                qualityFocused: this.selector.qualityFocused,
                enableLogging: this.selector.enableLogging,
                maxRetries: this.selector.maxRetries
            },
            defaults: this.defaultOptions
        };
    }
}

module.exports = SmartOpenAIAPI;